from .rag_system import AIAssistantRAG

def test_rag_system():
    """Test the RAG system."""
    print("Testing RAG System...")
    rag = AIAssistantRAG()
    
    # Test query
    query = "I need a plumber to fix a water leak in my kitchen"
    
    # Find matches
    matches = rag.find_matches(query, top_k=5)
    
    print(f"Query: {query}")
    print(f"Found {len(matches)} matches:")
    print("=" * 50)
    
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match['key']} (similarity: {match['similarity']:.3f})")
        if match['key'].startswith('technician_'):
            tech = match['data']
            print(f"   Technician: {tech['first_name']} {tech['last_name']}")
            print(f"   Specialization: {tech['specialization']}")
            print(f"   Rating: {tech['overall_rating']}")
            print(f"   Location: {tech['address']}")
        elif match['key'].startswith('service_'):
            service = match['data']
            print(f"   Service: {service['service_name']}")
            print(f"   Category: {service['category']['category_name']}")
            print(f"   Description: {service['description'][:100]}...")
        print()
    
    # Test technician-specific matches
    print("Top Technician Matches:")
    print("=" * 30)
    tech_matches = rag.get_technician_matches(query, top_k=3)
    
    for i, match in enumerate(tech_matches, 1):
        tech = match['data']
        print(f"{i}. {tech['first_name']} {tech['last_name']} (similarity: {match['similarity']:.3f})")
        print(f"   Specialization: {tech['specialization']}")
        print(f"   Rating: {tech['overall_rating']}")
        print()
    
    return matches

if __name__ == "__main__":
    test_rag_system()
