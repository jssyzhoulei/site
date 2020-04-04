from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def register_site_api(api):
    # from app.building import building_api
    # app.register_blueprint(cms_bp)
    # api.add_resource(someView, '/some/route')
    pass


def create_app(config_obj: str):
    # 实例化实现了wsgi接口功能的flask对象
    app = Flask(__name__)
    app.config.from_object(config_obj)
    api = Api(app)
    db.init_app(app)
    register_site_api(api)
    return app
