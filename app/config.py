class BaseDevConfig(object):
    # 测试开发时共有的一些配置...
    DEBUG = True


class DevConfig(BaseDevConfig):
    # 开发系统时定制化的一些配置
    pass


class ProConfig(object):
    # 系统正式部署时根据自己的需要的一些配置,例如mysql配置，redis配置等等，
    pass


config = {
    'dev': DevConfig,
    # 'tst': TestingConfig,
    'prd': ProConfig,
}
