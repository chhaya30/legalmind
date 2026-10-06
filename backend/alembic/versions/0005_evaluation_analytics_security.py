
"""phase 5 evaluation analytics security"""
from alembic import op
import sqlalchemy as sa
revision='0005_evaluation_analytics_security'; down_revision='0004_phase4_intelligence'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('documents', sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('documents', sa.Column('processing_finished_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table('evaluation_cases',
        sa.Column('id', sa.String(length=100), primary_key=True),
        sa.Column('task_type', sa.String(length=30), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('mode', sa.String(length=30), nullable=True),
        sa.Column('relevant_ids', sa.JSON(), nullable=True),
        sa.Column('expected_keywords', sa.JSON(), nullable=True),
        sa.Column('held_out', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('evaluation_results',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('metric', sa.String(length=80), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_evaluation_results_run_id','evaluation_results',['run_id'])
    op.create_index('ix_evaluation_results_case_id','evaluation_results',['case_id'])

def downgrade():
    op.drop_index('ix_evaluation_results_case_id', table_name='evaluation_results')
    op.drop_index('ix_evaluation_results_run_id', table_name='evaluation_results')
    op.drop_table('evaluation_results'); op.drop_table('evaluation_cases')
    op.drop_column('documents','processing_finished_at'); op.drop_column('documents','processing_started_at')
