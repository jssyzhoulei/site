import logging
from uuid import UUID
from typing import Optional
from sqlalchemy import func
from app.models import (
    Site,
    Building,
    BuildingFloor,
    BuildingFloorConnector,
    Elevator,
    ElevatorFloor,
    FloorFacility,
    SiteGroup,
    SiteFacilityUnit,
    Robot,
    Unit,
    session,
)
from app.handlers.build_site import flush_group_index, _bootstrap_group


logger = logging.getLogger(__name__)


def get_site_building(site_uuid: UUID):
    # 返回site的building信息 包含分组信息
    # 其中elevator比较特别 会返回两次 一次是在组内 一次是在building内
    # 修改elevator的信息之可以从building内的数据结构中修改
    # 组内的elevator仅修改分组信息  比如把电梯从货梯组转移到电梯组
    site = session.query(Site).get(site_uuid)
    if site is None:
        return {}

    site_building = {
        "buildings": [],
        "robot_groups": [],
        "created_at": str(site.create_time),
        "updated_at": str(site.modify_time),
        "version_id": site.version_id,
        "uuid": str(site.uuid),
        "site_uid": site.site_uid,
    }

    buildings = (
        session.query(Building)
        .filter(Building.site_uuid == site_uuid)
        .order_by(Building.create_time)
        .all()
    )
    for build in buildings:
        site_building["buildings"].append(build.get_building_info())

    robot_groups = (
        session.query(SiteGroup)
        .filter(
            SiteGroup.site_uuid == site_uuid,
            SiteGroup.unit_type == Unit.UNIT_TYPE_ROBOT,
        )
        .order_by(SiteGroup.create_time)
        .all()
    )
    for r_g in robot_groups:
        site_building["robot_groups"].append(r_g.get_site_group_info())

    return site_building


def update_site_building(site_uuid: UUID, site_building: dict):
    # 修改building信息
    site = session.query(Site).get(site_uuid)
    if not site:
        raise

    buildings = site_building["buildings"]
    robot_groups = site_building["robot_groups"]

    try:
        session.commit()
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise

    logger.info(
        f"[API.SECTION_UPDATE] update_site_building(site_uuid={site_uuid}, site_building={site_building})"
    )


def update_building(site_uuid: UUID, building: dict):
    """
    "building_floors": self.get_building_floors_info(),
    "elevators": self.get_elevators_info(),
    "elevator_groups": self.get_elevator_group(),
    "charger_groups": self.get_charger_info(),
    "station_groups": self.get_station_info(),
    "auto_door_groups": self.get_auto_door_info(),
    "gate_groups":
    """
    building_uuid = building["uuid"]
    building_db = session.query(Building).get(building_uuid)
    elevators = (
        session.query(Elevator).filter(Elevator.building_uuid == building_uuid).all()
    )
    ele_map = {str(i.uuid): i for i in elevators}
    elevator_reqs = building["elevators"]
    for ele_req in elevator_reqs:
        ele = ele_map[ele_req["uuid"]]
        ele.name = ele_req["name"]
        ele.brand = ele_req["brand"]
        _update_elevator_floors(ele.uuid, ele_req["elevator_floors"])

    building_floors = (
        session.query(BuildingFloor)
        .filter(BuildingFloor.building_uuid == building_uuid)
        .all()
    )
    build_map = {str(i.uuid): i for i in building_floors}
    building_floor_reqs = building["building_floors"]
    for building_floor_req in building_floor_reqs:
        building_floor = build_map[building_floor_req["uuid"]]
        building_floor.name = building_floor_req["name"]

    groups_db = (
        session.query(SiteGroup).filter(SiteGroup.building_uuid == building_uuid).all()
    )
    groups_db_map = {str(i): i for i in groups_db}
    for key in [
        "elevator_groups",
        "charger_groups",
        "station_groups",
        "auto_door_groups",
        "gate_groups",
    ]:
        _update_facility_group(building[key], groups_db_map, site_uuid, building_uuid)


def _update_elevator_floors(elevator_uuid: UUID, ele_floors: list):
    elevator_floors = session.query(ElevatorFloor).filter(
        ElevatorFloor.elevator_uuid == elevator_uuid
    )
    ele_floor_map = {str(i): i for i in elevator_floors}
    for ele_floor_req in ele_floors:
        ele_floor = ele_floor_map[ele_floor_req["uuid"]]
        ele_floor.name = ele_floor_req["name"]
        if ele_floor_req["name"] != "-":
            ele_floor.is_reachable = True
        if ele_floor_req.get("building_floor_uuid"):
            # 创建关联楼层信息
            pass


def _update_robot_group(site_uuid: UUID, robot_groups: dict):
    pass


def _update_facility_group(
    groups: list, groups_db_map: dict, site_uuid: UUID, building_uuid: UUID = None
):
    # 修改分组信息
    # 比较特别的是elevator和robot组
    # elevator有building uuid 没有building floor uuid
    # robot 两者都没有
    # 组内数据members可以移动 所以要刷新group index
    # 分组数据比较特别 可以更新分组  也可以新增分组 但是不允许新增空的分组
    # 允许把已有的分组members全部挪到别的分组去（这种方式产生空的分组  是被允许的）
    """
    "uuid": str(self.uuid),
    "name": self.name,
    "building_floor_uuid": str(self.building_floor_uuid or ""),
    "unit_type": self.unit_type,
    "members"
    """
    if not groups:
        return

    unit_type = groups[0]["unit_type"]
    for group in groups:
        # todo 验证mebers uuid类型
        group_member_list = [i["uuid"] for i in group["members"]]
        cls = FloorFacility
        if unit_type == Unit.UNIT_TYPE_ROBOT:
            cls = Robot
        if unit_type == Unit.UNIT_TYPE_ELEVATOR:
            cls = Elevator
        members_db = session.query(cls).filter(cls.uuid.in_(group_member_list)).all()
        members_db_map = {str(i): i for i in members_db}
        assert len(members_db) == group_member_list
        if group.get("uuid"):
            # 更新
            groups_db = groups_db_map[group["uuid"]]
            groups_db.name = group["name"]
            groups_db.building_floor_uuid = group.get("building_floor_uuid")
            groups_db.members = group_member_list

        else:
            # 新增
            groups_db = _bootstrap_group(
                site_uuid,
                building_uuid,
                group.get("building_floor_uuid"),
                group["name"],
                unit_type,
                0,
                group_member_list
            )

        # update site_facility_unit
        sfus = (
            session.query(SiteFacilityUnit)
            .filter(SiteFacilityUnit.site_uuid == site_uuid)
            .filter(SiteFacilityUnit.facility_uuid.in_(group_member_list))
            .all()
        )
        for sfu in sfus:
            # 很容易忘记修改site facility unit 的group uuid
            sfu.group_uuid = groups_db.uuid

        for member in group["members"]:
            member_db = members_db_map[member["uuid"]]
            member_db.group_uuid = groups_db.uuid
            if cls == Robot:
                members_db.name = member["name"]
            if cls != Elevator:
                # elevator 只修改分组信息
                members_db.name = member["name"]
                members_db.direction = member["direction"]
                members_db.building_uuid = group.get("building_uuid")
                members_db.building_floor_uuid = group.get("building_floor_uuid")
