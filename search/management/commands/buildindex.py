import argparse
import pickle
import gc

import numpy as np
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

from django.db import connection

from api import models as v1
from api_v2 import models as v2
from search import models as search

class Command(BaseCommand):
    """Build search indexes for text, fuzzy, and semantic search."""

    help = 'Build the search indexes (FTS, Whoosh, and vector).'

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
        """Create word embeddings using spaCy for semantic search."""
        print("Building semantic vector index with spaCy...")
        
        try:
            import spacy
        except ImportError:
            print("ERROR: spacy not installed. Run: pipenv install spacy")
            return
        
        # Load spaCy model with word vectors
        print("Loading spaCy model (en_core_web_md)...")
        try:
            nlp = spacy.load("en_core_web_md")
        except OSError:
            print("Downloading spaCy model en_core_web_md...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"], check=True)
            nlp = spacy.load("en_core_web_md")
        
        # Disable components we don't need for speed
        nlp.disable_pipes("ner", "parser")
        
        qs = search.SearchResult.objects.all().order_by("id")
        total_count = qs.count()
        
        if not total_count:
            print("No documents found for semantic indexing")
            return
        
        print(f"Processing {total_count} documents...")
        
        all_embeddings = []
        all_names = []
        all_metadata = []
        
        batch_size = 500
        for offset in range(0, total_count, batch_size):
            batch_qs = qs[offset:offset + batch_size]
            batch_texts = []
            
            for o in batch_qs:
                # Use name + first part of description
                text = o.object_name
                if o.text:
                    text += " " + o.text[:200]
                
                batch_texts.append(text)
                all_names.append(o.object_name)
                all_metadata.append({
                    'object_type': o.object_model,
                    'document_pk': o.document_pk,
                    'schema_version': o.schema_version,
                    'description': (o.text or '')[:500]
                })
            
            # Process batch with spaCy's pipe for efficiency
            for doc in nlp.pipe(batch_texts, batch_size=50):
                # Average word vectors, ignoring words without vectors
                vectors = [token.vector for token in doc if token.has_vector]
                if vectors:
                    avg_vector = np.mean(vectors, axis=0)
                    # Normalize for cosine similarity
                    norm = np.linalg.norm(avg_vector)
                    if norm > 0:
                        avg_vector = avg_vector / norm
                    all_embeddings.append(avg_vector)
                else:
                    # Zero vector for documents with no recognized words
                    all_embeddings.append(np.zeros(nlp.vocab.vectors_length))
            
            print(f"Processed {min(offset + batch_size, total_count)}/{total_count} documents")
            gc.collect()
        
        embeddings = np.array(all_embeddings)
        print(f"Embedding shape: {embeddings.shape}")
        print("Saving vector index to disk...")
        
        index_data = {
            "names": all_names, 
            "metadata": all_metadata,
            "embeddings": embeddings,
            "vector_size": nlp.vocab.vectors_length
        }
        
        with Path("server/vector_index.pkl").open("wb") as fh:
            pickle.dump(index_data, fh)
        
        print("Semantic vector index saved successfully")
        
        # Clean up
        del all_embeddings, all_names, all_metadata, embeddings, index_data, nlp
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

        # Build Whoosh index for Haystack text/fuzzy search
        print("=== Building Whoosh search index ===")
        self.build_whoosh_index()
        print("✅ Whoosh index built")

        # Unload content table (saves storage space.)
        print("=== Cleaning up ===")
        self.unload_all_content()
        print("✅ Cleanup complete")
        
        print("=== buildindex command completed successfully ===")
        print("Total SearchResult objects:", search.SearchResult.objects.all().count())
    
    def build_whoosh_index(self):
        """Build the Whoosh index for Haystack text search."""
        try:
            call_command('rebuild_index', '--noinput')
        except Exception as e:
            print(f"Warning: Could not build Whoosh index: {e}")
            print("Text search may fall back to SQLite FTS")
