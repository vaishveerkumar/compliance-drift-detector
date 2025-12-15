"""
Pinecone knowledge base search tool
"""

import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Initialize once
_pc = None
_index = None
_embedding_model = None


def _get_index():
    """Lazy initialization of Pinecone index"""
    global _pc, _index, _embedding_model
    
    if _index is None:
        _pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _index = _pc.Index(os.getenv("PINECONE_INDEX_NAME", "compliance-regulations"))
        _embedding_model = SentenceTransformer("all-mpnet-base-v2")
    
    return _index, _embedding_model


def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """
    Search the compliance regulations knowledge base.
    Returns formatted string of relevant regulations.
    """
    
    index, model = _get_index()
    
    # Embed query
    query_embedding = model.encode(query).tolist()
    
    # Search
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    if not results.matches:
        return "No relevant regulations found in knowledge base."
    
    # Format results
    formatted = []
    for match in results.matches:
        source = match.metadata.get("source_name", "Unknown")
        content = match.metadata.get("content", "")
        score = match.score
        
        formatted.append(f"[Source: {source}] (Relevance: {score:.2f})\n{content}")
    
    return "\n\n---\n\n".join(formatted)