"""Vector store for medical knowledge base using ChromaDB."""

from typing import Optional

from src.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, OPENAI_API_KEY, TOP_K_RESULTS
from src.knowledge_builder import MedicalKnowledgeBase


class MedicalVectorStore:
    """ChromaDB-backed vector store for medical knowledge."""

    COLLECTION_NAME = "medical_knowledge"

    def __init__(self):
        self.kb = MedicalKnowledgeBase()
        self._client = None
        self._collection = None
        self._embeddings = None

    def _get_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        return self._client

    def _get_embeddings(self):
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings
            self._embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=OPENAI_API_KEY,
            )
        return self._embeddings

    def build_index(self, force_rebuild: bool = False) -> None:
        """Build or rebuild the vector index from the knowledge base."""
        client = self._get_client()
        if force_rebuild:
            try:
                client.delete_collection(self.COLLECTION_NAME)
            except Exception:
                pass

        from langchain_community.vectorstores import Chroma
        from langchain.schema import Document

        docs_data = self.kb.generate_documents_for_vectordb()
        documents = [
            Document(page_content=d["content"], metadata=d["metadata"])
            for d in docs_data
        ]

        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self._get_embeddings(),
            collection_name=self.COLLECTION_NAME,
            persist_directory=str(CHROMA_PERSIST_DIR),
        )
        self._collection = vectorstore

    def _get_vectorstore(self):
        if self._collection is None:
            from langchain_community.vectorstores import Chroma
            self._collection = Chroma(
                collection_name=self.COLLECTION_NAME,
                embedding_function=self._get_embeddings(),
                persist_directory=str(CHROMA_PERSIST_DIR),
            )
        return self._collection

    def similarity_search(self, query: str, k: int = TOP_K_RESULTS, filter_dict: Optional[dict] = None) -> list:
        """General semantic search."""
        vs = self._get_vectorstore()
        kwargs = {"k": k}
        if filter_dict:
            kwargs["filter"] = filter_dict
        return vs.similarity_search(query, **kwargs)

    def search_conditions(self, query: str, k: int = 5) -> list:
        return self.similarity_search(query, k=k, filter_dict={"type": "condition"})

    def search_tests(self, query: str, k: int = 5) -> list:
        return self.similarity_search(query, k=k, filter_dict={"type": "test"})

    def search_specialists(self, query: str, k: int = 3) -> list:
        return self.similarity_search(query, k=k, filter_dict={"type": "specialist"})

    def get_retriever(self, search_kwargs: Optional[dict] = None):
        vs = self._get_vectorstore()
        kwargs = search_kwargs or {"k": TOP_K_RESULTS}
        return vs.as_retriever(search_kwargs=kwargs)
