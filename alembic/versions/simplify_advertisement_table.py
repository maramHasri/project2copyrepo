"""simplify_advertisement_table

Revision ID: simplify_ads
Revises: update_ads_structure
Create Date: 2024-01-15 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'simplify_ads'
down_revision = 'update_ads_structure'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old advertisements table and recreate with simplified structure
    op.drop_table('advertisements')
    
    # Create simplified advertisements table
    op.create_table('advertisements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('publisher_house_id', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['admins.id'], ),
        sa.ForeignKeyConstraint(['publisher_house_id'], ['publisher_houses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_advertisements_id'), 'advertisements', ['id'], unique=False)


def downgrade():
    # Drop the simplified table and recreate old structure
    op.drop_table('advertisements')
    
    # Recreate old structure
    op.create_table('advertisements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('link_url', sa.String(), nullable=True),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('publisher_house_id', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['admins.id'], ),
        sa.ForeignKeyConstraint(['publisher_house_id'], ['publisher_houses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_advertisements_id'), 'advertisements', ['id'], unique=False)
