"""persisted postgres keyword index"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0006_search_vector'; down_revision='0005_evaluation_analytics_security'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('chunks', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    op.execute("UPDATE chunks SET search_vector = to_tsvector('english', coalesce(text, ''))")
    op.execute("CREATE INDEX ix_chunks_search_vector ON chunks USING GIN (search_vector)")
    op.execute("CREATE OR REPLACE FUNCTION legalmind_chunks_search_vector_update() RETURNS trigger AS $$ BEGIN NEW.search_vector := to_tsvector('english', coalesce(NEW.text, '')); RETURN NEW; END; $$ LANGUAGE plpgsql")
    op.execute("CREATE TRIGGER chunks_search_vector_trigger BEFORE INSERT OR UPDATE OF text ON chunks FOR EACH ROW EXECUTE FUNCTION legalmind_chunks_search_vector_update()")

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS chunks_search_vector_trigger ON chunks")
    op.execute("DROP FUNCTION IF EXISTS legalmind_chunks_search_vector_update()")
    op.drop_index('ix_chunks_search_vector', table_name='chunks')
    op.drop_column('chunks','search_vector')
