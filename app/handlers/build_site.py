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
from sqlalchemy import func
from app.models import (
    Site,
    Building,
    BuildingFloor,
    BuildingFloorConnector,
    Elevator,
    ElevatorFloor,
    session,
)

logger = logging.getLogger(__name__)


def _gen_site_uid():
    """
    site uid  全局递增唯一
    """
    max_uid = session.query(func.max(Site.site_uid)).scalar()
    return max_uid + 1 if max_uid else 1


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
        # 羃等 创建时 building_floor_count 为0
        should_extend_floor = building_info - building_floor_count

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
                new_building_floors.append(b_f.uuid)

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
                for idx1 in range(should_extend_floor):
                    # elevator floor 默认名字为- 表示不可达
                    # 由前端更新name时修改 is reachable状态
                    elevator_floor_name = "-"

        building.building_floors = building.building_floors + new_building_floors
        session.flush()


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
    site_uuid: UUID, building_uuid: UUID, elevator_uuid: UUID, name: str, index: int
):
    building_floor = BuildingFloor(
        name=name,
        site_uuid=site_uuid,
        building_uuid=building_uuid,
        elevator_uuid=elevator_uuid,
        floor_index=index,
    )
    session.add(building_floor)
    session.flush()
    return building_floor


def create_site_json_sanity_check(request: dict):
    # check site name 站点名称不允许重复
    pass
