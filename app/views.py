import logging
from flask import request
from flask_restful import Resource
from app.models import Site
from app.handlers.build_site import create_site, update_site, session
from app.handlers.buildings import get_site_building, update_site_building
from app.handlers.facility_bind import get_unit_list, update_bind_facility

logger = logging.getLogger()


def parse_site(site: Site):
    return {
        "site_uid": site.site_uid,
        "uuid": str(site.uuid),
        "name": site.name,
        "status": site.status,
        "address": site.address,
        "has_building_connector": site.has_building_connector,
        "business_types": site.business_types,
        "location": site.location,
        "meta_info": site.meta_info,
    }


class SiteView(Resource):
    method_decorators = []

    def get(self):
        site_uuid = request.args.get("site_uuid")
        if site_uuid is None:
            return {"msg": "请求参数出错"}
        site = session.query(Site).get(site_uuid)
        rsp = {}
        if site is not None:

            rsp = parse_site(site)
        return rsp

    def post(self):
        data = request.get_json()
        if data is None:
            return {"msg": "没有请求数据"}

        create_site(data)
        return {"msg": "success"}

    def put(self):
        # 修改site信息只可增加数据 删除另外有接口
        data = request.get_json()

        update_site(data)
        return {"msg": "success"}


class SitesView(Resource):
    method_decorators = []

    def get(self):
        name = request.args.get("name")
        sites = session.query(Site)
        if name:
            sites = sites.filter(Site.name.ilike(f"%{name}%"))

        return [parse_site(i) for i in sites]


class BuildingView(Resource):
    method_decorators = []

    def get(self):
        site_uuid = request.args.get("site_uuid")
        if site_uuid is None:
            return {"msg": "请求参数出错"}
        return get_site_building(site_uuid)

    def put(self):
        site_uuid = request.args.get("site_uuid")
        if site_uuid is None:
            return {"msg": "请求参数出错"}
        data = request.get_json()
        if data is None:
            return {"msg": "没有请求数据"}

        update_site_building(site_uuid, data)
        return get_site_building(site_uuid)


class UnitsView(Resource):
    method_decorators = []

    def get(self):
        site_uuid = request.args.get("site_uuid")
        unit_type = request.args.get("unit_type")
        building_uuid = request.args.get("building_uuid")
        if not all([site_uuid, unit_type]):
            return {"msg": "请求参数出错"}
        return get_unit_list(unit_type, site_uuid, building_uuid)


class FacilityBindView(Resource):
    method_decorators = []

    def put(self):
        # 提交的数据以building和unit type为单位
        site_uuid = request.args.get("site_uuid")
        unit_type = request.args.get("unit_type")
        if not all([site_uuid, unit_type]):
            return {"msg": "请求参数出错"}
        new_bind_facility = request.get_json()
        if new_bind_facility is None:
            return {"msg": "没有请求数据"}

        update_bind_facility(site_uuid, new_bind_facility, unit_type)
        return get_site_building(site_uuid)
