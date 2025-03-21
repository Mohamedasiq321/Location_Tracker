"""Add TargetDestination table

Revision ID: e8a6b2df53f0
Revises: 
Create Date: 2025-03-21 10:47:25.852330

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8a6b2df53f0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('location', schema=None) as batch_op:
        batch_op.add_column(sa.Column('timestamp', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('location', schema=None) as batch_op:
        batch_op.drop_column('timestamp')

    # ### end Alembic commands ###
