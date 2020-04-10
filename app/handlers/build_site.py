"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

API for bootstrap site, this handle will bootstrap all leaf resources for site.

API

    POST `create_site`

    Request =>
    {
        "business_types": [1],
        "name": "上海大厦",
        "address": "上海市南京路50号",
        "has_building_connector": False,
        "enabled": True,
        "status": 1,
        "location": "",
        "meta_info": {
            "building_count": 1,
            "robot_count": 9,
            "building_info": [{"name": "", "floor_count": 6, "elevator_count": 3,
                               "station_count": 9, "gate_count": 9, "auto_door_count": 9,
                               "charger_count": 9}],
        },
    }

"""
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

logger = logging.getLogger(__name__)


def _gen_site_uid():
    """
    site uid  全局递增唯一
    """
    max_uid = session.query(func.max(Site.site_uid)).scalar() or 0
    return max_uid + 1


def create_site(request: dict):

    # 校验前端数据
    create_site_json_sanity_check(request)
    site = Site(
        name=request["name"],
        site_uid=_gen_site_uid(),
        address=request["address"],
        status=request["status"],
        has_building_connector=request["has_building_connector"],
        business_types=request["business_types"],
        location=request["location"],
        meta_info=request["meta_info"],
        version_id=1,
    )
    session.add(site)
    # flush to get site uuid
    session.flush()
    bootstrap_site(site)

    try:

        session.commit()
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise


def bootstrap_site(site: Site):
    """
    根据统计信息创建楼宇
    此方法幂等
    新增或这个更新都可以调用
    区别为： 更新则会带building uuid
    且不支持删除building 数据
    即第一次创建 floor_count 数量为6 则此后  floor_count数量小于6 则系统忽略
    删除building 数据在其他接口中实现
    "meta_info": {
            "building_count": 1,
            "robot_count": 9,
            "building_info": [{"name": "", "floor_count": 6, "elevator_count": 3,
                               "station_count": 9, "gate_count": 9, "auto_door_count": 9,
                               "charger_count": 9}],
        }
    """
    meta_info = site.meta_info
    assert meta_info["building_count"] == len(meta_info["building_info"])
    _bootstrap_robot(site, meta_info.get("robot_count") or 0)
    for idx, building_info in enumerate(meta_info["building_info"]):
        building = None
        building_uuid = building_info.get("uuid")
        if building_uuid:
            # 更新
            building = session.query(Building).get(building_uuid)
            if building and building_info.get("name"):
                building.name = building_info.get("name")
        if building is None:
            # 创建building
            building = Building(
                name=building_info.get("name") or f"{site.name}#{idx + 1}号楼",
                site_uuid=site.uuid,
            )
            session.add(building)
            session.flush()

        # building 内是否需要扩展楼层
        # 羃等 创建时 building_floor_count 为0  更新时不为0
        should_extend_floor = building_info.get("floor_count") or 0 - len(
            building.building_floors
        )

        new_building_floors = []
        if should_extend_floor > 0:
            for idx in range(should_extend_floor):
                building_floor_name = f"{len(building.building_floors) + idx + 1} 楼"
                b_f = _bootstrap_building_floor(
                    site.uuid,
                    building.uuid,
                    building_floor_name,
                    len(building.building_floors) + idx + 1,
                )
                new_building_floors.append(str(b_f.uuid))

            """
            扩展了floor  同时同步扩展elevator floor  
            elevator floor和 building floor层数相同
            区别是 building floor  每幢楼内只有一个系列
            但是elevator floor是 每个 电梯井内都有  elevator floor
            """
            elevators = (
                session.query(Elevator)
                .filter(Elevator.building_uuid == building.uuid)
                .all()
            )

            for ele in elevators:
                new_ele_floors = []
                for idx1 in range(should_extend_floor):
                    # elevator floor 默认名字为- 表示不可达
                    # 由前端更新name时修改 is reachable状态
                    elevator_floor_name = "-"
                    building_floor_uuid = new_building_floors[idx1]
                    elevator_floor = _bootstrap_elevator_floor(
                        site.uuid,
                        building.uuid,
                        ele.uuid,
                        UUID(building_floor_uuid),
                        elevator_floor_name,
                        len(building.building_floors) + idx1 + 1,
                    )
                    new_ele_floors.append(str(elevator_floor.uuid))

                ele.elevator_floors = ele.elevator_floors + new_ele_floors
                session.flush()

        building.building_floors = building.building_floors + new_building_floors
        session.flush()

        # 是否需要扩展电梯
        should_extend_elevator = building_info.get("elevator_count") or 0 - len(
            building.elevators
        )
        # 新增电梯略复杂  需要创建电梯组  如果此前已经有电梯组  是否新建或沿用旧的电梯组
        # 这里的策略是创建新的电梯组
        if should_extend_elevator > 0:
            # 此前电梯组count
            ele_group_count = (
                session.query(SiteGroup)
                .filter(
                    SiteGroup.building_uuid == building.uuid,
                    SiteGroup.unit_type == Unit.UNIT_TYPE_ELEVATOR,
                )
                .count()
            )
            new_elevators = []
            ele_name = building.name + f"默认电梯组[{ele_group_count+1}]"
            ele_group = _bootstrap_group(
                site.uuid, building.uuid, None, ele_name, Unit.UNIT_TYPE_ELEVATOR, 0
            )
            # building floor count
            # elevator floor count == building floor count
            floor_count = len(building.building_floors)
            for idx2 in range(should_extend_elevator):
                name = f"{building.name}-{ele_name}-{idx2+1}号梯"
                ele = _bootstrap_elevator(
                    site.uuid, building.uuid, ele_group.uuid, "", name
                )
                new_elevators.append(str(ele.uuid))
                # bootstrap elevator floor
                new_ele_floors = []
                for idx3 in range(floor_count):
                    building_floor_uuid = building.building_floors[idx3]
                    elevator_floor = _bootstrap_elevator_floor(
                        site.uuid,
                        building.uuid,
                        ele.uuid,
                        UUID(building_floor_uuid),
                        "-",
                        idx3 + 1,
                    )
                    new_ele_floors.append(str(elevator_floor.uuid))
                ele.elevator_floors = new_ele_floors

            ele_group.members = new_elevators
            building.elevators = building.elevators + new_elevators
            session.flush()

        _bootstrap_floor_facility(site.uuid, building, building_info)
    # 最后创建unit数据
    session.flush()
    _bootstrap_facility_unit(site)
    flush_group_index(site.uuid)


def _bootstrap_building_floor(
    site_uuid: UUID, building_uuid: UUID, name: str, index: int
):
    building_floor = BuildingFloor(
        name=name, site_uuid=site_uuid, building_uuid=building_uuid, floor_index=index
    )
    session.add(building_floor)
    session.flush()
    return building_floor


def _bootstrap_elevator_floor(
    site_uuid: UUID,
    building_uuid: UUID,
    elevator_uuid: UUID,
    building_floor_uuid: UUID,
    name: str,
    index: int,
):
    elevator_floor = ElevatorFloor(
        name=name,
        site_uuid=site_uuid,
        building_uuid=building_uuid,
        building_floor_uuid=building_floor_uuid,
        elevator_uuid=elevator_uuid,
        floor_index=index,
    )
    session.add(elevator_floor)
    session.flush()
    return elevator_floor


def _gen_group_sid(site_uuid: UUID) -> int:
    max_group_sid = (
        session.query(func.max(SiteGroup.facility_group_sid))
        .filter(SiteGroup.site_uuid == site_uuid)
        .scalar()
        or 0
    )
    return max_group_sid + 1


def _bootstrap_group(
    site_uuid: UUID,
    building_uuid: Optional[UUID],
    building_floor_uuid: Optional[UUID],
    name: str,
    unit_type: int,
    facility_group_sid: int,
):
    group = SiteGroup(
        name=name,
        site_uuid=site_uuid,
        building_uuid=building_uuid,
        building_floor_uuid=building_floor_uuid,
        unit_type=unit_type,
        # todo 单元测试要检测同一站点下sid是否会重复
        facility_group_sid=facility_group_sid or _gen_group_sid(site_uuid),
    )
    session.add(group)
    session.flush()
    # 记得更新group的members
    # members存的都是组下facility uuid字符串
    return group


def _bootstrap_elevator(
    site_uuid: UUID, building_uuid: UUID, group_uuid: UUID, brand: str, name: str
):
    elevator = Elevator(
        name=name,
        site_uuid=site_uuid,
        building_uuid=building_uuid,
        group_uuid=group_uuid,
        brand=brand,
    )
    session.add(elevator)
    session.flush()
    return elevator


def _bootstrap_floor_facility(site_uuid: UUID, building: Building, building_info: dict):
    # 创建floor facility
    # elevator robot 以及floor facility 都需要在分组下
    # 因为这三种设备都需要安装iot板子（robot比较特殊）用来和robot近场通讯
    # 这里robot并不是真正的机器人  而是robot的坑位  坑位中以后会绑定机器人
    # 所以此三种facility  放到分组下  并在分组下标识facility的index（类似编号or学号）
    # robot 交互iot设备的时候通过 group sid + facility index 识别通信设备
    # 先创建分组 而后创建分组下的facility
    """
    {"name": "", "floor_count": 6, "elevator_count": 3,
                               "station_count": 9, "gate_count": 9, "auto_door_count": 9,
                               "charger_count": 9}
    """
    station_count = building_info.get("station_count") or 0
    gate_count = building_info.get("gate_count") or 0
    auto_door_count = building_info.get("auto_door_count") or 0
    charger_count = building_info.get("charger_count") or 0

    facility_count_map = {
        Unit.UNIT_TYPE_STATION: station_count,
        Unit.UNIT_TYPE_AUTO_DOOR: auto_door_count,
        Unit.UNIT_TYPE_CHARGER: charger_count,
        Unit.UNIT_TYPE_GATE: gate_count,
    }

    facility_name_map = {
        Unit.UNIT_TYPE_STATION: "station",
        Unit.UNIT_TYPE_AUTO_DOOR: "自动门",
        Unit.UNIT_TYPE_CHARGER: "充电桩",
        Unit.UNIT_TYPE_GATE: "闸机",
    }

    facility_group_sid = _gen_group_sid(site_uuid)
    for facility_type, facility_count in facility_count_map.items():
        facility_count_before = (
            session.query(FloorFacility)
            .filter(
                FloorFacility.building_uuid == building.uuid,
                FloorFacility.unit_type == facility_type,
            )
            .count()
            or 0
        )
        should_extend_facility = facility_count - facility_count_before
        if should_extend_facility > 0:
            facility_group_count = (
                session.query(SiteGroup)
                .filter(
                    SiteGroup.building_uuid == building.uuid,
                    SiteGroup.unit_type == facility_type,
                )
                .count()
                or 0
            )
            group_name = f"{building.name}(默认){facility_name_map[facility_type]}组：[{facility_group_count + 1}]"
            new_facilities = []

            facility_group = _bootstrap_group(
                site_uuid,
                building.uuid,
                None,
                group_name,
                facility_type,
                facility_group_sid,
            )
            session.add(facility_group)
            session.flush()
            facility_group_sid += 1
            for idx in range(should_extend_facility):
                facility_name = (
                    f"{group_name}#{facility_name_map[facility_type]}{idx+1}号"
                )
                facility = _new_floor_facility(
                    site_uuid,
                    building.uuid,
                    facility_group.uuid,
                    facility_type,
                    facility_name,
                )
                session.add(facility)
                session.flush()
                new_facilities.append(str(facility.uuid))

            facility_group.members = new_facilities
            if facility_type == Unit.UNIT_TYPE_CHARGER:
                building.chargers = building.chargers + new_facilities
            elif facility_type == Unit.UNIT_TYPE_AUTO_DOOR:
                building.auto_doors = building.auto_doors + new_facilities
            elif facility_type == Unit.UNIT_TYPE_STATION:
                building.stations = building.stations + new_facilities
            else:
                # 注意此处没有判断type  直接使用了else  如果以后新增 facility类型  需要修改
                building.gates = building.gates + new_facilities
            session.flush()

    return


def _bootstrap_robot(site: Site, robot_count: int):

    robot_count_before = (
        session.query(Robot).filter(Robot.site_uuid == site.uuid).count() or 0
    )
    should_extend_robot = robot_count - robot_count_before
    if should_extend_robot > 0:
        facility_group_count = (
            session.query(SiteGroup)
            .filter(
                SiteGroup.site_uuid == site.uuid,
                SiteGroup.unit_type == Unit.UNIT_TYPE_ROBOT,
            )
            .count()
            or 0
        )
        group_name = f"{site.name}(默认)机器人组：[{facility_group_count + 1}]"
        new_facilities = []

        facility_group = _bootstrap_group(
            site.uuid, None, None, group_name, Unit.UNIT_TYPE_ROBOT, 0
        )
        session.add(facility_group)
        session.flush()
        for idx in range(should_extend_robot):
            facility_name = f"{group_name}#robot{idx+1}号"
            robot = _new_robot(site.uuid, facility_group.uuid, facility_name)
            session.add(robot)
            session.flush()
            new_facilities.append(str(robot.uuid))

        facility_group.members = new_facilities

        session.flush()

    return


def _new_floor_facility(
    site_uuid: UUID, building_uuid: UUID, group_uuid: UUID, unit_type: int, name: str
):
    facility = FloorFacility(
        name=name,
        site_uuid=site_uuid,
        building_uuid=building_uuid,
        group_uuid=group_uuid,
        unit_type=unit_type,
    )
    session.add(facility)
    session.flush()
    return facility


def _new_robot(site_uuid: UUID, group_uuid: UUID, name: str):
    robot = Robot(name=name, site_uuid=site_uuid, group_uuid=group_uuid)
    session.add(robot)
    session.flush()
    return robot


def _bootstrap_facility_unit(site: Site):
    """
    创建facility绑定关系
    site facility unit 记录各个坑位（机器人、elevator、facility）内的设备是否就位（绑定or进坑）
    生成site数据的时候默认生成facility绑定数据
    只是此时尚未绑定iot、robot等设备
    即每一行的unit uid、  unit uuid、 unit name为空
    unit表内同时记录着各种facility的sid  所有facility（在三张表内floor_facility、elevator、robot）
    同时也记录每个facility在组内的index（从1开始计数）
    """
    # 创建电梯绑定关系
    site_uuid = site.uuid
    site_uid = site.site_uid
    facility_sid = _gen_facility_sid(site_uuid)

    current_sfus = (
        session.query(SiteFacilityUnit.facility_uuid)
        .filter(SiteFacilityUnit.site_uuid == site_uuid)
        .all()
    )
    current_sfus = [i[0] for i in current_sfus]
    elevators = (
        session.query(Elevator)
        .filter(Elevator.site_uuid == site_uuid, Elevator.uuid.notin_(current_sfus))
        .all()
    )
    # todo 后续优化批量新增 bulk_insert_mappings
    for ele in elevators:
        new_facility_unit(
            site_uuid,
            site_uid,
            ele.group_uuid,
            ele.uuid,
            Unit.UNIT_TYPE_ELEVATOR,
            facility_sid,
        )
        facility_sid += 1

    # robot绑定关系
    robots = (
        session.query(Robot)
        .filter(Robot.site_uuid == site_uuid, Robot.uuid.notin_(current_sfus))
        .all()
    )
    for r in robots:
        new_facility_unit(
            site_uuid,
            site_uid,
            r.group_uuid,
            r.uuid,
            Unit.UNIT_TYPE_ROBOT,
            facility_sid,
        )
        facility_sid += 1

    facilities = (
        session.query(FloorFacility)
        .filter(
            FloorFacility.site_uuid == site_uuid,
            FloorFacility.uuid.notin_(current_sfus),
        )
        .all()
    )
    for f in facilities:
        new_facility_unit(
            site_uuid, site_uid, f.group_uuid, f.uuid, f.unit_type, facility_sid
        )
        facility_sid += 1


def _gen_facility_sid(site_uuid: UUID):
    max_facility_sid = (
        session.query(func.max(SiteFacilityUnit.facility_sid))
        .filter(SiteFacilityUnit.site_uuid == site_uuid)
        .scalar()
        or 0
    )
    return max_facility_sid + 1


def new_facility_unit(
    site_uuid: UUID,
    site_uid: int,
    group_uuid: UUID,
    facility_uuid: UUID,
    unit_type: int,
    facility_sid: int,
):
    sfu = SiteFacilityUnit(
        site_uid=site_uid,
        site_uuid=site_uuid,
        facility_uuid=facility_uuid,
        unit_type=unit_type,
        facility_sid=facility_sid or _gen_facility_sid(site_uuid),
        group_uuid=group_uuid,
    )
    session.add(sfu)
    session.flush()
    return sfu


# 刷新facility unit group index
def flush_group_index(site_uuid: UUID):
    # 每次新增或更新facility unit的时候 都要重新更新组内的index编号（编号顺序没有要求）
    group_uuid_site_unit_dict = {}
    sfus = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.site_uuid == site_uuid)
        .all()
    )
    for sfu in sfus:
        if str(sfu.group_uuid) in group_uuid_site_unit_dict:
            group_uuid_site_unit_dict[str(sfu.group_uuid)].append(sfu)
        else:
            group_uuid_site_unit_dict[str(sfu.group_uuid)] = [sfu]

    for _, group_site_info in group_uuid_site_unit_dict.items():
        for i, sfu in enumerate(group_site_info):
            sfu.facility_group_index = i + 1

    session.flush()


def force_cleanup_site(site_uuid: UUID) -> None:
    logger.warning(f"delete site related rows for site_uuid={str(site_uuid)}")

    session.query(Site).filter(Site.uuid == site_uuid).delete(synchronize_session=False)
    session.query(Building).filter(Building.site_uuid == site_uuid).delete(
        synchronize_session=False
    )
    session.query(BuildingFloor).filter(BuildingFloor.site_uuid == site_uuid).delete(
        synchronize_session=False
    )
    session.query(BuildingFloorConnector).filter(
        BuildingFloor.site_uuid == site_uuid
    ).delete(synchronize_session=False)
    session.query(FloorFacility).filter(FloorFacility.site_uuid == site_uuid).delete(
        synchronize_session=False
    )

    session.query(Elevator).filter(Elevator.site_uuid == site_uuid).delete(
        synchronize_session=False
    )
    session.query(ElevatorFloor).filter(ElevatorFloor.site_uuid == site_uuid).delete(
        synchronize_session=False
    )
    session.query(SiteGroup).filter(SiteGroup.site_uuid == site_uuid).delete(
        synchronize_session=False
    )
    session.query(SiteFacilityUnit).filter(
        SiteFacilityUnit.site_uuid == site_uuid
    ).delete(synchronize_session=False)
    session.query(Robot).filter(Robot.site_uuid == site_uuid).delete(
        synchronize_session=False
    )

    try:
        session.commit()
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise


def create_site_json_sanity_check(request: dict):
    # check site name 站点名称不允许重复
    pass
