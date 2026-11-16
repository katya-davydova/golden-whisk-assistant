
import os
import hashlib
import logging
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "data"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-openai-index")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL_NAME", "text-embedding-3-small"
)

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    raise RuntimeError("Check OPENAI_API_KEY and PINECONE_API_KEY")

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

def load_documents():
    documents = []

    for path in sorted(DOCUMENTS_DIR.rglob("*")):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            loaded = PyPDFLoader(str(path)).load()
        elif suffix in {".txt", ".md"}:
            loaded = TextLoader(
                str(path), encoding="utf-8"
            ).load()
        else:
            continue

        for doc in loaded:
            doc.metadata["source"] = str(
                path.relative_to(DOCUMENTS_DIR)
            )

        documents.extend(loaded)
        logger.info("Loaded %s", path.name)

    if not documents:
        raise RuntimeError(
            f"No supported documents found in {DOCUMENTS_DIR}"
        )

    return documents

def main():
    documents = load_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)

    ids = []
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page", 0)
        start = chunk.metadata.get("start_index", 0)

        raw_id = (
            f"{source}|{page}|{start}|{chunk.page_content}"
        )
        ids.append(
            hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
        )

    pc = Pinecone(api_key=PINECONE_API_KEY)

    if INDEX_NAME not in pc.list_indexes().names():
        raise RuntimeError(
            f"Index '{INDEX_NAME}' not found. Run create_index.py."
        )

    description = pc.describe_index(INDEX_NAME)

    if description.dimension != 1536:
        raise RuntimeError(
            f"Index dimension is {description.dimension}; "
            "text-embedding-3-small requires 1536."
        )

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
    )

    # Fail early if the selected embedding model has a different dimension.
    if len(embeddings.embed_query("dimension test")) != description.dimension:
        raise RuntimeError("Embedding and index dimensions do not match")

    index = pc.Index(INDEX_NAME)

    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
    )

    batch_size = 50
    for start in range(0, len(chunks), batch_size):
        vector_store.add_documents(
            documents=chunks[start:start + batch_size],
            ids=ids[start:start + batch_size],
        )
        logger.info(
            "Uploaded %d/%d chunks",
            min(start + batch_size, len(chunks)),
            len(chunks),
        )

    logger.info("Ingestion complete: %d chunks", len(chunks))

if __name__ == "__main__":
    main()
