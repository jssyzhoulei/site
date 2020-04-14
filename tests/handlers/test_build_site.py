import json


def test_create_site(client):
    rsp = client.post(
        "/site",
        data=json.dumps({
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
        }),
        content_type="application/json",
        charset="UTF-8",
    )
    assert rsp.get_json() == {"msg": "success"}
