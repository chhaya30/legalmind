"""phase3 rag
Revision ID: 0003_phase3_rag
Revises: 0002_phase2_retrieval
"""
from alembic import op
import sqlalchemy as sa

revision='0003_phase3_rag'
down_revision='0002_phase2_retrieval'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('rag_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=40), nullable=False),
        sa.Column('evidence_ids', sa.JSON(), nullable=False),
        sa.Column('citation_ids', sa.JSON(), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('coverage', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('insufficient_evidence', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('rag_events')
