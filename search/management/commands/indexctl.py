"""
Index control command for managing search indexes.

Usage:
    manage.py indexctl check     - Check if indexes are stale
    manage.py indexctl build     - Build indexes from data
    manage.py indexctl pack      - Pack indexes for committing
    manage.py indexctl unpack    - Unpack indexes from committed archives
"""
import argparse
import gzip
import hashlib
import json
import shutil
import tarfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


def get_data_hash():
    """Compute a hash of all JSON data files."""
    data_dirs = [Path("data/v1"), Path("data/v2")]
    hasher = hashlib.md5()
    
    for data_dir in data_dirs:
        if not data_dir.exists():
            continue
        for json_file in sorted(data_dir.rglob("*.json")):
            hasher.update(json_file.name.encode())
            hasher.update(json_file.read_bytes())
    
    return hasher.hexdigest()


class Command(BaseCommand):
    help = "Manage search indexes"
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        subparsers = parser.add_subparsers(dest="action", help="Action to perform")
        
        subparsers.add_parser("check", help="Check if indexes are stale")
        subparsers.add_parser("build", help="Build indexes from data")
        subparsers.add_parser("pack", help="Pack indexes for committing")
        subparsers.add_parser("unpack", help="Unpack indexes from committed archives")
    
    def handle(self, *args, **options):
        action = options.get("action")
        
        if action == "check":
            self.check_indexes()
        elif action == "build":
            self.build_indexes()
        elif action == "pack":
            self.pack_indexes()
        elif action == "unpack":
            self.unpack_indexes()
        else:
            self.print_help("manage.py", "indexctl")
    
    def check_indexes(self):
        """Check if indexes are stale compared to data."""
        manifest_path = Path("search/index_manifest.json")
        
        if not manifest_path.exists():
            self.stdout.write(self.style.WARNING("No manifest found - indexes need building"))
            return False
        
        with manifest_path.open() as f:
            manifest = json.load(f)
        
        current_hash = get_data_hash()
        stored_hash = manifest.get("data_hash")
        
        if current_hash != stored_hash:
            self.stdout.write(self.style.WARNING(
                f"Indexes are STALE (data hash changed)\n"
                f"  Stored: {stored_hash}\n"
                f"  Current: {current_hash}"
            ))
            return False
        
        # Check that unpacked indexes exist
        whoosh_path = Path(settings.HAYSTACK_CONNECTIONS['default']['PATH'])
        vector_path = Path(settings.BASE_DIR) / "server" / "vector_index.pkl"
        
        if not whoosh_path.exists():
            self.stdout.write(self.style.WARNING("Whoosh index missing - run 'indexctl unpack'"))
            return False
        
        if not vector_path.exists():
            self.stdout.write(self.style.WARNING("Vector index missing - run 'indexctl unpack'"))
            return False
        
        self.stdout.write(self.style.SUCCESS(f"Indexes are current (hash: {current_hash[:12]}...)"))
        return True
    
    def build_indexes(self):
        """Build all search indexes."""
        self.stdout.write("Building search indexes...")
        
        # Build using existing buildindex command
        call_command('buildindex', '--v1', '--v2')
        
        # Update manifest
        self._update_manifest()
        
        self.stdout.write(self.style.SUCCESS("Indexes built successfully"))
    
    def pack_indexes(self):
        """Pack indexes into compressed archives for committing."""
        whoosh_path = Path(settings.HAYSTACK_CONNECTIONS['default']['PATH'])
        vector_path = Path(settings.BASE_DIR) / "server" / "vector_index.pkl"
        archive_dir = Path("search/indexes")
        
        archive_dir.mkdir(exist_ok=True)
        
        # Pack Whoosh index
        if whoosh_path.exists():
            whoosh_archive = archive_dir / "whoosh_index.tar.gz"
            self.stdout.write(f"Packing Whoosh index to {whoosh_archive}...")
            with tarfile.open(whoosh_archive, "w:gz") as tar:
                tar.add(whoosh_path, arcname="whoosh_index")
            self.stdout.write(f"  Size: {whoosh_archive.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            self.stdout.write(self.style.WARNING("Whoosh index not found, skipping"))
        
        # Pack vector index
        if vector_path.exists():
            vector_archive = archive_dir / "vector_index.pkl.gz"
            self.stdout.write(f"Packing vector index to {vector_archive}...")
            with vector_path.open("rb") as f_in:
                with gzip.open(vector_archive, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self.stdout.write(f"  Size: {vector_archive.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            self.stdout.write(self.style.WARNING("Vector index not found, skipping"))
        
        # Update manifest
        self._update_manifest()
        
        self.stdout.write(self.style.SUCCESS(
            f"Indexes packed. Commit:\n"
            f"  search/indexes/\n"
            f"  search/index_manifest.json"
        ))
    
    def unpack_indexes(self):
        """Unpack indexes from committed archives."""
        archive_dir = Path("search/indexes")
        whoosh_archive = archive_dir / "whoosh_index.tar.gz"
        vector_archive = archive_dir / "vector_index.pkl.gz"
        
        whoosh_path = Path(settings.HAYSTACK_CONNECTIONS['default']['PATH'])
        vector_path = Path(settings.BASE_DIR) / "server" / "vector_index.pkl"
        
        # Unpack Whoosh index
        if whoosh_archive.exists():
            self.stdout.write(f"Unpacking Whoosh index...")
            if whoosh_path.exists():
                shutil.rmtree(whoosh_path)
            with tarfile.open(whoosh_archive, "r:gz") as tar:
                tar.extractall(whoosh_path.parent)
            self.stdout.write(self.style.SUCCESS("  Whoosh index unpacked"))
        else:
            self.stdout.write(self.style.WARNING("No Whoosh archive found"))
        
        # Unpack vector index
        if vector_archive.exists():
            self.stdout.write(f"Unpacking vector index...")
            with gzip.open(vector_archive, "rb") as f_in:
                with vector_path.open("wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self.stdout.write(self.style.SUCCESS("  Vector index unpacked"))
        else:
            self.stdout.write(self.style.WARNING("No vector archive found"))
        
        self.stdout.write(self.style.SUCCESS("Indexes unpacked"))
    
    def _update_manifest(self):
        """Update the index manifest file."""
        manifest = {
            "data_hash": get_data_hash(),
            "version": 1,
        }
        
        manifest_path = Path("search/index_manifest.json")
        with manifest_path.open("w") as f:
            json.dump(manifest, f, indent=2)
        
        self.stdout.write(f"Manifest updated (hash: {manifest['data_hash'][:12]}...)")

