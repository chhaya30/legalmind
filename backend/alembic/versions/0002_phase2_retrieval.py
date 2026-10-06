"""phase 2 retrieval tables and vector index"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0002_phase2_retrieval"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 768

def upgrade():
    op.add_column("documents", sa.Column("judgment_date", sa.Date(), nullable=True))
    op.drop_column("chunks", "embedding")
    op.create_table(
        "chunk_embeddings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("chunk_id", sa.String(36), sa.ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chunk_embeddings_chunk_id", "chunk_embeddings", ["chunk_id"], unique=True)
    op.execute(
        "CREATE INDEX ix_chunk_embeddings_embedding_hnsw "
        "ON chunk_embeddings USING hnsw (embedding vector_cosine_ops)"
    )
    op.create_table(
        "retrieval_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("retrieved_ids", sa.JSON(), nullable=False),
        sa.Column("reranked_ids", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

def downgrade():
    op.drop_table("retrieval_events")
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_embedding_hnsw")
    op.drop_index("ix_chunk_embeddings_chunk_id", table_name="chunk_embeddings")
    op.drop_table("chunk_embeddings")
    op.add_column("chunks", sa.Column("embedding", Vector(384), nullable=True))
    op.drop_column("documents", "judgment_date")
