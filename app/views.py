import logging
from flask import request
from flask_restful import Resource
from app.models import Site
from app.handlers.build_site import create_site, update_site, session

logger = logging.getLogger()


def parse_site(site: Site):
    return {
        "site_uid": site.site_uid,
        "uuid": site.uuid,
        "name": site.name,
        "address": site.address,
        "business_types": site.business_types,
        "location": site.location,
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
            return {"": ""}

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
