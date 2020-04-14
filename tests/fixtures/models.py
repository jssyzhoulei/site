"""
pytest models
the pytestFixture whats setup to test
"""
import pytest

from app import CreateApp


@pytest.fixture
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
