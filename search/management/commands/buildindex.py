import argparse
import pickle
import gc

from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

from django.db import connection, transaction

from api import models as v1
from api_v2 import models as v2
from search import models as search
from sklearn.feature_extraction.text import TfidfVectorizer

class Command(BaseCommand):
    """Implementation for the `manage.py `index_v1` subcommand."""

    help = 'Build the v1 search index.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        """Define arguments for the `manage.py quicksetup` subcommand."""

        # Named (optional) arguments.
        parser.add_argument(
            "--v1",
            action="store_true",
            help="Explicitly adding v1 data to index.",
        )
        # Named (optional) arguments.
        parser.add_argument(
            "--v2",
            action="store_true",
            help="Explicitly adding v2 data to index.",
        )

    def unload_all_content(self):
        object_count = search.SearchResult.objects.all().count()
        search.SearchResult.objects.all().delete()
        print("UNLOADED_OBJECT_COUNT:{}".format(object_count))

    def load_v1_content(self, model):
        results = []
        standard_v1_models = ['MagicItem','Spell','Monster','CharClass','Archetype',
                'Race','Subrace','Plane','Section','Feat','Condition','Background','Weapon','Armor']

        if model.__name__ in standard_v1_models:
            for o in model.objects.all():
                results.append(search.SearchResult(
                    document_pk=o.document.slug,
                    object_pk=o.slug,
                    object_name=o.name,
                    object_model=o.__class__.__name__,
                    schema_version="v1",
                    text=o.name+"\n"+o.desc

                ))
        return results

    def load_v2_content(self, model):
        results = []
        standard_v2_models = ['Item','Spell','Creature','CharacterClass','Species','Feat','Background','Environment', 'Rule']

        if model.__name__ in standard_v2_models:
            for o in model.objects.all():
                results.append(search.SearchResult(
                    document_pk=o.document.key,
                    object_pk=o.pk,
                    object_name=o.name,
                    object_model=o.__class__.__name__,
                    schema_version='v2',
                    text=o.as_text()
                ))
        return results

    def load_content(self, model, schema):
        print("SCHEMA:{} OBJECT_COUNT:{} MODEL:{} TABLE_NAME:{}".format(
                    schema,
                    model.objects.all().count(),
                    model.__name__,
                    model._meta.db_table))

        # Use batching to reduce memory usage
        batch_size = 500  # Process in smaller batches
        
        if schema == 'v1':
            objects_to_create = self.load_v1_content(model)
        elif schema == 'v2':
            objects_to_create = self.load_v2_content(model)
        else:
            return
        
        # Create in batches to avoid memory issues
        for i in range(0, len(objects_to_create), batch_size):
            batch = objects_to_create[i:i + batch_size]
            search.SearchResult.objects.bulk_create(batch, batch_size=batch_size)
            print(f"Created batch {i//batch_size + 1}: {len(batch)} objects")
            
            # Force garbage collection after each batch
            gc.collect()

    def load_index(self):
        with connection.cursor() as cursor:

            cursor.execute("DROP TABLE IF EXISTS search_index;")

            cursor.execute(
                "CREATE VIRTUAL TABLE search_index " +
                "USING FTS5(document_pk,object_pk,object_name,object_model,text,schema_version);")

            cursor.execute(
                "INSERT INTO search_index " +
                "(document_pk,object_pk,object_name,object_model,text,schema_version) " +
                "SELECT document_pk,object_pk,object_name,object_model,text,schema_version " +
                "FROM search_searchresult")

    def build_vector_index(self):
        """Create a TF-IDF matrix for vector search and store it to disk with memory optimization."""
        print("Building TF-IDF vector index...")
        
        qs = search.SearchResult.objects.all().order_by("id")
        total_count = qs.count()
        
        if not total_count:
            print("No documents found for TF-IDF indexing")
            return
        
        print(f"Processing {total_count} documents for TF-IDF...")
        
        # Process in smaller batches to reduce memory usage
        batch_size = 1000
        all_docs = []
        all_ids = []
        all_names = []
        
        for offset in range(0, total_count, batch_size):
            batch_qs = qs[offset:offset + batch_size]
            batch_docs = []
            batch_ids = []
            batch_names = []
            
            for o in batch_qs:
                text = f"{o.object_name} {o.text or ''}"
                # Limit text length to prevent memory issues
                if len(text) > 1000:
                    text = text[:1000]
                
                batch_docs.append(text)
                batch_ids.append(o.id)
                batch_names.append(o.object_name)
            
            all_docs.extend(batch_docs)
            all_ids.extend(batch_ids)
            all_names.extend(batch_names)
            
            print(f"Processed batch {offset//batch_size + 1}/{(total_count-1)//batch_size + 1}")
            
            # Clean up batch variables
            del batch_docs, batch_ids, batch_names
            gc.collect()
        
        # Create TF-IDF vectorizer with memory-friendly settings
        print("Creating TF-IDF vectorizer...")
        vectorizer = TfidfVectorizer(
            max_features=2000,  # Reduced from 5000 to save memory
            stop_words='english',
            ngram_range=(1, 1),  # Only unigrams to save memory
            min_df=2,
            max_df=0.8,
            lowercase=True,
            strip_accents='unicode'
        )
        
        print("Fitting TF-IDF vectorizer...")
        # Keep sparse matrix to save memory
        matrix = vectorizer.fit_transform(all_docs)
        
        print(f"TF-IDF matrix shape: {matrix.shape}")
        print("Saving vector index to disk...")
        
        index_data = {
            "ids": all_ids, 
            "names": all_names, 
            "matrix": matrix,  # Keep as sparse matrix
            "vectorizer": vectorizer
        }
        
        with Path("server/vector_index.pkl").open("wb") as fh:
            pickle.dump(index_data, fh)
        
        print("Vector index saved successfully")
        
        # Clean up large variables
        del all_docs, all_ids, all_names, matrix, index_data
        gc.collect()

    def check_fts_enabled(self):
        #import sqlite3
        with connection.cursor() as cursor:
            cursor.execute('pragma compile_options;')
            available_pragmas = cursor.fetchall()
            
            for pragma in available_pragmas:
                if pragma[0]=='ENABLE_FTS5':
                    print("FOUND PRAGMA {}, FTS5 IS ENABLED".format(pragma))


    def handle(self, *args, **options):
        print("=== Starting buildindex command ===")
        
        # Ensure FTS is enabled and ready to go.
        print("Checking FTS support...")
        self.check_fts_enabled()
        print("✅ FTS check complete")

        # Clear out the content table.
        print("Clearing existing content...")
        self.unload_all_content()
        print("✅ Content cleared")

        if options["v1"]:
            print("=== Loading v1 content ===")
            # Load the v1 models into the content table.
            self.load_content(v1.MagicItem,"v1")
            self.load_content(v1.Spell,"v1")
            self.load_content(v1.Monster,"v1")
            self.load_content(v1.CharClass,"v1")
            self.load_content(v1.Race,"v1")
            self.load_content(v1.Subrace,"v1")
            self.load_content(v1.Plane,"v1")
            self.load_content(v1.Section,"v1")
            self.load_content(v1.Feat,"v1")
            self.load_content(v1.Condition,"v1")
            self.load_content(v1.Background,"v1")
            self.load_content(v1.Weapon,"v1")
            self.load_content(v1.Armor,"v1")
            print("✅ v1 content loaded")

        if options["v2"]:
            print("=== Loading v2 content ===")
            # Load the v2 models into the content table.
            self.load_content(v2.Item,"v2")
            self.load_content(v2.Spell,"v2")
            self.load_content(v2.Creature,"v2")
            self.load_content(v2.CharacterClass,"v2")
            self.load_content(v2.Species,"v2")
            self.load_content(v2.Feat,"v2")
            self.load_content(v2.Condition,"v2")
            self.load_content(v2.Background,"v2")
            self.load_content(v2.Environment,"v2")
            self.load_content(v2.Rule, "v2")
            print("✅ v2 content loaded")

        # Take the content table's current data and load it into the index.
        print("=== Building FTS search index ===")
        self.load_index()
        print("✅ FTS index built")

        # Also build the vector search index from the loaded content.
        print("=== Building vector search index ===")
        self.build_vector_index()
        print("✅ Vector index built")

        # Unload content table (saves storage space.)
        print("=== Cleaning up ===")
        self.unload_all_content()
        print("✅ Cleanup complete")
        
        print("=== buildindex command completed successfully ===")
        print("Total SearchResult objects:", search.SearchResult.objects.all().count())
