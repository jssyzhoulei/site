from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

from app.config import config


db = SQLAlchemy()


def register_site_api(api):
    # from app.building import building_api
    # app.register_blueprint(cms_bp)
    # api.add_resource(someView, '/some/route')
    pass


def import_migrate_models():
    from app.models import (
        Site,
        SiteGroup,
        SiteFacilityUnit,
        Building,
        BuildingFloor,
        BuildingFloorConnector,
        Elevator,
        ElevatorFloor,
        Robot,
    )


class CreateApp(object):
    def __init__(self):
        self.db = db

    def create_app(self, config_name: str):
        # 实例化实现了wsgi接口功能的flask对象
        app = Flask(__name__)
        app.config.from_object(config[config_name])
        import_migrate_models()
        api = Api(app)
        self.db.init_app(app)
        register_site_api(api)
        return app


def create_app(config_name: str):
    # 实例化实现了wsgi接口功能的flask对象
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    import_migrate_models()
    api = Api(app)
    db.init_app(app)
    register_site_api(api)
    return app
