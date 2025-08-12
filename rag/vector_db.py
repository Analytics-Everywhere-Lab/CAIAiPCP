from typing import Any, Dict, List
import chromadb
import torch
from sentence_transformers import SentenceTransformer

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "medical_rag"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class MedicalVectorDB:
    def __init__(
        self, db_path: str = CHROMA_DB_PATH, collection_name: str = COLLECTION_NAME
    ):
        self.db_path = db_path
        self.collection_name = collection_name

        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=DEVICE)

        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize or get existing collection."""
        try:
            self.collection = self.chroma_client.get_collection(
                name=self.collection_name
            )
            existing_count = self.collection.count()
            print(
                f"Collection '{self.collection_name}' already exists with {existing_count} documents."
            )
        except Exception as e:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Medical RAG Dataset Embeddings"},
            )
            print(f"Created new collection '{self.collection_name}'.")

    def is_indexed(self) -> bool:
        """Check if the collection is indexed."""
        try:
            count = self.collection.count()
            return count > 0
        except:
            return False

    def get_document_count(self) -> int:
        try:
            return self.collection.count()
        except:
            return 0

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            retrieved_docs = []
            for i in range(len(results["documents"][0])):
                retrieved_docs.append(
                    {
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "similarity_score": 1 - results["distances"][0][i],
                    }
                )

            return retrieved_docs

        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "document_count": self.get_document_count(),
            "collection_name": self.collection_name,
            "db_path": self.db_path,
            "is_indexed": self.is_indexed(),
        }
