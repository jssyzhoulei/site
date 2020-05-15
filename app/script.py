import uuid
from app.models import Cmdb, Unit, session


def build_random_unit():
    # 创建随机的unit
    unit_name_map = {
        Unit.UNIT_TYPE_ROBOT: "fake-机器人",
        Unit.UNIT_TYPE_ELEVATOR: "fake-电梯板",
        Unit.UNIT_TYPE_STATION: "fake-sation-unit",
        Unit.UNIT_TYPE_GATE: "fake-闸机",
        Unit.UNIT_TYPE_AUTO_DOOR: "fake-自动门板子",
        Unit.UNIT_TYPE_CHARGER: "fake-充电桩板子",
    }

    unit_uid =1
    for unit_type, name in unit_name_map.items():
        for i in range(20):
            unit = Cmdb(
                unit_type=unit_type,
                unit_uuid=uuid.uuid4(),
                unit_uid=unit_uid,
                # 资产名称
                unit_name=f"{name}-{i+1}",
            )
            unit_uid += 1
            session.add(unit)

    try:

        session.commit()
    except Exception as e:
        session.rollback()
        raise
