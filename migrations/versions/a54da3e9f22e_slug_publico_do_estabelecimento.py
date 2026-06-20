"""slug publico do estabelecimento

Revision ID: a54da3e9f22e
Revises: a24c28cd154e
Create Date: 2026-06-20 16:25:20.903911

"""
import re
import unicodedata
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a54da3e9f22e'
down_revision = 'a24c28cd154e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('estabelecimento', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=160), nullable=True))

    # Backfill: gera um slug a partir do nome para estabelecimentos criados
    # antes deste campo existir. Usa "<base>-<id>" para garantir unicidade
    # sem depender de consultas repetidas (id já é único por definição).
    bind = op.get_bind()
    estabelecimento = sa.table(
        'estabelecimento',
        sa.column('id', sa.Integer),
        sa.column('nome', sa.String),
        sa.column('slug', sa.String),
    )
    linhas = bind.execute(sa.select(estabelecimento.c.id, estabelecimento.c.nome)).fetchall()
    for id_, nome in linhas:
        sem_acento = unicodedata.normalize('NFKD', (nome or '').strip().lower()).encode('ascii', 'ignore').decode('ascii')
        base = re.sub(r'[^a-z0-9]+', '-', sem_acento).strip('-') or 'clinica'
        bind.execute(
            estabelecimento.update().where(estabelecimento.c.id == id_).values(slug=f"{base}-{id_}")
        )

    with op.batch_alter_table('estabelecimento', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_estabelecimento_slug', ['slug'])


def downgrade():
    with op.batch_alter_table('estabelecimento', schema=None) as batch_op:
        batch_op.drop_constraint('uq_estabelecimento_slug', type_='unique')
        batch_op.drop_column('slug')
