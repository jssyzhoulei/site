"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
handlers 目录下bind facility测试函数
"""

import json
from uuid import UUID
from app.handlers.build_site import (
    session,
    Site,
    Building,
    BuildingFloor,
    Cmdb,
    Robot,
    Elevator,
    FloorFacility,
    SiteGroup,
    SiteFacilityUnit,
    Unit,
    force_cleanup_site,
)
from app.handlers.buildings import get_site_building, update_site_building
from app.handlers.facility_bind import (
    get_unit_list,
    update_bind_facility,
    get_unbind_unit,
)


from manage import make_shell_ctx

make_shell_ctx()


def test_bind_unbind_unit(connect_site, fake_site):
    units = get_unbind_unit(Unit.UNIT_TYPE_ROBOT)
    robots = session.query(Robot).filter(Robot.site_uuid == fake_site.uuid).all()
    robot_1, robot_2 = robots[0], robots[1]
    unit_robot_1 = units[0]

    bind_req = {
        "facility_uuid": str(robot_1.uuid),
        "unit_type": Unit.UNIT_TYPE_ROBOT,
        "unit_uuid": str(unit_robot_1["unit_uuid"]),
    }
    update_bind_facility(fake_site.uuid, [bind_req], Unit.UNIT_TYPE_ROBOT)
    cmdb = session.query(Cmdb).filter(Cmdb.facility_uuid == robot_1.uuid).scalar()
    # 验证数据已经绑定
    assert cmdb.site_uuid is not None

    # 重复绑定同一台设备需要报错
    try:
        bind_req2 = {
            "facility_uuid": str(robot_2.uuid),
            "unit_type": Unit.UNIT_TYPE_ROBOT,
            "unit_uuid": str(unit_robot_1["unit_uuid"]),
        }
        update_bind_facility(
            fake_site.uuid, [bind_req2, bind_req], Unit.UNIT_TYPE_ROBOT
        )
        assert False
    except Exception as e:
        assert AssertionError != e, "重复绑定没有报错"

    # 测试解绑
    unbind_req = {
        "facility_uuid": str(robot_1.uuid),
        "unit_type": Unit.UNIT_TYPE_ROBOT,
        "unit_uuid": "",
    }
    update_bind_facility(fake_site.uuid, [unbind_req], Unit.UNIT_TYPE_ROBOT)
    sfu = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.facility_uuid == robot_1.uuid)
        .scalar()
    )
    assert sfu.unit_uuid is None


def test_repeat_facility(connect_site, fake_site):
    # 同building下的facility绑定后会再获取到 不同building获取不到此facility
    building_info = get_site_building(fake_site.uuid)
    building_1 = building_info["buildings"][0]
    building_2 = building_info["buildings"][1]
    building_1_charger = building_1["charger_groups"][0]["members"][0]["uuid"]

    chargers = get_unit_list(
        Unit.UNIT_TYPE_CHARGER, fake_site.uuid, UUID(building_1["uuid"])
    )
    facility_uuid = chargers[0]["unit_uuid"]

    bind_req = {
        "facility_uuid": building_1_charger,
        "unit_type": Unit.UNIT_TYPE_ROBOT,
        "unit_uuid": facility_uuid,
    }
    update_bind_facility(fake_site.uuid, [bind_req], Unit.UNIT_TYPE_ROBOT)

    chargers2 = get_unit_list(
        Unit.UNIT_TYPE_CHARGER, fake_site.uuid, UUID(building_1["uuid"])
    )
    assert chargers[0] in chargers2

    chargers3 = get_unit_list(
        Unit.UNIT_TYPE_CHARGER, fake_site.uuid, UUID(building_2["uuid"])
    )
    # building2 无法获取到被绑定的charger  但是building1可以可以获取
    assert chargers[0] not in chargers3


# 新版更换绑定
def test_change_bind_unit(connect_site, fake_site):

    robots = session.query(Robot).filter(Robot.site_uuid == fake_site.uuid).all()
    robot_1, robot_2 = robots[0], robots[1]

    available_units = get_unit_list(Unit.UNIT_TYPE_ROBOT, fake_site.uuid)

    # 首次绑定两个
    bind_req_list = [
        {
            "facility_uuid": str(robot_1.uuid),
            "unit_type": Unit.UNIT_TYPE_ROBOT,
            "unit_uuid": str(available_units[0]["unit_uuid"]),
        },
        {
            "facility_uuid": str(robot_2.uuid),
            "unit_type": Unit.UNIT_TYPE_ROBOT,
            "unit_uuid": str(available_units[1]["unit_uuid"]),
        },
    ]
    update_bind_facility(fake_site.uuid, bind_req_list, Unit.UNIT_TYPE_ROBOT)

    sfus = (
        session
        .query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.facility_uuid.in_([robot_1.uuid, robot_2.uuid]))
        .all()
    )
    sfu_dict = {i.facility_uuid: i for i in sfus}

    assert str(sfu_dict[robot_1.uuid].unit_uuid) == available_units[0]["unit_uuid"]
    assert str(sfu_dict[robot_2.uuid].unit_uuid) == available_units[1]["unit_uuid"]

    # 更换绑定关系
    bind_req_list2 = [
        {
            "facility_uuid": str(robot_1.uuid),
            "unit_type": Unit.UNIT_TYPE_ROBOT,
            "unit_uuid": str(available_units[1]["unit_uuid"]),
        },
        {
            "facility_uuid": str(robot_2.uuid),
            "unit_type": Unit.UNIT_TYPE_ROBOT,
            "unit_uuid": str(available_units[0]["unit_uuid"]),
        },
    ]
    update_bind_facility(fake_site.uuid, bind_req_list2, Unit.UNIT_TYPE_ROBOT)

    session.expire_all()
    sfus2 = (
        session
        .query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.facility_uuid.in_([robot_2.uuid, robot_1.uuid]))
        .all()
    )
    sfu_dict2 = {i.facility_uuid: i for i in sfus2}

    assert str(sfu_dict2[robot_1.uuid].unit_uuid) == available_units[1]["unit_uuid"]
    assert str(sfu_dict2[robot_2.uuid].unit_uuid) == available_units[0]["unit_uuid"]
