"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create search_logs table
    op.create_table(
        'search_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.String(length=255), nullable=True),
        sa.Column('request_json', sa.JSON(), nullable=False),
        sa.Column('response_meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_logs_conversation_id'), 'search_logs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_search_logs_id'), 'search_logs', ['id'], unique=False)

    # Create saved_searches table
    op.create_table(
        'saved_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('request_json', sa.JSON(), nullable=False),
        sa.Column('results_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_searches_id'), 'saved_searches', ['id'], unique=False)
    op.create_index(op.f('ix_saved_searches_user_id'), 'saved_searches', ['user_id'], unique=False)

    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('place_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('thumbs_up', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)
    op.create_index(op.f('ix_feedback_place_id'), 'feedback', ['place_id'], unique=False)
    op.create_index(op.f('ix_feedback_user_id'), 'feedback', ['user_id'], unique=False)

    # Create profiles table
    op.create_table(
        'profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profiles_id'), 'profiles', ['id'], unique=False)
    op.create_index(op.f('ix_profiles_user_id'), 'profiles', ['user_id'], unique=True)

    # Create profile_preferences table
    op.create_table(
        'profile_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profile_preferences_id'), 'profile_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_profile_preferences_profile_id'), 'profile_preferences', ['profile_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_profile_preferences_profile_id'), table_name='profile_preferences')
    op.drop_index(op.f('ix_profile_preferences_id'), table_name='profile_preferences')
    op.drop_table('profile_preferences')
    
    op.drop_index(op.f('ix_profiles_user_id'), table_name='profiles')
    op.drop_index(op.f('ix_profiles_id'), table_name='profiles')
    op.drop_table('profiles')
    
    op.drop_index(op.f('ix_feedback_user_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_place_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_table('feedback')
    
    op.drop_index(op.f('ix_saved_searches_user_id'), table_name='saved_searches')
    op.drop_index(op.f('ix_saved_searches_id'), table_name='saved_searches')
    op.drop_table('saved_searches')
    
    op.drop_index(op.f('ix_search_logs_id'), table_name='search_logs')
    op.drop_index(op.f('ix_search_logs_conversation_id'), table_name='search_logs')
    op.drop_table('search_logs')