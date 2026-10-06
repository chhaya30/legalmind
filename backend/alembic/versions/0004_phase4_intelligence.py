"""phase 4 legal intelligence"""
from alembic import op
import sqlalchemy as sa
revision='0004_phase4_intelligence'; down_revision='0003_phase3_rag'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('documents', sa.Column('nlp_model_version', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('nlp_method', sa.String(length=40), nullable=True))

def downgrade():
    op.drop_column('documents','nlp_method'); op.drop_column('documents','nlp_model_version')
