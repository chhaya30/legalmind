"""Rebuild all chunk embeddings with the configured model."""
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.document import Chunk
from app.retrieval.engine import index_chunks


def main():
    db = SessionLocal()
    try:
        chunks = db.scalars(select(Chunk).order_by(Chunk.document_id, Chunk.chunk_index)).all()
        count = index_chunks(db, chunks)
        print(f"Indexed {count} chunks.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
