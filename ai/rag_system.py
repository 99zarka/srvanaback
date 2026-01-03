import os
import json
import time
import numpy as np
from .embedding_utils import get_embedding, cosine_similarity

class AIAssistantRAG:
    INDEX_FILE = "ai_assistant_embeddings.npy"
    METADATA_FILE = "ai_assistant_metadata.json"

    def __init__(self, db_alias='default'):
        self.db_alias = db_alias
        self.embeddings = {}  # key -> embedding vector
        self.metadata = {}    # key -> original data
        self.load_or_build_index()
    
    def load_or_build_index(self):
        """Load existing index or build new one."""
        if self.is_index_fresh():
            self.load_index()
            print(f"Loaded existing index with {len(self.embeddings)} embeddings")
        else:
            self.build_index()
    
    def is_index_fresh(self):
        """Check if index is less than 24 hours old."""
        if not os.path.exists(self.INDEX_FILE):
            return False
        
        file_age = time.time() - os.path.getmtime(self.INDEX_FILE)
        return file_age < 24 * 3600  # 24 hours
    
    def build_index(self):
        """Build embeddings index from database using serializers."""
        print("Building AI Assistant Index for Egypt-based services platform...")
        
        # Clear existing data
        self.embeddings.clear()
        self.metadata.clear()
        
        # 1. Build technician embeddings
        self._build_technician_embeddings()
        
        # 2. Build service embeddings
        self._build_service_embeddings()
        
        # 3. Build order embeddings
        self._build_order_embeddings()
        
        # 4. Save index
        self.save_index()
        print(f"Index built with {len(self.embeddings)} embeddings for Egyptian marketplace")
    
    def _build_technician_embeddings(self):
        """Build embeddings for all technicians."""
        from users.serializers.user_serializers import UserSerializer
        from users.models import User

        print("Building technician embeddings...")

        # Get all technicians with optimized queries
        technicians = User.objects.using(self.db_alias).filter(
            user_type__user_type_name='technician'
        ).select_related('user_type').prefetch_related('received_reviews')
        
        serializer = UserSerializer(technicians, many=True)
        tech_data = serializer.data
        
        for tech in tech_data:
            # Create embedding from JSON data
            json_text = json.dumps(tech, ensure_ascii=False, indent=2)
            embedding = get_embedding(json_text)
            
            key = f"technician_{tech['user_id']}"
            self.embeddings[key] = embedding
            self.metadata[key] = tech
    
    def _build_service_embeddings(self):
        """Build embeddings for all services."""
        from services.serializers import ServiceSerializer
        from services.models import Service

        print("Building service embeddings...")

        # Get all services
        services = Service.objects.using(self.db_alias).all()
        serializer = ServiceSerializer(services, many=True)
        service_data = serializer.data
        
        for service in service_data:
            # Create embedding from JSON data
            json_text = json.dumps(service, ensure_ascii=False, indent=2)
            embedding = get_embedding(json_text)
            
            key = f"service_{service['service_id']}"
            self.embeddings[key] = embedding
            self.metadata[key] = service
    
    def _build_order_embeddings(self):
        """Build embeddings for all orders."""
        from orders.serializers import PublicOrderSerializer
        from orders.models import Order

        print("Building order embeddings...")

        # Get all orders with optimized queries
        orders = Order.objects.using(self.db_alias).select_related(
            'client_user', 'client_user__user_type', 'service'
        ).prefetch_related(
            'client_user__received_reviews',
            'project_offers__technician_user',
            'project_offers__technician_user__user_type'
        )
        
        serializer = PublicOrderSerializer(orders, many=True)
        order_data = serializer.data
        
        for order in order_data:
            # Create embedding from JSON data
            json_text = json.dumps(order, ensure_ascii=False, indent=2)
            embedding = get_embedding(json_text)
            
            key = f"order_{order['order_id']}"
            self.embeddings[key] = embedding
            self.metadata[key] = order
    
    def save_index(self):
        """Save embeddings and metadata to disk."""
        # Save embeddings as numpy array
        embedding_array = np.array(list(self.embeddings.values()))
        np.save(self.INDEX_FILE, embedding_array)
        
        # Save metadata as JSON
        with open(self.METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def load_index(self):
        """Load embeddings and metadata from disk."""
        # Load embeddings
        embedding_array = np.load(self.INDEX_FILE)
        
        # Load metadata
        with open(self.METADATA_FILE, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        # Rebuild embeddings dict
        keys = list(self.metadata.keys())
        for i, key in enumerate(keys):
            self.embeddings[key] = embedding_array[i]
    
    def find_matches(self, query, top_k=5):
        """Find best matches for a query across all data types."""
        # Create embedding for query
        query_embedding = np.array(get_embedding(query))
        
        # Calculate similarities
        similarities = []
        for key, embedding in self.embeddings.items():
            similarity = cosine_similarity(query_embedding, np.array(embedding))
            similarities.append((key, similarity))
        
        # Get top matches
        top_matches = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
        
        # Return with metadata
        results = []
        for key, similarity in top_matches:
            results.append({
                'key': key,
                'data': self.metadata[key],
                'similarity': float(similarity)
            })
        
        return results
    
    def get_technician_matches(self, query, top_k=3):
        """Get top technician matches for a query."""
        matches = self.find_matches(query, top_k * 2)  # Get more matches, then filter
        tech_matches = [m for m in matches if m['key'].startswith('technician_')]
        return tech_matches[:top_k]
