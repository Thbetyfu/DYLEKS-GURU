import pytest
from unittest.mock import AsyncMock, patch
from app.services.rag_service import RAGService

def test_cosine_similarity():
    service = RAGService()
    
    # Uji kesamaan 100% (vektor yang sama)
    v1 = [1.0, 2.0, 3.0]
    v2 = [1.0, 2.0, 3.0]
    assert abs(service._cosine_similarity(v1, v2) - 1.0) < 1e-6

    # Uji vektor orthogonal (sudut 90 derajat, similarity = 0)
    v3 = [1.0, 0.0]
    v4 = [0.0, 1.0]
    assert abs(service._cosine_similarity(v3, v4) - 0.0) < 1e-6

    # Uji vektor berlawanan arah (sudut 180 derajat, similarity = -1)
    v5 = [1.0, 1.0]
    v6 = [-1.0, -1.0]
    assert abs(service._cosine_similarity(v5, v6) - (-1.0)) < 1e-6

@pytest.mark.asyncio
async def test_rag_search():
    service = RAGService()
    
    # Mock method embedding secara langsung agar tidak memicu HTTP request
    service._get_query_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    
    # Mock data dokumen di dalam memori
    service.documents = [
        {
            "id": "doc1",
            "category": "Test",
            "title": "Materi Uji 1",
            "content": "Ini adalah dokumen rujukan pengujian kesatu.",
            "vector": [0.1, 0.2, 0.3]
        },
        {
            "id": "doc2",
            "category": "Test",
            "title": "Materi Uji 2",
            "content": "Ini adalah dokumen rujukan pengujian kedua.",
            "vector": [-0.1, -0.2, -0.3]
        }
    ]

    results = await service.search("kueri uji", top_k=1, min_score=0.5)
    
    # Harus mengembalikan 1 dokumen terdekat (doc1) yang berjarak dekat
    assert len(results) == 1
    assert results[0]["title"] == "Materi Uji 1"
    assert results[0]["score"] > 0.99
