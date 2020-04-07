import os


class BaseDevConfig(object):
    # 测试开发时共有的一些配置...
    DEBUG = True

    APP_NAME = "site-api"
    if os.environ.get("SECRET_KEY"):
        SECRET_KEY = os.environ.get("SECRET_KEY")
    else:
        SECRET_KEY = "SECRET_KEY_ENV_VAR_NOT_SET"
        print("SECRET KEY ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION")

    # SqlAlchemy
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 50
    SQLALCHEMY_POOL_TIMEOUT = 10
    TOKEN_TTL = 3600
    TOKEN_PREFIX = "site:token"

    # DB Url
    user = os.environ.get("DB_USER", "postgres")
    pwd = os.environ.get("DB_PASSWORD", "123456")
    host = os.environ.get("DB_HOST", "localhost")
    port = int(os.environ.get("DB_PORT", "5432"))

    db = os.environ.get("DB_NAME", "postgres")
    data = dict(user=user, pwd=pwd, host=host, port=port, db=db)
    con_str = (
        "postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}?client_encoding=utf8"
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or con_str.format(**data)


class DevConfig(BaseDevConfig):
    # 开发系统时定制化的一些配置
    pass


class ProConfig(object):
    # 系统正式部署时根据自己的需要的一些配置,例如mysql配置，redis配置等等，
    pass


config = {
    "dev": DevConfig,
    # 'tst': TestingConfig,
    "prd": ProConfig,
}
