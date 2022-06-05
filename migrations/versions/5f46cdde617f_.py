"""empty message

Revision ID: 5f46cdde617f
Revises: 
Create Date: 2022-06-05 12:55:01.845520

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f46cdde617f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Artists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('city', sa.String(length=120), nullable=True),
    sa.Column('state', sa.String(length=120), nullable=True),
    sa.Column('phone', sa.String(length=120), nullable=True),
    sa.Column('genres', sa.String(), nullable=True),
    sa.Column('image_link', sa.String(length=500), nullable=True),
    sa.Column('facebook_link', sa.String(length=120), nullable=True),
    sa.Column('website_link', sa.String(length=120), nullable=True),
    sa.Column('is_venue_seeking', sa.Boolean(), nullable=False),
    sa.Column('venue_seeking_description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('Venues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('city', sa.String(length=120), nullable=True),
    sa.Column('state', sa.String(length=120), nullable=True),
    sa.Column('address', sa.String(length=120), nullable=True),
    sa.Column('phone', sa.String(length=120), nullable=True),
    sa.Column('genres', sa.String(), nullable=True),
    sa.Column('image_link', sa.String(length=500), nullable=True),
    sa.Column('facebook_link', sa.String(length=120), nullable=True),
    sa.Column('website_link', sa.String(length=120), nullable=True),
    sa.Column('is_talent_seeking', sa.Boolean(), nullable=False),
    sa.Column('talent_seeking_description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('show_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('artist_id', sa.Integer(), nullable=False),
    sa.Column('venue_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['artist_id'], ['Artists.id'], ),
    sa.ForeignKeyConstraint(['venue_id'], ['Venues.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('show_items')
    op.drop_table('Venues')
    op.drop_table('Artists')
    # ### end Alembic commands ###