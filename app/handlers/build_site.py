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
    SiteGroup,
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
    for idx, building_info in enumerate(meta_info["building_info"]):
        building = None
        building_uuid = building_info.get("uuid")
        if building_uuid:
            # 更新
            building = session.query(Building).get(building_uuid)
        if building is None:
            # 创建building
            building = Building(
                name=building_info.get("name") or site.name + f"{idx + 1}号楼",
                address=building_info.get("address"),
            )
            session.add(building)
            session.flush()

        building_floor_count = (
            session.query(BuildingFloor)
            .filter(BuildingFloor.building_uuid == building.uuid)
            .count()
        )
        # building 内是否需要扩展楼层
        # 羃等 创建时 building_floor_count 为0  更新时不为0
        should_extend_floor = (
            building_info.get("floor_count") or 0 - building_floor_count
        )

        new_building_floors = []
        if should_extend_floor > 0:
            for idx1 in range(should_extend_floor):
                building_floor_name = f"{building_floor_count + idx1 + 1} 楼"
                b_f = _bootstrap_building_floor(
                    site.uuid,
                    building.uuid,
                    building_floor_name,
                    building_floor_count + idx1 + 1,
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
                        building_floor_count + idx1 + 1,
                    )
                    new_ele_floors.append(str(elevator_floor.uuid))

                ele.elevator_floors = ele.elevator_floors + new_ele_floors
                session.flush()

        building.building_floors = building.building_floors + new_building_floors
        session.flush()

        elevator_count = (
            session.query(Elevator)
            .filter(Elevator.building_uuid == building.uuid)
            .count()
        )
        # 是否需要扩展电梯
        should_extend_elevator = building_info.get("floor_count") or 0 - elevator_count
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
                name = f"{idx2+1}号梯"
                ele = _bootstrap_elevator(
                    site.uuid, building.uuid, ele_group.uuid, "", name
                )
                new_elevators.append(str(ele.uuid))
                # bootstrap elevator floor
                for idx3 in range(floor_count):
                    pass

            ele_group.members = new_elevators


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


def create_site_json_sanity_check(request: dict):
    # check site name 站点名称不允许重复
    pass
