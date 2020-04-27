"""
pytest models
the pytestFixture whats setup to test
"""
import pytest

from app import CreateApp
from app.handlers.build_site import create_site, Site, force_cleanup_site, session


@pytest.fixture(scope="session")
def client():
    cls = CreateApp()
    app = cls.create_app("test")
    with app.test_client() as client:
        with app.app_context():
            # 清空此前测试数据
            # 注意保证创建site数据库作为测试数据库
            # dev数据库为postgres
            cls.db.drop_all()
            cls.db.create_all()
            cls.db.session.commit()
        yield client


@pytest.fixture(scope="function")
def connect_site(client):
    create_site(
        {
            "business_types": [1],
            "name": "联通大厦",
            "address": "上海市南京路50号",
            "has_building_connector": True,
            "enabled": True,
            "status": 1,
            "location": "",
            "meta_info": {
                "building_count": 2,
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
                    },
                    {
                        "name": "",
                        "floor_count": 3,
                        "elevator_count": 2,
                        "station_count": 1,
                        "gate_count": 3,
                        "auto_door_count": 3,
                        "charger_count": 2,
                    },
                ],
            },
        }
    )
    yield
    s = session.query(Site).first()
    force_cleanup_site(s.uuid)
