"""empty message

Revision ID: a590abe92c24
Revises: 433070142145
Create Date: 2020-04-07 00:19:49.940355

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a590abe92c24'
down_revision = '433070142145'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('elevator')
    op.drop_table('site_facility_unit')
    op.drop_table('site')
    op.drop_table('elevator_floor')
    op.drop_table('building_floor_connector')
    op.drop_table('building')
    op.drop_table('robot')
    op.drop_table('site_group')
    op.drop_table('floor_facility')
    op.drop_table('building_floor')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('building_floor',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('floor_index', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('connected_floors', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('floor_facilities', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('uuid', name='building_floor_pkey'),
    sa.UniqueConstraint('uuid', name='building_floor_uuid_key')
    )
    op.create_table('floor_facility',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('unit_type', sa.SMALLINT(), autoincrement=False, nullable=False),
    sa.Column('direction', sa.SMALLINT(), autoincrement=False, nullable=False),
    sa.Column('building_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('group_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_floor_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uuid', name='floor_facility_pkey'),
    sa.UniqueConstraint('uuid', name='floor_facility_uuid_key')
    )
    op.create_table('site_group',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_floor_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('facility_group_sid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('unit_type', sa.SMALLINT(), autoincrement=False, nullable=False),
    sa.Column('members', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('uuid', name='site_group_pkey'),
    sa.UniqueConstraint('uuid', name='site_group_uuid_key')
    )
    op.create_table('robot',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('robot_type', sa.SMALLINT(), autoincrement=False, nullable=False),
    sa.Column('group_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('uuid', name='robot_pkey'),
    sa.UniqueConstraint('uuid', name='robot_uuid_key')
    )
    op.create_table('building',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('address', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('building_floors', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('elevators', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('chargers', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('stations', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('auto_doors', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('gates', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('uuid', name='building_pkey'),
    sa.UniqueConstraint('uuid', name='building_uuid_key')
    )
    op.create_table('building_floor_connector',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_uuid_1', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('floor_uuid_1', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_uuid_2', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('floor_uuid_2', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uuid', name='building_floor_connector_pkey'),
    sa.UniqueConstraint('uuid', name='building_floor_connector_uuid_key')
    )
    op.create_table('elevator_floor',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('elevator_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('floor_index', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('building_floor_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('is_reachable', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('uuid', name='elevator_floor_pkey'),
    sa.UniqueConstraint('uuid', name='elevator_floor_uuid_key')
    )
    op.create_table('site',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('address', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('status', sa.SMALLINT(), autoincrement=False, nullable=False),
    sa.Column('has_building_connector', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('business_types', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=False),
    sa.Column('location', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('section_site', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('section_building', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('section_map', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('section_facility', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('section_iot', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('uuid', name='site_pkey'),
    sa.UniqueConstraint('uuid', name='site_uuid_key')
    )
    op.create_table('site_facility_unit',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('site_uid', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('facility_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('group_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('facility_sid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('facility_group_index', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('unit_type', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('unit_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('unit_uid', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('unit_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uuid', name='site_facility_unit_pkey'),
    sa.UniqueConstraint('unit_uid', name='site_facility_unit_unit_uid_key'),
    sa.UniqueConstraint('unit_uuid', name='site_facility_unit_unit_uuid_key'),
    sa.UniqueConstraint('uuid', name='site_facility_unit_uuid_key')
    )
    op.create_table('elevator',
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('creator_uuid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('creator_ugid', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('modify_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('meta_info', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('is_delete', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('site_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('building_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('brand', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('elevator_floors', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('group_uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uuid', name='elevator_pkey'),
    sa.UniqueConstraint('uuid', name='elevator_uuid_key')
    )
    # ### end Alembic commands ###