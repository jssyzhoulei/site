import json
import random
from app.handlers.buildings import (
    session,
    Site,
    Building,
    BuildingFloor,
    Robot,
    Elevator,
    FloorFacility,
    SiteGroup,
    SiteFacilityUnit,
    Unit,
    get_site_building,
    update_site_building,
)
from app.handlers.build_site import force_cleanup_site


class BuildingInfo(object):
    # 修改building info信息
    def __init__(self, building_info: dict, facility_type: int):
        """
        {
        "buildings": [],
        "robot_groups": [],
        "created_at": str(site.create_time),
        "updated_at": str(site.modify_time),
        "version_id": site.version_id,
        "uuid": str(site.uuid),
        "site_uid": site.site_uid,
        }
        """
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
