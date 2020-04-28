import json
import random
import uuid
from app.handlers.buildings import (
    session,
    Site,
    Building,
    BuildingFloor,
    BuildingFloorConnector,
    Robot,
    Elevator,
    ElevatorFloor,
    FloorFacility,
    SiteGroup,
    SiteFacilityUnit,
    Unit,
    get_site_building,
    update_site_building,
)
from app.handlers.build_site import force_cleanup_site, update_site


class BuildingInfo(object):
    # 修改building info信息
    def __init__(self, building_info: dict, facility_type: int):
        self.building_info = building_info
        self.facility_type = facility_type

    def get_facility_name(self):
        facility_map = {
            Unit.UNIT_TYPE_ROBOT: "robot_groups",
            Unit.UNIT_TYPE_ELEVATOR: "elevator_groups",
            Unit.UNIT_TYPE_STATION: "station_groups",
            Unit.UNIT_TYPE_GATE: "gate_groups",
            Unit.UNIT_TYPE_AUTO_DOOR: "auto_door_groups",
            Unit.UNIT_TYPE_CHARGER: "charger_groups",
        }
        return facility_map.get(self.facility_type)

    @property
    def groups(self):
        return self.building_info[self.get_facility_name()]

    def new_group(self, building_floor_uuid: str = ""):
        # 创建一个新组
        new_group = {
            "name": f"{self.get_facility_name()}-{len(self.groups)+1}",
            "unit_type": self.facility_type,
            "members": [],
            "building_uuid": self.building_info["uuid"],
        }
        if building_floor_uuid:
            new_group["building_floor_uuid"] = building_floor_uuid
        return new_group

    def add_group(self, group: dict):
        # 添加新建的组
        self.groups.append(group)

    def remove_group(self, group_index=None):
        # 从building info 移除并返回group
        if group_index:
            group = self.groups[group_index]
            del self.groups[group_index]
            return group
        else:
            return self.groups.pop()

    def add_group_member(self, group_index: int, member: dict):
        # 添加组成员
        self.groups[group_index]["members"].append(member)

    def remove_group_member(self, group_index: int, member_index: int):
        # 移除组的某个member
        member = self.groups[group_index]["members"][member_index]
        del self.groups[group_index]["members"][member_index]
        return member

    def move_group_member(
        self, from_group_index: int, to_group_index: int, member_index: int
    ):
        # 把组成员从一个组移动到另一个组
        member = self.remove_group_member(from_group_index, member_index)
        self.add_group_member(to_group_index, member)


def test_update(connect_site):
    site = session.query(Site).first()
    buildings_info = get_site_building(site.uuid)
    update_site_building(site.uuid, buildings_info)


def test_update_section_building_group_uid_check(connect_site):
    """
    flush 之后每个site_facility_unit 都应该有group uuid
    """
    site = session.query(Site).first()

    new_section_building = get_site_building(site.uuid)
    update_site_building(site.uuid, new_section_building)

    # flush 之后每个site_facility_unit 都应该有group uuid
    sfus = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.site_uuid == site.uuid)
        .all()
    )
    for sfu in sfus:
        assert sfu.group_uuid is not None


def test_update_section_building_name(connect_site):
    """
    测试更新 building section 的名字
        * 测试更改 building_floor 的名称
        * 测试更改 elevator_floor 的名称
        * 测试更改 robot 的名称
    """

    building_floor_name = "XXX FLOOR"
    elevator_floor_name = "YYY FLOOR"
    sg_robot_name = "XXX ROBOT"

    site = session.query(Site).first()

    site_info = get_site_building(site.uuid)
    site_info["buildings"][0]["building_floors"][0]["name"] = building_floor_name
    site_info["buildings"][0]["elevators"][0]["elevator_floors"][0][
        "name"
    ] = elevator_floor_name
    site_info["robot_groups"][0]["name"] = sg_robot_name

    update_site_building(site.uuid, site_info)

    building_floor = (
        session.query(BuildingFloor)
        .filter(
            BuildingFloor.uuid
            == uuid.UUID(site_info["buildings"][0]["building_floors"][0]["uuid"])
        )
        .first()
    )
    assert building_floor.name == building_floor_name

    elevator_floor = ElevatorFloor.get_by_uuid(
        uuid.UUID(
            site_info["buildings"][0]["elevators"][0]["elevator_floors"][0]["uuid"]
        )
    )
    assert elevator_floor and elevator_floor.name == elevator_floor_name

    sg = SiteGroup.get_by_uuid(uuid.UUID(site_info["robot_groups"][0]["uuid"]))
    assert sg.name == sg_robot_name


def test_update_section_building_unknown_uuid(connect_site):
    """
    测试传入不存在的 uuid，报错
    """

    site = session.query(Site).first()
    site_info = get_site_building(site.uuid)
    site_info["buildings"][0]["uuid"] = str(uuid.uuid4())

    try:
        update_site_building(site.uuid, site_info)

    except:
        return
    assert False, "传入不存在的 uuid, 没有报错！"


def new_robot_group():
    return {
        "name": f"robot_groups-{random.randint(100, 200)}",
        "unit_type": Unit.UNIT_TYPE_ROBOT,
        "members": [],
    }


def test_update_robot_site_group_1(connect_site):
    """
    测试修改机器人组

    1. 新增 group 但是 members 总数量不全, 报错
    """
    site = session.query(Site).first()
    site_info = get_site_building(site.uuid)
    groups = site_info["robot_groups"]
    new_group = new_robot_group()
    groups.append(new_group)
    member = groups[0]["members"].pop()
    new_group["members"].append(member)
    groups[0]["members"].pop()

    try:
        update_site_building(site.uuid, site_info)
    except:
        return

    assert False, "members 数量缺失，没有报错！"


def test_update_robot_site_group_2(connect_site):
    """
    测试修改机器人组

    2. 新增 group 但是新的 groups 里面没有 members，不持久化新的 group。
    """
    site = session.query(Site).first()
    site_info = get_site_building(site.uuid)

    empty_group = new_robot_group()
    site_info["robot_groups"].append(empty_group)

    try:
        update_site_building(site.uuid, site_info)

    except:
        return
    assert False, "新增空 group，没有报错！"


def test_update_robot_site_group_3(connect_site, fake_site):
    """
    测试修改机器人组

    4. 新增 group 并且移动全部 member 到新的 group，正常完成。老的 group 所有属性不变。
    """
    site_info = get_site_building(fake_site.uuid)
    groups = site_info["robot_groups"]
    new_group = new_robot_group()
    groups.append(new_group)
    # 机器人组有三个member
    for _ in range(3):
        member = groups[0]["members"].pop()
        new_group["members"].append(member)

    sg_before = SiteGroup.get_by_uuid(site_info["robot_groups"][0]["uuid"])
    update_site_building(fake_site.uuid, site_info)
    res_info = get_site_building(fake_site.uuid)
    assert res_info["robot_groups"][0]["name"] == site_info["robot_groups"][0]["name"]
    assert res_info["robot_groups"][0]["uuid"] == site_info["robot_groups"][0]["uuid"]

    sg_after = SiteGroup.get_by_uuid(res_info["robot_groups"][0]["uuid"])
    assert sg_after.facility_group_sid == sg_before.facility_group_sid


def test_update_robot_site_group_4(connect_site, fake_site):
    """
    测试修改机器人组

    5. 给 robot_group 传入 building uuid 字段，报错。
    """
    site_info = get_site_building(fake_site.uuid)
    groups = site_info["robot_groups"]
    groups[0]["building_uuid"] = site_info["buildings"][0]["uuid"]

    # TODO Add detection
    try:
        update_site_building(uuid.UUID(site_info["uuid"]), site_info)
        assert False, "robot_group 传入 building uuid 字段，没有报错！"
    except:
        pass


def test_update_robot_site_group_7(connect_site, fake_site):
    """
    测试修改机器人组

    7. 给 robot_group 传入随机新的 member uuid，报错。
    """
    site_info = get_site_building(fake_site.uuid)
    groups = site_info["robot_groups"]
    groups[0]["members"][0] = {"uuid": str(uuid.uuid4())}

    try:
        update_site_building(fake_site.uuid, site_info)

    except Exception:
        return
    assert False, "robot_group 传入随机新的 member uuid，没有报错！"


def test_update_elevator_site_group_1(
    connect_site, fake_site
):
    """
    测试修改电梯组

    1. 新增 group 但是 members 总数量不全, 报错
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)
    new_group = building.new_group()
    building.add_group(new_group)
    building.move_group_member(0, 1, 0)
    building.remove_group_member(1, 0)

    try:
        update_site_building(fake_site.uuid, site_info)
        res_info = get_site_building(fake_site.uuid)
        res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)

    except Exception:
        return
    assert False, (
        f"前后member数量不一致，应该报错！\n"
        f"请求: {json.dumps(res_building.groups)}\n"
        f"响应: {json.dumps(building.groups)}\n"
    )


def test_update_elevator_site_group_3(
        connect_site, fake_site
):
    """
    测试修改电梯组

    3. 新增 group 并且移动部分 member 到新的 group，正常完成。老的 group 所有属性不变。
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)
    new_group = building.new_group()
    building.add_group(new_group)
    building.move_group_member(0, 1, 0)

    update_site_building(fake_site.uuid, site_info)
    res_info = get_site_building(fake_site.uuid)
    res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)
    assert building.groups[0] == res_building.groups[0]


def test_update_elevator_site_group_4(
    connect_site, fake_site
):
    """
    测试修改电梯组

    4. 新增 group 并且移动全部 member 到新的 group，正常完成。老的 group 所有属性不变。
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)
    new_group = building.new_group()
    building.add_group(new_group)
    # 3 个 elevator 全部移动到新的group
    for _ in range(3):
        building.move_group_member(0, 1, 0)

    update_site_building(fake_site.uuid, site_info)
    res_info = get_site_building(fake_site.uuid)
    res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)
    assert building.groups[0] == res_building.groups[0]


def test_update_elevator_site_group_7(
        connect_site, fake_site
):
    """
    测试修改电梯组

    7. 给 elevator_group 传入随机新的 member uuid，报错。
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)
    building.add_group_member(0, {"uuid": str(uuid.uuid4()), "name": "test随机电梯"})
    try:
        update_site_building(fake_site.uuid, site_info)
        res_info = get_site_building(fake_site.uuid)
        res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_ELEVATOR)
    except Exception:
        return
    assert False, (
        f"传入随机新的 member uuid，没有报错！\n"
        f"请求: {json.dumps(res_building.groups[0])}\n"
        f"响应: {json.dumps(building.groups[0])}\n"
    )


def test_update_floor_facility_site_group_1(
    connect_site, fake_site
):
    """
    测试修改楼层设施组

    1. 新增 group 但是 members 总数量不全, 报错
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_GATE)
    new_group = building.new_group()
    building.add_group(new_group)
    building.move_group_member(0, 1, 0)
    building.remove_group_member(1, 0)

    try:
        update_site_building(fake_site.uuid, site_info)
        res_info = get_site_building(fake_site.uuid)
        res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_GATE)

    except Exception:
        return
    assert False, (
        f"前后member数量不一致，应该报错！\n"
        f"请求: {json.dumps(res_building.groups)}\n"
        f"响应: {json.dumps(building.groups)}\n"
    )


def test_update_floor_facility_site_group_2(
    connect_site, fake_site
):
    """
    测试修改楼层设施组

    2. 新增 group 但是新的 groups 里面没有 members，不持久化新的 group。
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_CHARGER)
    new_group = building.new_group()
    building.add_group(new_group)
    try:
        res_info = update_site_building(fake_site.uuid, site_info)
        res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_CHARGER)

    except Exception:
        return
    assert False, (
        f"新增空group，没有报错！\n"
        f"请求: {json.dumps(res_building.groups)}\n"
        f"响应: {json.dumps(building.groups)}\n"
    )


def test_update_floor_facility_site_group_3(
    connect_site, fake_site
):
    """
    测试修改楼层设施组

    3. 新增 group 并且移动全部 member 到新的 group，正常完成。老的 group 所有属性不变。新的 group 的 building / floor 属性匹配
    """
    site_info = get_site_building(fake_site.uuid)
    first_floor = site_info["buildings"][0]["building_floors"][0]["uuid"]

    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_AUTO_DOOR)
    new_group = building.new_group(building_floor_uuid=first_floor)
    building.add_group(new_group)
    # 3 个 auto door 全部移动到新的group
    for _ in range(3):
        building.move_group_member(0, 1, 0)

    update_site_building(fake_site.uuid, site_info)
    res_info = get_site_building(fake_site.uuid)
    res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_AUTO_DOOR)
    assert building.groups[0] == res_building.groups[0]


def test_update_floor_facility_site_group_4(
    connect_site, fake_site
):
    """
    测试修改楼层设施组

    4. 新增 group 并且移动部分 member 到新的 group，正常完成。老的 group 所有属性不变。新的 group 的 building / floor 属性匹配
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_STATION)
    new_group = building.new_group()
    building.add_group(new_group)
    building.move_group_member(0, 1, 0)

    update_site_building(fake_site.uuid, site_info)
    res_info = get_site_building(fake_site.uuid)
    res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_STATION)
    assert building.groups[0] == res_building.groups[0]


def test_update_floor_facility_site_group_5(
    connect_site, fake_site
):
    """
    测试修改楼层设施组

    4. 在 2 个 group 之间部分移动 member，正常完成。2 个 group 所有属性包括 building/floor/sid 均不变。
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_CHARGER)
    new_group = building.new_group()
    building.add_group(new_group)
    building.move_group_member(0, 1, 0)
    building.move_group_member(0, 1, 0)
    update_site_building(fake_site.uuid, site_info)
    res_info = get_site_building(fake_site.uuid)
    res_building = BuildingInfo(res_info["buildings"][0], Unit.UNIT_TYPE_CHARGER)
    assert building.groups[0] == res_building.groups[0]


def test_update_floor_facility_floor_1(
    connect_site, fake_site
):
    """
    测试修改楼层设施组的楼层

    1. 修改楼层设施组到新的楼层，正常完成。group 的属性全部不变。members 的楼层全部发生对应变化。
    """

    meta_info = fake_site.meta_info
    meta_info["building_info"][0]["floor_count"] += 1

    update_site({
        "uuid": fake_site.uuid,
        "name": fake_site.name,
        "address": fake_site.address,
        "status": fake_site.status,
        "has_building_connector": fake_site.has_building_connector,
        "business_types": fake_site.business_types,
        "location": fake_site.location,
        "meta_info": meta_info,
    })

    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_CHARGER)
    floor_uuid = building.building_info["building_floors"][-1]["uuid"]
    building.groups[0]["building_floor_uuid"] = floor_uuid
    update_site_building(fake_site.uuid, site_info)
    section_building = get_site_building(fake_site.uuid)

    res_building = BuildingInfo(section_building["buildings"][0], Unit.UNIT_TYPE_CHARGER)
    for member in res_building.groups[0]["members"]:
        assert (
            str(FloorFacility.get_by_uuid(member["uuid"]).building_floor_uuid)
            == floor_uuid
        ), "修改楼层设施组到新的楼层后， 组内member的楼层没跟着变！"


def test_update_floor_facility_floor_2(
    connect_site, fake_site
):
    """
    测试修改楼层设施组的楼层

    2. 修改楼层设施组到不存在的楼层，报错。
    """
    site_info = get_site_building(fake_site.uuid)
    building = BuildingInfo(site_info["buildings"][0], Unit.UNIT_TYPE_CHARGER)
    building.groups[0]["building_floor_uuid"] = str(uuid.uuid4())

    try:
        update_site_building(fake_site.uuid, site_info)
    except Exception:
        return

    assert False, "修改楼层设施组到不存在的楼层, 没有报错"


def test_update_site_group_building_floor_uuid(
    connect_site, fake_site
):
    """
    测试组以及组members添加  building_floor_uuid
    以及 building_floor_uuid 不对齐情况
    """
    site_info = get_site_building(fake_site.uuid)
    building_1_floor_uuid = site_info["buildings"][0]["building_floors"][0]["uuid"]
    site_info["buildings"][1]["charger_groups"][0][
        "building_floor_uuid"
    ] = building_1_floor_uuid

    for member in site_info["buildings"][1]["charger_groups"][0]["members"]:
        member["building_floor_uuid"] = building_1_floor_uuid
    building_2_uuid = site_info["buildings"][1]["uuid"]

    update_site_building(fake_site.uuid, site_info)
    chargers = (
        session
        .query(FloorFacility)
        .filter(FloorFacility.building_uuid == building_2_uuid)
        .filter(FloorFacility.building_floor_uuid == building_1_floor_uuid)
        .filter(FloorFacility.unit_type == Unit.UNIT_TYPE_CHARGER)
        .all()
    )
    chargers_raw_count = len(site_info["buildings"][1]["charger_groups"][0]["members"])
    # 关联building floor的数量保持对齐
    assert chargers_raw_count == len(chargers)


def test_connect_floor(
    connect_site, fake_site
):
    """
    测试楼层关联取关逻辑
    """
    site_info = get_site_building(fake_site.uuid)
    building_1_floor_list = site_info["buildings"][0]["building_floors"]
    building_2_floor_list = site_info["buildings"][1]["building_floors"]
    building_1_floor_1 = building_1_floor_list[0]
    building_1_floor_2 = building_1_floor_list[1]
    building_2_floor_1 = building_2_floor_list[0]

    # 绑定同一栋building floor
    building_1_floor_1["connected_building_floor_uuid"] = building_1_floor_2["uuid"]
    site_info["buildings"][0]["building_floors"][0] = building_1_floor_1
    try:
        update_site_building(fake_site.uuid, site_info)
        assert False, "联通同一栋building未报错"
    except Exception as e:
        assert AssertionError != e

    # 绑定不同building
    building_1_floor_1["connected_building_floor_uuid"] = building_2_floor_1["uuid"]
    site_info["buildings"][0]["building_floors"][0] = building_1_floor_1
    update_site_building(fake_site.uuid, site_info)

    building_1_floor_1_uuid = building_1_floor_1["uuid"]
    building_2_floor_1_uuid = building_1_floor_1["connected_building_floor_uuid"]
    exist = (
        session
        .query(BuildingFloorConnector)
        .filter(BuildingFloorConnector.floor_uuid_1 == building_1_floor_1_uuid)
        .filter(BuildingFloorConnector.floor_uuid_2 == building_2_floor_1_uuid)
        .filter(BuildingFloorConnector.is_delete == 0)
        .all()
    )
    assert exist != []


# 一些边界测试
def test_get_section_building(connect_site, fake_site):

    # 返回数据按照create at排序
    meta_info = fake_site.meta_info
    meta_info["building_info"].append(
        {
            "name": "楼宇 3",
            "floor_count": 7,
            "elevator_count": 1,
            "gate_count": 1,
            "charger_count": 2,
            "station_count": 1,
            "auto_door_count": 3,
        }
    )
    meta_info["building_count"] = 3
    update_site({
        "uuid": fake_site.uuid,
        "name": fake_site.name,
        "address": fake_site.address,
        "status": fake_site.status,
        "has_building_connector": fake_site.has_building_connector,
        "business_types": fake_site.business_types,
        "location": fake_site.location,
        "meta_info": meta_info,
    })

    building_info = get_site_building(fake_site.uuid)
    building3 = building_info["buildings"][2]
    assert building3["name"] == "楼宇 3"