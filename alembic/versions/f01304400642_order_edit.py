"""Order edit

Revision ID: f01304400642
Revises: 257bcf7a6a4a
Create Date: 2023-07-06 02:35:54.280577

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f01304400642'
down_revision = '257bcf7a6a4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('time_created', sa.DateTime(), nullable=True))
    op.add_column('order', sa.Column('price', sa.Float(), nullable=True))
    op.add_column('order', sa.Column('delivered', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'delivered')
    op.drop_column('order', 'price')
    op.drop_column('order', 'time_created')
    # ### end Alembic commands ###
