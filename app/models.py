#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import uuid
from typing import Dict, List, Tuple, Any
from app import db
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy import func, or_, and_
from flask import g


def get_session():
    return db.create_scoped_session(options={'autocommit': False, 'autoflush': False})


session = get_session()


class BaseMixIn(object):
    uuid = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    creator_uuid = db.Column(db.String(50), nullable=True)
    creator_ugid = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime(), default=datetime.datetime.now)
    modify_time = db.Column(db.DateTime(), default=lambda: datetime.datetime.now, onupdate=datetime.datetime.now)
    meta_info = db.Column(JSONB, nullable=True)
    is_delete = db.Column(db.Integer, nullable=True, default=0)
    version_id = db.Column(db.Integer, nullable=True, default=0)

    @classmethod
    def gen_version_id(cls, cls_uuid: uuid.UUID):
        return (
                       session
                       .query(func.max(cls.version_id))
                       .filter(cls.uuid == cls_uuid)
                       .scalar()
                       or 0
               ) + 1

    @classmethod
    def get_by_uuid(cls, cls_uuid: uuid.UUID):
        return session.query(cls).filter(cls.uuid == cls_uuid).scalar()

    @property
    def creator_user(self):
        data = None
        if data:
            return {'user_id': self.creator_uuid,
                    'user_name': data['username']}
        else:
            return {'user_id': self.creator_uuid,
                    'user_name': ""}

    @property
    def creator_group(self):
        data = None
        if data:
            return {'group_id': self.creator_ugid,
                    'group_name': data['group_name']}
        else:
            return {'group_id': self.creator_ugid,
                    'group_name': ""}

    def to_dict(self):
        return {c.name: c.type for c in self.__table__.columns}


class Unit:
    UNIT_TYPE_UNKNOWN = 0
    UNIT_TYPE_ROBOT = 1
    UNIT_TYPE_STATION = 2
    UNIT_TYPE_ELEVATOR = 3
    UNIT_TYPE_GATE = 4
    UNIT_TYPE_AUTO_DOOR = 5
    UNIT_TYPE_IOT_GENERAL = 6
    UNIT_TYPE_CHARGER = 10
    UNIT_TYPE_CALL = 11


class Direction:
    DIRECTION_UNKNOWN = 0
    DIRECTION_NO_DIRECTION = 1
    DIRECTION_IN = 2
    DIRECTION_OUT = 3
    DIRECTION_BIDIRECTIONAL = 4


class Site(db.Model, BaseMixIn):
    __tablename__: str = "site"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    SITE_STATUS_UNKNOWN = 0
    SITE_STATUS_NORMAL = 1
    SITE_STATUS_MAINTENANCE = 10
    SITE_STATUS_DISABLED = 20

    BUSINESS_TYPE_UNKNOWN = 0
    BUSINESS_TYPE_CBD = 1
    BUSINESS_TYPE_HOTEL = 2
    BUSINESS_TYPE_KTV = 3
    # map file key in meta info
    MAP_FILE_DOWNLOAD_KEY = "map_file_url"

    site_uid = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(128), nullable=False, default="")
    address = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.SmallInteger, nullable=False, default=0)
    has_building_connector = db.Column(db.Boolean, nullable=False, default=True)
    business_types = db.Column(ARRAY(db.Integer), nullable=False, default=[])
    location = db.Column(db.String(128), nullable=False, default="")

    section_site = db.Column(JSONB, nullable=False, default={})
    section_building = db.Column(JSONB, nullable=False, default={})
    section_map = db.Column(JSONB, nullable=False, default={})
    section_facility = db.Column(JSONB, nullable=False, default={})
    section_iot = db.Column(JSONB, nullable=False, default={})

    @classmethod
    def encode_business_type(cls, type_str: str) -> int:
        mapping = {
            "BUSINESS_TYPE_CBD": cls.BUSINESS_TYPE_CBD,
            "BUSINESS_TYPE_HOTEL": cls.BUSINESS_TYPE_HOTEL,
            "BUSINESS_TYPE_KTV": cls.BUSINESS_TYPE_KTV,
        }
        return mapping.get(type_str, cls.BUSINESS_TYPE_UNKNOWN)

    @classmethod
    def decode_business_type(cls, bussiness_type: int) -> str:
        mapping = {
            cls.BUSINESS_TYPE_CBD: "BUSINESS_TYPE_CBD",
            cls.BUSINESS_TYPE_HOTEL: "BUSINESS_TYPE_HOTEL",
            cls.BUSINESS_TYPE_KTV: "BUSINESS_TYPE_KTV",
        }
        return mapping.get(bussiness_type, "BUSINESS_TYPE_UNKNOWN")

    @classmethod
    def encode_site_status(cls, type_str: str) -> int:
        mapping = {
            "SITE_STATUS_DISABLED": cls.SITE_STATUS_DISABLED,
            "SITE_STATUS_NORMAL": cls.SITE_STATUS_NORMAL,
            "SITE_STATUS_MAINTENANCE": cls.SITE_STATUS_MAINTENANCE,
        }
        return mapping.get(type_str, cls.SITE_STATUS_UNKNOWN)

    @classmethod
    def decode_site_status(cls, status: int) -> str:
        mapping = {
            cls.SITE_STATUS_DISABLED: "SITE_STATUS_DISABLED",
            cls.SITE_STATUS_NORMAL: "SITE_STATUS_NORMAL",
            cls.SITE_STATUS_MAINTENANCE: "SITE_STATUS_MAINTENANCE",
        }
        return mapping.get(status, "SITE_STATUS_UNKNOWN")


class Building(db.Model, BaseMixIn):
    __tablename__: str = "building"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True))

    name = db.Column(db.String(128), nullable=False, default="")
    address = db.Column(db.String(128), nullable=False, default="")
    building_floors = db.Column(JSONB, nullable=False, default=[])
    elevators = db.Column(JSONB, nullable=False, default=[])
    chargers = db.Column(JSONB, nullable=False, default=[])
    stations = db.Column(JSONB, nullable=False, default=[])
    auto_doors = db.Column(JSONB, nullable=False, default=[])
    gates = db.Column(JSONB, nullable=False, default=[])

    def get_building_info(self):
        return {
            "uuid": str(self.uuid),
            "name": self.name,
            "address": self.address,
            "building_floors": self.get_building_floors_info(),
            "elevators": self.get_elevators_info(),
            "elevator_groups": self.get_elevator_group(),
            "charger_groups": self.get_charger_info(),
            "station_groups": self.get_station_info(),
            "auto_door_groups": self.get_auto_door_info(),
            "gate_groups": self.get_gate_info(),
        }

    def get_building_floors_info(self):
        """Keep order based on building_floors
        :return:
        """

        def get_connect_building_floor_uuid(floor_uuid: str):
            connect_building_floor_uuid_list = []
            connects = (
                session
                .query(BuildingFloorConnector)
                .filter(BuildingFloorConnector.is_delete == 0)
                .filter(
                # 只查主关联侧
                BuildingFloorConnector.floor_uuid_1 == uuid.UUID(floor_uuid),
                # BuildingFloorConnector.floor_uuid_2 == uuid.UUID(floor_uuid),
                )
            ).all()
            for c in connects:
                connect_building_floor_uuid_list.append(c.floor_uuid_2)

            return connect_building_floor_uuid_list

        query = (
            session
            .query(BuildingFloor)
            .filter(BuildingFloor.building_uuid == self.uuid)
            .order_by(BuildingFloor.create_time)
            .all()
        )
        bfloors = {str(floor.uuid): floor for floor in query}

        # TODO change to SystemError
        assert len(bfloors) == len(self.building_floors)

        info = []
        for _uuid in self.building_floors:
            bfloor: BuildingFloor = bfloors[_uuid]
            connect_building_floor_uuid_list = get_connect_building_floor_uuid(_uuid)
            if connect_building_floor_uuid_list:
                for connect in connect_building_floor_uuid_list:
                    if str(connect) != _uuid:
                        info.append(
                            {
                                "uuid": _uuid,
                                "name": bfloor.name,
                                "connected_building_floor_uuid": str(connect),
                            }
                        )
            else:
                info.append(
                    {
                        "uuid": _uuid,
                        "name": bfloor.name,
                        "connected_building_floor_uuid": "",
                    }
                )

        return info

    def get_elevators_info(self):
        """Keep order based on elevators
        """
        query = (
            session
            .query(Elevator)
            .filter(Elevator.building_uuid == self.uuid)
            .all()
        )

        belevators = {str(elevator.uuid): elevator for elevator in query}

        # TODO change to SystemError
        assert len(belevators) == len(self.elevators)

        info = []
        for _uuid in self.elevators:
            belevator: Elevator = belevators[_uuid]
            info.append(
                {
                    "uuid": str(belevator.uuid),
                    "name": belevator.name,
                    "brand": belevator.brand,
                    "elevator_floors": belevator.get_elevator_floors_info(),
                }
            )
        return info

    def get_facility_group(self, unit_type: int):
        """Keep order based on elevators
        """
        query = (
            session
            .query(SiteGroup)
            .filter(SiteGroup.building_uuid == self.uuid)
            .filter(SiteGroup.unit_type == unit_type)
            .order_by(SiteGroup.create_time)
            .all()
        )

        info = []
        for site_group in query:
            group = site_group.get_site_group_info()
            if group:
                info.append(group)
        return info

    def get_auto_door_info(self):
        return self.get_facility_group(Unit.UNIT_TYPE_AUTO_DOOR)

    def get_gate_info(self):
        return self.get_facility_group(Unit.UNIT_TYPE_GATE)

    def get_charger_info(self):
        return self.get_facility_group(Unit.UNIT_TYPE_CHARGER)

    def get_station_info(self):
        return self.get_facility_group(Unit.UNIT_TYPE_STATION)

    def get_elevator_group(self):
        return self.get_facility_group(Unit.UNIT_TYPE_ELEVATOR)


class BuildingFloor(db.Model, BaseMixIn):
    __tablename__: str = "building_floor"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True))
    building_uuid = db.Column(UUID(as_uuid=True))

    name = db.Column(db.String(128), nullable=False, default="")
    floor_index = db.Column(db.Integer, nullable=False, default=0)
    connected_floors = db.Column(JSONB, nullable=False, default=[])
    floor_facilities = db.Column(JSONB, nullable=False, default=[])

    def get_building_floor_info(self):
        # map = session().query(Map).filter(Map.building_floor_uuid == self.uuid).first()
        building_floor_info = {
            "uuid": str(self.uuid),
            "name": self.name,
            "floor_index": self.floor_index,
        }
        # if map:
        #     building_floor_info["map_sid"] = map.map_sid
        return building_floor_info


class BuildingFloorConnector(db.Model, BaseMixIn):
    __tablename__: str = "building_floor_connector"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True))

    building_uuid_1 = db.Column(UUID(as_uuid=True))
    floor_uuid_1 = db.Column(UUID(as_uuid=True))
    building_uuid_2 = db.Column(UUID(as_uuid=True))
    floor_uuid_2 = db.Column(UUID(as_uuid=True))

    @classmethod
    def is_floor_connect_exist(
            cls, floor_uuid_1: uuid.UUID, floor_uuid_2: uuid.UUID
    ) -> list:
        # floor_uuid_1 作为主关联侧  floor_uuid_2作为被关联方
        # 但是不允许 floor_uuid_1 floor_uuid_2 关联两次  即使位置不同
        return (
            session
            .query(cls)
            .filter(cls.is_delete == 0)
            .filter(
                or_(
                    and_(
                        cls.floor_uuid_1 == floor_uuid_1,
                        cls.floor_uuid_2 == floor_uuid_2,
                    ),
                    and_(
                        cls.floor_uuid_1 == floor_uuid_2,
                        cls.floor_uuid_2 == floor_uuid_1,
                    ),
                )
            )
        ).all()


class Elevator(db.Model, BaseMixIn):
    __tablename__: str = "elevator"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True))
    building_uuid = db.Column(UUID(as_uuid=True))

    name = db.Column(db.String(128), nullable=False, default="")
    brand = db.Column(db.String(128), nullable=False, default="")
    elevator_floors = db.Column(JSONB, nullable=False, default=[])
    group_uuid = db.Column(UUID(as_uuid=True))

    def get_elevator_floors_info(self):
        """Keep elevator floors order based on elevator_floors
        :return:
        """
        query = (
            session
            .query(ElevatorFloor)
            .filter(ElevatorFloor.elevator_uuid == self.uuid)
            .all()
        )
        efloors = {str(efloor.uuid): efloor for efloor in query}
        info = []
        for _uuid in self.elevator_floors:
            efloor: ElevatorFloor = efloors[_uuid]
            info.append(
                {
                    "uuid": str(efloor.uuid),
                    "name": efloor.name,
                    "building_floor_uuid": str(efloor.building_floor_uuid or ""),
                }
            )
        return info


class ElevatorFloor(db.Model, BaseMixIn):
    __tablename__: str = "elevator_floor"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True))
    building_uuid = db.Column(UUID(as_uuid=True))
    elevator_uuid = db.Column(UUID(as_uuid=True))

    floor_index = db.Column(db.Integer, nullable=False, default=0)
    name = db.Column(db.String(128), nullable=False, default="")
    building_floor_uuid = db.Column(UUID(as_uuid=True))
    is_reachable = db.Column(db.Boolean, nullable=False, default=False)


class FloorFacility(db.Model, BaseMixIn):
    __tablename__: str = "floor_facility"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True))

    name = db.Column(db.String(128), nullable=False, default="")
    unit_type = db.Column(db.SmallInteger, nullable=False)
    direction = db.Column(db.SmallInteger, nullable=False, default=0)
    building_uuid = db.Column(UUID(as_uuid=True))
    group_uuid = db.Column(UUID(as_uuid=True))
    building_floor_uuid = db.Column(UUID(as_uuid=True))

    def get_floor_facility_info(self):
        return {
            "uuid": str(self.uuid),
            "name": self.name,
            "direction": self.direction,
            "unit_type": self.unit_type,
            "building_uuid": str(self.building_uuid or ""),
            "building_floor_uuid": str(self.building_floor_uuid or ""),
        }


class SiteGroup(db.Model, BaseMixIn):
    __tablename__: str = "site_group"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True))
    building_uuid = db.Column(UUID(as_uuid=True), nullable=True)
    building_floor_uuid = db.Column(UUID(as_uuid=True))

    name = db.Column(db.String(128), nullable=False, default="")
    facility_group_sid = db.Column(db.Integer)
    unit_type = db.Column(db.SmallInteger, nullable=False, default=0)
    members = db.Column(JSONB, nullable=False, default=[])

    def get_members_attr(self):
        type_cls_dict = {
            Unit.UNIT_TYPE_GATE: FloorFacility,
            Unit.UNIT_TYPE_AUTO_DOOR: FloorFacility,
            Unit.UNIT_TYPE_CHARGER: FloorFacility,
            Unit.UNIT_TYPE_STATION: FloorFacility,
            Unit.UNIT_TYPE_ELEVATOR: Elevator,
            Unit.UNIT_TYPE_ROBOT: Robot,
        }

        cls = type_cls_dict[self.unit_type]
        # elevator、robot 没有building floor uuid 、 unit_type
        # robot 只有name

        units = (
            session
            .query(SiteFacilityUnit)
            .filter(SiteFacilityUnit.facility_uuid.in_(self.members))
            .all()
        )
        facility_unit_dict = {str(i.facility_uuid): i for i in units}

        if cls == FloorFacility:
            query = (
                session
                .query(
                    cls.name,
                    cls.uuid,
                    cls.direction,
                    cls.unit_type,
                    cls.building_uuid,
                    cls.building_floor_uuid,
                )
                .filter(cls.uuid.in_(self.members))
                .order_by(cls.create_time)
                .all()
            )

            return [
                {
                    "name": i.name,
                    "uuid": str(i.uuid),
                    "direction": i.direction,
                    "unit_type": i.unit_type,
                    "building_uuid": str(i.building_uuid),
                    "unit_name": facility_unit_dict[str(i.uuid)].unit_name or "",
                    "unit_uid": facility_unit_dict[str(i.uuid)].unit_uid or 0,
                    "unit_uuid": str(facility_unit_dict[str(i.uuid)].unit_uuid or ""),
                    "building_floor_uuid": str(i.building_floor_uuid or ""),
                }
                for i in query
            ]
        if cls == Elevator or cls == Robot:
            query = (
                session
                .query(cls.name, cls.uuid)
                .filter(cls.uuid.in_(self.members))
                .order_by(cls.create_time)
                .all()
            )
            return [
                {
                    "name": i.name,
                    "uuid": str(i.uuid),
                    "unit_name": facility_unit_dict[str(i.uuid)].unit_name or "",
                    "unit_uid": facility_unit_dict[str(i.uuid)].unit_uid or 0,
                    "unit_uuid": str(facility_unit_dict[str(i.uuid)].unit_uuid or ""),
                }
                for i in query
            ]

    def get_site_group_info(self):
        group = {
            "uuid": str(self.uuid),
            "name": self.name,
            "building_floor_uuid": str(self.building_floor_uuid or ""),
            "unit_type": self.unit_type,
            "members": self.get_members_attr(),
        }
        if self.unit_type in [Unit.UNIT_TYPE_ROBOT, Unit.UNIT_TYPE_ELEVATOR]:
            del group["building_floor_uuid"]
        return group


class Robot(db.Model, BaseMixIn):
    __tablename__: str = "robot"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    ROBOT_TYPE_UNKNOWN = 0
    ROBOT_TYPE_DELIVERY = 10
    ROBOT_TYPE_STERILIZATION = 20

    ROBOT_HOME_POI_KEY = "home_point_poi"

    site_uuid = db.Column(UUID(as_uuid=True))
    robot_type = db.Column(db.SmallInteger, nullable=False, default=0)
    group_uuid = db.Column(UUID(as_uuid=True))
    name = db.Column(db.String(128), nullable=False, default="")

    def get_robot_info(self):
        sfu: SiteFacilityUnit = session.query(SiteFacilityUnit).filter(
            SiteFacilityUnit.facility_uuid == self.uuid
        ).scalar()
        return {
            "uuid": self.uuid,
            "name": self.name,
            "unit_uid": sfu.unit_uid,
            "facility_sid": sfu.facility_sid,
            "robot_type": self.robot_type,
        }


class SiteFacilityUnit(db.Model, BaseMixIn):
    __tablename__: str = "site_facility_unit"
    __table_args__: Dict[str, Any] = {"schema": "public"}

    site_uuid = db.Column(UUID(as_uuid=True), nullable=False)
    site_uid = db.Column(db.BigInteger, nullable=False)

    facility_uuid = db.Column(UUID(as_uuid=True))
    group_uuid = db.Column(UUID(as_uuid=True))
    facility_sid = db.Column(db.Integer, default=0)
    facility_group_index = db.Column(db.Integer, default=0)
    unit_type = db.Column(db.Integer, nullable=False)
    unit_uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=True)
    unit_uid = db.Column(db.BigInteger, unique=True, nullable=True)
    unit_name = db.Column(db.String, nullable=True)

    def get_facility_name(self, facility_uuid: uuid.UUID) -> str:
        if self.unit_type == Unit.UNIT_TYPE_ELEVATOR:
            cls = Elevator
        elif self.unit_type == Unit.UNIT_TYPE_ROBOT:
            cls = Robot
        else:
            cls = FloorFacility

        facility = session.query(cls).filter(cls.uuid == facility_uuid).scalar()
        if facility is not None:
            return facility.name

    def get_facility_unit_info(self):
        return {
            str(self.uuid): {
                "site_uid": self.site_uid,
                "site_uuid": str(self.site_uuid),
                "facility_name": self.get_facility_name(self.facility_uuid),
                "facility_uuid": str(self.facility_uuid),
                "group_uuid": str(self.group_uuid),
                "unit_type": self.unit_type,
                "unit_uuid": str(self.unit_uuid or ""),
                "unit_uid": self.unit_uid or 0,
                "unit_name": self.unit_name or "",
            }
        }

    def get_site_info(self):
        site_group: SiteGroup = (
            session
            .query(SiteGroup)
            .filter(SiteGroup.uuid == self.group_uuid)
            .first()
        )
        if not site_group:
            # SiteGroupNotFound
            raise

        return {
            "site_uuid": str(self.site_uuid),
            "site_uid": self.site_uid,
            "unit_type": self.unit_type,
            "unit_uuid": str(self.unit_uuid) if self.unit_uuid else None,
            "unit_uid": self.unit_uid,
            "unit_sid": self.facility_sid,
            "unit_group_sid": site_group.facility_group_sid,
            "unit_group_index": self.facility_group_index,
            "unit_name": self.unit_name,
        }

    @classmethod
    def get_bind_unit_uuid_list(cls, unit_type: int) -> list:
        unit_uuids = (
            session
            .query(cls.unit_uuid)
            .filter(cls.unit_type == unit_type)
            .filter(cls.unit_uuid != None)
            .all()
        )
        return [str(i[0]) for i in unit_uuids]

    @classmethod
    def query_by_unit_uuid(cls, unit_uuid: str):
        return session.query(cls).filter(cls.unit_uuid == unit_uuid).first()
