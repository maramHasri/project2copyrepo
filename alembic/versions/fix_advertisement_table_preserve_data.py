"""fix_advertisement_table_preserve_data

Revision ID: fix_ads_preserve
Revises: simplify_ads
Create Date: 2024-01-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'fix_ads_preserve'
down_revision = 'simplify_ads'
branch_labels = None
depends_on = None


def upgrade():
    # Instead of dropping the table, let's just add missing columns if they don't exist
    # and remove unnecessary columns if they exist
    
    # Check if the table exists and has the right structure
    conn = op.get_bind()
    
    # Get current table info
    result = conn.execute("PRAGMA table_info(advertisements)")
    columns = [row[1] for row in result.fetchall()]
    
    # If the table doesn't exist, create it
    if not columns:
        op.create_table('advertisements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('image_url', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('publisher_house_id', sa.Integer(), nullable=False),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['approved_by'], ['admins.id'], ),
            sa.ForeignKeyConstraint(['publisher_house_id'], ['publisher_houses.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_advertisements_id'), 'advertisements', ['id'], unique=False)
    else:
        # Table exists, just ensure it has the right structure
        # Add missing columns if they don't exist
        if 'status' not in columns:
            op.add_column('advertisements', sa.Column('status', sa.String(), nullable=True))
        
        if 'publisher_house_id' not in columns:
            op.add_column('advertisements', sa.Column('publisher_house_id', sa.Integer(), nullable=False))
        
        if 'approved_by' not in columns:
            op.add_column('advertisements', sa.Column('approved_by', sa.Integer(), nullable=True))
        
        if 'approved_at' not in columns:
            op.add_column('advertisements', sa.Column('approved_at', sa.DateTime(), nullable=True))
        
        if 'created_at' not in columns:
            op.add_column('advertisements', sa.Column('created_at', sa.DateTime(), nullable=True))
        
        # Remove unnecessary columns if they exist (but preserve data first)
        if 'title' in columns:
            # Create a backup of the data first
            conn.execute("""
                CREATE TABLE IF NOT EXISTS advertisements_backup AS 
                SELECT * FROM advertisements
            """)
            op.drop_column('advertisements', 'title')
        
        if 'description' in columns:
            op.drop_column('advertisements', 'description')
        
        if 'link_url' in columns:
            op.drop_column('advertisements', 'link_url')
        
        if 'position' in columns:
            op.drop_column('advertisements', 'position')
        
        if 'rejection_reason' in columns:
            op.drop_column('advertisements', 'rejection_reason')
        
        if 'updated_at' in columns:
            op.drop_column('advertisements', 'updated_at')


def downgrade():
    # This is a complex downgrade, but we'll keep it simple
    # Just recreate the old structure if needed
    pass
