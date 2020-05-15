import logging
from uuid import UUID
from typing import Optional
from sqlalchemy import func
from app.models import (
    Site,
    Building,
    BuildingFloor,
    BuildingFloorConnector,
    Cmdb,
    Elevator,
    ElevatorFloor,
    FloorFacility,
    SiteGroup,
    SiteFacilityUnit,
    Robot,
    Unit,
    session,
)

logger = logging.getLogger(__name__)


"""
绑定相关api
楼宇内的设施是坑位 需要绑定iot(近场通讯)板子  才能和机器人交互
楼宇内的机器人其实是机器人坑位 需要绑定真正的机器人
"""


def get_unbind_unit(unit_type: int, limit: int = 10, offset: int = 1) -> list:
    from manage import make_shell_ctx

    make_shell_ctx()
    # 获取所有未绑定的unit
    units = (
        session.query(Cmdb)
        .filter(Cmdb.site_uuid == None, Cmdb.unit_type == unit_type)
        .paginate(offset, limit)
        .items
    )
    return [i.get_unit_info() for i in units]


def bind_cmdb_unit(site_uuid: UUID, site_uid: int, unit_uuid: UUID, unit_type: int):
    # cmdb端加绑
    cmdb = Cmdb.get(unit_uuid)
    if not cmdb:
        # 绑定iot不存在
        raise

    if unit_type != cmdb.unit_type:
        raise

    cmdb.site_uuid = site_uuid
    cmdb.site_uid = site_uid
    session.flush()


def unbind_cmdb_unit(unit_uuid: UUID):
    # cmdb端解绑
    cmdb = Cmdb.get(unit_uuid)
    if not cmdb:
        # 绑定iot不存在
        raise

    cmdb.site_uuid = None
    cmdb.site_uid = 0
    session.flush()


def bind_site_unit(
    site_uuid: UUID,
    site_uid: int,
    unit_uuid: UUID,
    facility_uuid: UUID,
    force: bool = False,
):
    # site端加绑
    cmdb = Cmdb.get(unit_uuid)
    if not cmdb:
        # 绑定iot不存在
        raise

    # iot设备此前是否已经绑定  如果绑定则根据force参数决定是否强制加解绑定
    old_sfu = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.unit_uuid == unit_uuid)
        .first()
    )
    if old_sfu:
        if force:
            unbind_site_unit(old_sfu.facility_uuid)
        else:
            logger.error(
                "Unit already bind to another facility, unit_uuid = {}, facility_uuid = {}".format(
                    unit_uuid, facility_uuid
                )
            )
            raise

    new_sfu = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.facility_uuid == facility_uuid)
        .scalar()
    )
    if not new_sfu:
        # 要绑定的设施不存在
        raise
    if new_sfu.unit_type != cmdb.unit_type:

        logger.error(
            "Unit type not matched with CMDB, unit_uuid = {}, unit_name = {}, unit_type = {}, cmdb_type = {}".format(
                unit_uuid, cmdb.unit_name, new_sfu.unit_type, cmdb.unit_type
            )
        )
        raise

    try:
        bind_cmdb_unit(site_uuid, site_uid, unit_uuid, new_sfu.unit_type)

        new_sfu.unit_uuid = unit_uuid
        new_sfu.unit_name = cmdb.unit_name
        new_sfu.unit_uid = cmdb.unit_uid
        # 注意此处session没有提交
        session.flush()
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise

    logger.info("bind facility {} -> {}".format(facility_uuid, unit_uuid))


def unbind_site_unit(facility_uuid: UUID,):
    new_sfu = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.facility_uuid == facility_uuid)
        .scalar()
    )
    if not new_sfu:
        # 要解绑定的设施不存在
        raise

    if not new_sfu.unit_uuid:
        return

    try:
        unbind_cmdb_unit(new_sfu.unit_uuid)

        new_sfu.unit_uuid = None
        new_sfu.unit_name = ""
        new_sfu.unit_uid = 0
        # 注意此处session没有提交
        session.flush()
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise

    logger.info("bind facility {} -> NONE".format(facility_uuid))


def get_buildings_bind_units(building_uuid: UUID, unit_type: int) -> list:
    # 获取building下已经绑定的units
    building = session.query(Building).filter(Building.uuid == building_uuid).scalar()

    def get_info(info):
        return {
            "unit_uuid": str(info.unit_uuid),
            "unit_uid": info.unit_uid,
            "unit_name": info.unit_name,
            "unit_type": info.unit_type,
        }

    mappings = {
        Unit.UNIT_TYPE_ELEVATOR: building.elevators,
        Unit.UNIT_TYPE_AUTO_DOOR: building.auto_doors,
        Unit.UNIT_TYPE_STATION: building.stations,
        Unit.UNIT_TYPE_CHARGER: building.chargers,
        Unit.UNIT_TYPE_GATE: building.gates,
        Unit.UNIT_TYPE_IOT_GENERAL: [],
        Unit.UNIT_TYPE_CALL: [],
    }

    members = mappings[unit_type]
    sfus = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.unit_uuid != None)
        .filter(SiteFacilityUnit.facility_uuid.in_(members))
        .all()
    )
    return [get_info(i) for i in sfus]


def get_bond_robots(site_uuid: UUID) -> list:
    # site下已经绑定的robot
    return (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.site_uuid == site_uuid)
        .filter(SiteFacilityUnit.unit_uuid != None)
        .filter(SiteFacilityUnit.unit_type == Unit.UNIT_TYPE_ROBOT)
        .all()
    )


def get_unit_list(unit_type: int, site_uuid: UUID, building_uuid: UUID = None) -> list:
    # 获取未绑定的units和同building下或site下已绑定的unit
    # 即同building下已经绑定过的unit可以再次绑定到同building下其他facility上(不过要把之前的绑定解绑)
    if unit_type is None:
        return []

    def get_info(info):
        return {
            "unit_uuid": str(info.unit_uuid),
            "unit_uid": info.unit_uid,
            "unit_name": info.unit_name,
            "unit_type": info.unit_type,
        }

    unit_list = get_unbind_unit(unit_type)
    if building_uuid and unit_type != Unit.UNIT_TYPE_ROBOT:
        unit_list += get_buildings_bind_units(building_uuid, unit_type)
    else:
        robots = get_bond_robots(site_uuid)
        unit_list += [get_info(i) for i in robots]

    return unit_list


def update_bind_facility(site_uuid: UUID, new_bind_facility: list, unit_type: int):
    # 绑定或解绑定某个类型的facilities 每次传过来同一个building下的绑定数据(robot例外)
    # new_bind_facility是前端传过来的字典列表 字典中包含同一building下(如果是robot则是同一site下)所有的绑定未绑定设备
    # {"facility_uuid": "...", "unit_uuid": "..."}
    if not new_bind_facility:
        return
    site = session.query.get(site_uuid)
    site.version_id += 1

    # 前端传过来的uuid  这里要求前端要把site下同building下所有同类型的facility数据传过来 后台作比较验证
    # 如果是robot 则没有building限制
    front_facility_uuids = [i.get("facility_uuid") for i in new_bind_facility]
    sfus = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.facility_uuid.in_(front_facility_uuids))
        .all()
    )
    assert len(sfus) == len(set(front_facility_uuids))

    # 同一个building下的facility接棒后可以再次绑定的同building下其他的facility上
    # 此前绑定过的组合就无需再次绑定 未绑定的组合调用绑定方法即可
    # facility_uuid, unit_uuid 组成元组  以元组为单位区分此前是否绑定过

    new_bind_list = [
        (i.get("facility_uuid"), i.get("unit_uuid"))
        for i in new_bind_facility
        if i.get("unit_uuid")
    ]

    one_faility_uuid = new_bind_facility[0]["facility_uuid"]
    if unit_type != Unit.UNIT_TYPE_ROBOT:
        if unit_type == Unit.UNIT_TYPE_ELEVATOR:
            cls = Elevator
        else:
            cls = FloorFacility

        facility = session.query(cls).get(one_faility_uuid)
        building_uuid = facility.building_uuid

        groups = (
            session.query(SiteGroup)
            .filter(
                SiteGroup.unit_type == unit_type,
                SiteGroup.building_uuid == building_uuid,
            )
            .all()
        )
        one_building_groups = [i.uuid for i in groups]
        old_sfus = (
            session.query(SiteFacilityUnit)
            .filter(SiteFacilityUnit.group_uuid.in_(one_building_groups))
            .all()
        )
        old_bind_list = [
            (str(i.facility_uuid), str(i.unit_uuid)) for i in old_sfus if i.unit_uuid
        ]
    else:
        binded_sfu = (
            session.query(SiteFacilityUnit)
            .filter(
                SiteFacilityUnit.site_uuid == site_uuid,
                SiteFacilityUnit.unit_type == unit_type,
                SiteFacilityUnit.unit_uuid != None,
            )
            .all()
        )
        old_bind_list = [(str(i.facility_uuid), str(i.unit_uuid)) for i in binded_sfu]

    for old in old_bind_list:
        if old not in new_bind_list:
            unbind_site_unit(UUID(old[0]))

    for new_ in new_bind_list:
        if new_ not in old_bind_list:
            bind_site_unit(site.uuid, site.site_uid, UUID(new_[1]), UUID(new_[0]))

    session.flush()
    try:
        session.commit()
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise

    logger.info(
        "[API.SECTION_UPDATE] update_section_facility(site_uuid={}, new_section_facility={})".format(
            site_uuid, new_bind_facility
        )
    )
