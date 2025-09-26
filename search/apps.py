import pickle
from pathlib import Path
from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
    vector_index = None  # Class attribute to store the loaded index
    
    def ready(self):
        """Load vector index once when Django starts."""
        vector_index_path = Path('server/vector_index.pkl')
        
        if vector_index_path.exists():
            try:
                print("Loading vector search index...")
                with vector_index_path.open('rb') as f:
                    SearchConfig.vector_index = pickle.load(f)
                
                # Print basic info about the loaded index
                if SearchConfig.vector_index and 'matrix' in SearchConfig.vector_index:
                    matrix_shape = SearchConfig.vector_index['matrix'].shape
                    print(f"Vector index loaded successfully: {matrix_shape}")
                else:
                    print("Vector index loaded but missing expected components")
                    
            except Exception as e:
                print(f"Failed to load vector index: {e}")
                SearchConfig.vector_index = None
        else:
            print(f"Vector index file not found: {vector_index_path}")
            SearchConfig.vector_index = None
