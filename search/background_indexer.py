"""
Background search index refresh that runs after server startup.
Ensures indexes stay consistent with the database even when repopulated on deploy.
"""
import threading
import time
import logging
import gc
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_indexing_lock = threading.Lock()
_indexing_in_progress = False
_last_index_time = None


def is_indexing_in_progress():
    return _indexing_in_progress


def get_last_index_time():
    return _last_index_time


def schedule_background_reindex(delay_seconds=60, rebuild_vector=True):
    if delay_seconds <= 0:
        return

    def _delayed_reindex():
        global _indexing_in_progress, _last_index_time

        logger.info(f"Background re-index scheduled in {delay_seconds}s")
        time.sleep(delay_seconds)

        if not _indexing_lock.acquire(blocking=False):
            logger.warning("Background re-index skipped - already in progress")
            return

        try:
            _indexing_in_progress = True
            logger.info("Starting background search index refresh...")
            start_time = time.time()

            _run_reindex(rebuild_vector=rebuild_vector)

            elapsed = time.time() - start_time
            _last_index_time = time.time()
            logger.info(f"Background re-index completed in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"Background re-index failed: {e}", exc_info=True)
        finally:
            _indexing_in_progress = False
            _indexing_lock.release()

    thread = threading.Thread(target=_delayed_reindex, daemon=True, name="search-reindex")
    thread.start()


def _run_reindex(rebuild_vector=True):
    from django.core.management import call_command

    logger.info("Updating Whoosh index...")
    try:
        call_command('update_index', '--remove', verbosity=1)
    except Exception as e:
        logger.error(f"Whoosh update failed: {e}")
        try:
            call_command('rebuild_index', '--noinput', verbosity=1)
        except Exception as e2:
            logger.error(f"Whoosh rebuild failed: {e2}")

    if rebuild_vector:
        logger.info("Rebuilding vector index...")
        try:
            _rebuild_vector_index()
        except Exception as e:
            logger.error(f"Vector index rebuild failed: {e}")


def _rebuild_vector_index():
    from django.conf import settings
    from api import models as v1
    from api_v2 import models as v2

    try:
        import spacy
    except ImportError:
        logger.warning("spaCy not installed - skipping vector index")
        return

    try:
        nlp = spacy.load("en_core_web_md")
    except OSError:
        logger.warning("spaCy model not found - skipping vector index")
        return

    nlp.select_pipes(disable=["ner", "parser"])

    all_embeddings = []
    all_names = []
    all_metadata = []

    v1_models = [
        (v1.MagicItem, lambda o: o.name + " " + (o.desc or "")[:200]),
        (v1.Spell, lambda o: o.name + " " + (o.desc or "")[:200]),
        (v1.Monster, lambda o: o.name + " " + (o.desc or "")[:200]),
        (v1.CharClass, lambda o: o.name + " " + (o.desc or "")[:200]),
        (v1.Race, lambda o: o.name + " " + (o.desc or "")[:200]),
        (v1.Feat, lambda o: o.name + " " + (o.desc or "")[:200]),
        (v1.Condition, lambda o: o.name + " " + (o.desc or "")[:200]),
        (v1.Background, lambda o: o.name + " " + (o.desc or "")[:200]),
    ]

    v2_models = [
        (v2.Item, lambda o: o.name + " " + (o.as_text() or "")[:200]),
        (v2.Spell, lambda o: o.name + " " + (o.as_text() or "")[:200]),
        (v2.Creature, lambda o: o.name + " " + (o.as_text() or "")[:200]),
        (v2.CharacterClass, lambda o: o.name + " " + (o.as_text() or "")[:200]),
        (v2.Species, lambda o: o.name + " " + (o.as_text() or "")[:200]),
        (v2.Feat, lambda o: o.name + " " + (o.as_text() or "")[:200]),
        (v2.Background, lambda o: o.name + " " + (o.as_text() or "")[:200]),
    ]

    def process_model(model, text_func, schema_version):
        texts = []
        for obj in model.objects.all():
            try:
                text = text_func(obj)
                texts.append(text)
                all_names.append(obj.name)

                doc_key = obj.document.slug if schema_version == 'v1' else obj.document.key
                all_metadata.append({
                    'object_type': model.__name__,
                    'document_pk': doc_key,
                    'schema_version': schema_version,
                    'description': text[:500] if text else ''
                })
            except Exception as e:
                logger.debug(f"Skipping {model.__name__} object: {e}")

        for doc in nlp.pipe(texts, batch_size=50):
            vectors = [token.vector for token in doc if token.has_vector]
            if vectors:
                avg_vector = np.mean(vectors, axis=0)
                norm = np.linalg.norm(avg_vector)
                if norm > 0:
                    avg_vector = avg_vector / norm
                all_embeddings.append(avg_vector)
            else:
                all_embeddings.append(np.zeros(nlp.vocab.vectors_length))

    for model, text_func in v1_models:
        try:
            process_model(model, text_func, 'v1')
        except Exception as e:
            logger.warning(f"Error processing {model.__name__}: {e}")

    for model, text_func in v2_models:
        try:
            process_model(model, text_func, 'v2')
        except Exception as e:
            logger.warning(f"Error processing {model.__name__}: {e}")

    if not all_embeddings:
        logger.warning("No documents found for vector indexing")
        return

    embeddings = np.array(all_embeddings)
    logger.info(f"Vector index: {len(all_names)} documents, shape {embeddings.shape}")

    index_data = {
        "names": all_names,
        "metadata": all_metadata,
        "embeddings": embeddings,
        "vector_size": nlp.vocab.vectors_length
    }

    index_path = Path(settings.BASE_DIR) / "server" / "vector_index.pkl"
    with index_path.open("wb") as fh:
        pickle.dump(index_data, fh)

    # Invalidate cached index
    from search import services
    services._vector_index = None
    services._vector_index_loaded = False
    services._fuzzy_search_cache.clear()

    del all_embeddings, all_names, all_metadata, embeddings, index_data, nlp
    gc.collect()


def trigger_reindex_now(rebuild_vector=True):
    """Trigger immediate re-index. Returns True if started, False if already running."""
    global _indexing_in_progress, _last_index_time

    if not _indexing_lock.acquire(blocking=False):
        return False

    def _run():
        global _indexing_in_progress, _last_index_time
        try:
            _indexing_in_progress = True
            start_time = time.time()
            _run_reindex(rebuild_vector=rebuild_vector)
            _last_index_time = time.time()
            logger.info(f"Manual re-index completed in {time.time() - start_time:.1f}s")
        except Exception as e:
            logger.error(f"Manual re-index failed: {e}", exc_info=True)
        finally:
            _indexing_in_progress = False
            _indexing_lock.release()

    thread = threading.Thread(target=_run, daemon=True, name="search-reindex-manual")
    thread.start()
    return True
