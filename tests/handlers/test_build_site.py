import json
from app.handlers.build_site import (
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
    force_cleanup_site,
)


def test_create_site(client):
    rsp = client.post(
        "/site",
        data=json.dumps(
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
                    "robot_count": 3,
                    "building_info": [
                        {
                            "name": "",
                            "floor_count": 6,
                            "elevator_count": 3,
                            "station_count": 1,
                            "gate_count": 5,
                            "auto_door_count": 3,
                            "charger_count": 2,
                        }
                    ],
                },
            }
        ),
        content_type="application/json",
        charset="UTF-8",
    )
    assert rsp.get_json() == {"msg": "success"}

    site = client.get("/sites?name=上海大厦")
    site_info = site.get_json()
    parse_site(site_info[0])
    force_cleanup_site(site_info[0]["uuid"])


def parse_site(site: dict):

    site_uuid = site["uuid"]
    meta_info = site["meta_info"]
    building_info = meta_info["building_info"]

    buildings = session.query(Building).filter(Building.site_uuid == site_uuid).all()
    assert len(buildings) == len(building_info)
    building = buildings[0]
    assert building.name == building_info[0]["name"] == "上海大厦#1号楼"

    building_floors = building.building_floors
    building_floors_db = (
        session.query(BuildingFloor)
        .filter(BuildingFloor.building_uuid == building.uuid)
        .all()
    )

    assert (
        len(building_floors)
        == building_info[0]["floor_count"]
        == len(building_floors_db)
    )

    elevators = building.elevators
    elevators_db = (
        session.query(Elevator).filter(Elevator.building_uuid == building.uuid).all()
    )

    assert len(elevators_db) == building_info[0]["elevator_count"] == len(elevators)

    stations = building.stations
    stations_db = (
        session.query(FloorFacility)
        .filter(
            FloorFacility.building_uuid == building.uuid,
            FloorFacility.unit_type == Unit.UNIT_TYPE_STATION,
        )
        .all()
    )

    assert len(stations_db) == building_info[0]["station_count"] == len(stations)

    gates = building.gates
    gates_db = (
        session.query(FloorFacility)
        .filter(
            FloorFacility.building_uuid == building.uuid,
            FloorFacility.unit_type == Unit.UNIT_TYPE_GATE,
        )
        .all()
    )

    assert len(gates) == building_info[0]["gate_count"] == len(gates_db)

    auto_doors = building.auto_doors
    auto_doors_db = (
        session.query(FloorFacility)
        .filter(
            FloorFacility.building_uuid == building.uuid,
            FloorFacility.unit_type == Unit.UNIT_TYPE_AUTO_DOOR,
        )
        .all()
    )

    assert len(auto_doors) == building_info[0]["auto_door_count"] == len(auto_doors_db)

    chargers = building.chargers
    chargers_db = (
        session.query(FloorFacility)
        .filter(
            FloorFacility.building_uuid == building.uuid,
            FloorFacility.unit_type == Unit.UNIT_TYPE_CHARGER,
        )
        .all()
    )

    assert len(chargers) == building_info[0]["charger_count"] == len(chargers_db)

    sfus = (
        session.query(SiteFacilityUnit)
        .filter(SiteFacilityUnit.site_uuid == site_uuid)
        .all()
    )
    assert len(sfus) == len(elevators) + meta_info["robot_count"] + len(chargers) + len(
        auto_doors
    ) + len(stations) + len(gates)

    site_groups = session.query(SiteGroup).filter(SiteGroup.site_uuid == site_uuid)
    for sg in site_groups:
        if sg.unit_type == Unit.UNIT_TYPE_CHARGER:
            assert sorted(sg.members) == sorted(chargers)
        elif sg.unit_type == Unit.UNIT_TYPE_AUTO_DOOR:
            assert sorted(sg.members) == sorted(auto_doors)
        elif sg.unit_type == Unit.UNIT_TYPE_GATE:
            assert sorted(sg.members) == sorted(gates)
        elif sg.unit_type == Unit.UNIT_TYPE_ELEVATOR:
            assert sorted(sg.members) == sorted(elevators)
        elif sg.unit_type == Unit.UNIT_TYPE_STATION:
            assert sorted(sg.members) == sorted(stations)


def test_update_site(client):

    rsp = client.post(
        "/site",
        data=json.dumps(
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
                    "robot_count": 3,
                    "building_info": [
                        {
                            "name": "",
                            "floor_count": 6,
                            "elevator_count": 3,
                            "station_count": 1,
                            "gate_count": 5,
                            "auto_door_count": 3,
                            "charger_count": 2,
                        }
                    ],
                },
            }
        ),
        content_type="application/json",
        charset="UTF-8",
    )
    assert rsp.get_json() == {"msg": "success"}
