"""Document chunking strategies for RAG.

Two strategies:
  - Recursive character splitting (for articles, product descriptions)
  - Structured product chunking (for CSV/structured product data)
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Chinese-aware separator ordering
CN_SEPARATORS = ["\n\n", "\n", "。", ". ", "；", "，", " ", ""]


def create_recursive_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> RecursiveCharacterTextSplitter:
    """Create a recursive character text splitter optimized for Chinese."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=CN_SEPARATORS,
        keep_separator=True,
    )


def chunk_text(
    text: str,
    metadata: dict | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[dict]:
    """Split text into chunks with metadata.

    Returns list of {"content": str, "metadata": dict}.
    """
    splitter = create_recursive_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_text(text)
    base_metadata = metadata or {}
    return [
        {
            "content": chunk,
            "metadata": {**base_metadata, "chunk_index": i},
        }
        for i, chunk in enumerate(chunks)
    ]


def chunk_structured_product(
    fields: dict[str, str],
    metadata: dict | None = None,
) -> list[dict]:
    """Create chunks from structured product fields (CSV row).

    Each field becomes a separate chunk for precise retrieval.
    """
    base_metadata = metadata or {}
    chunks = []

    for field_name, value in fields.items():
        if not value or not value.strip():
            continue
        chunks.append(
            {
                "content": f"{field_name}: {value}",
                "metadata": {
                    **base_metadata,
                    "field": field_name,
                    "chunk_type": "product_spec",
                },
            }
        )

    return chunks


def chunk_document_pages(
    pages: list[dict],
    source_file: str,
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[dict]:
    """Chunk all pages from a parsed document.

    Args:
        pages: list of {"text": str, "metadata": dict} from parser
        source_file: original source file name
        chunk_size: target chunk size in characters
        chunk_overlap: overlap between chunks

    Returns list of {"content": str, "metadata": dict} ready for embedding.
    """
    all_chunks = []
    for page in pages:
        page_meta = {
            "source_file": source_file,
            **page.get("metadata", {}),
        }
        chunks = chunk_text(
            text=page["text"],
            metadata=page_meta,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(chunks)

    return all_chunks
