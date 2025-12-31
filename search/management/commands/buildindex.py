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
    help = 'Build search indexes (FTS, Whoosh, and vector)'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument("--v1", action="store_true", help="Include v1 data")
        parser.add_argument("--v2", action="store_true", help="Include v2 data")

    def unload_all_content(self):
        count = search.SearchResult.objects.count()
        search.SearchResult.objects.all().delete()
        print(f"Cleared {count} objects")

    def load_v1_content(self, model):
        results = []
        indexable = ['MagicItem', 'Spell', 'Monster', 'CharClass', 'Archetype',
                     'Race', 'Subrace', 'Plane', 'Section', 'Feat', 'Condition',
                     'Background', 'Weapon', 'Armor']

        if model.__name__ in indexable:
            for o in model.objects.all():
                results.append(search.SearchResult(
                    document_pk=o.document.slug,
                    object_pk=o.slug,
                    object_name=o.name,
                    object_model=o.__class__.__name__,
                    schema_version="v1",
                    text=o.name + "\n" + o.desc
                ))
        return results

    def load_v2_content(self, model):
        results = []
        indexable = ['Item', 'Spell', 'Creature', 'CharacterClass', 'Species',
                     'Feat', 'Background', 'Environment', 'Rule']

        if model.__name__ in indexable:
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
        print(f"{schema}: {model.__name__} ({model.objects.count()} objects)")

        batch_size = 500
        if schema == 'v1':
            objects_to_create = self.load_v1_content(model)
        elif schema == 'v2':
            objects_to_create = self.load_v2_content(model)
        else:
            return

        for i in range(0, len(objects_to_create), batch_size):
            batch = objects_to_create[i:i + batch_size]
            search.SearchResult.objects.bulk_create(batch, batch_size=batch_size)
            gc.collect()

    def load_index(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS search_index;")
            cursor.execute(
                "CREATE VIRTUAL TABLE search_index "
                "USING FTS5(document_pk,object_pk,object_name,object_model,text,schema_version);")
            cursor.execute(
                "INSERT INTO search_index "
                "(document_pk,object_pk,object_name,object_model,text,schema_version) "
                "SELECT document_pk,object_pk,object_name,object_model,text,schema_version "
                "FROM search_searchresult")

    def build_vector_index(self):
        print("Building vector index...")

        try:
            import spacy
        except ImportError:
            print("ERROR: spacy not installed")
            return

        print("Loading spaCy model...")
        try:
            nlp = spacy.load("en_core_web_md")
        except OSError:
            print("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"], check=True)
            nlp = spacy.load("en_core_web_md")

        nlp.select_pipes(disable=["ner", "parser"])

        qs = search.SearchResult.objects.all().order_by("id")
        total_count = qs.count()

        if not total_count:
            print("No documents to index")
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

            for doc in nlp.pipe(batch_texts, batch_size=50):
                vectors = [token.vector for token in doc if token.has_vector]
                if vectors:
                    avg_vector = np.mean(vectors, axis=0)
                    norm = np.linalg.norm(avg_vector)
                    if norm > 0:
                        avg_vector = avg_vector / norm
                    all_embeddings.append(avg_vector)
                else:
                    all_embeddings.append(np.zeros(nlp.vocab.vectors_length))

            print(f"  {min(offset + batch_size, total_count)}/{total_count}")
            gc.collect()

        embeddings = np.array(all_embeddings)
        print(f"Embedding shape: {embeddings.shape}")

        index_data = {
            "names": all_names,
            "metadata": all_metadata,
            "embeddings": embeddings,
            "vector_size": nlp.vocab.vectors_length
        }

        with Path("server/vector_index.pkl").open("wb") as fh:
            pickle.dump(index_data, fh)

        del all_embeddings, all_names, all_metadata, embeddings, index_data, nlp
        gc.collect()

    def check_fts_enabled(self):
        with connection.cursor() as cursor:
            cursor.execute('pragma compile_options;')
            for pragma in cursor.fetchall():
                if pragma[0] == 'ENABLE_FTS5':
                    print("FTS5 enabled")

    def handle(self, *args, **options):
        print("=== buildindex ===")

        self.check_fts_enabled()
        self.unload_all_content()

        if options["v1"]:
            print("Loading v1 content...")
            self.load_content(v1.MagicItem, "v1")
            self.load_content(v1.Spell, "v1")
            self.load_content(v1.Monster, "v1")
            self.load_content(v1.CharClass, "v1")
            self.load_content(v1.Race, "v1")
            self.load_content(v1.Subrace, "v1")
            self.load_content(v1.Plane, "v1")
            self.load_content(v1.Section, "v1")
            self.load_content(v1.Feat, "v1")
            self.load_content(v1.Condition, "v1")
            self.load_content(v1.Background, "v1")
            self.load_content(v1.Weapon, "v1")
            self.load_content(v1.Armor, "v1")

        if options["v2"]:
            print("Loading v2 content...")
            self.load_content(v2.Item, "v2")
            self.load_content(v2.Spell, "v2")
            self.load_content(v2.Creature, "v2")
            self.load_content(v2.CharacterClass, "v2")
            self.load_content(v2.Species, "v2")
            self.load_content(v2.Feat, "v2")
            self.load_content(v2.Condition, "v2")
            self.load_content(v2.Background, "v2")
            self.load_content(v2.Environment, "v2")
            self.load_content(v2.Rule, "v2")

        print("Building FTS index...")
        self.load_index()

        self.build_vector_index()

        print("Building Whoosh index...")
        self.build_whoosh_index()

        self.unload_all_content()
        print("=== done ===")

    def build_whoosh_index(self):
        try:
            call_command('rebuild_index', '--noinput')
        except Exception as e:
            print(f"Whoosh index failed: {e}")
