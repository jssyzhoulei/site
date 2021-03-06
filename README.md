### a site info manage system for iot facility use

main for robot 

### 项目环境说明


env| value
---|---
python version | 3.7.3+
postgresql | 9.6
flask | 1.1.2

-  安装最新版docker

如果是linux环境还需要安装`docker-compose`

- 单个项目建议启用虚拟环境
建议`pyenv[推荐]  or virtualenv`  


- 为保证代码风格
本项目使用[black](https://pypi.org/project/black/) format

### 项目初始化准备

clone代码到本地

切换到相应python虚拟环境

运行数据库镜像
```
docker-compose up -d
```
安装项目依赖
```
pip install -r requirements.txt
```
建议先删除migrations目录

然后迁移db
```
python manage.py db init
python manage.py db migrate
python manage.py db updgrade
```

### Unit Test

项目使用pytest作为单元测试框架

当前大部分逻辑已经覆盖测试

在项目根目录执行`pytest`即可

测试数据库需要手动创建
```
# cd  项目根目录 查看容器是否启动
docker-compose ps
# 进入psql
psql -h localhost -p 5432 -U postgres
# 数据库密码在config以及docker-compose.yml都可以查看到
# 创建测试数据库
create database site;

```

生产数据库使用默认的postgres

测试数据库名限定为`site`

可以手动到`site/app/config`下的`TestingConfig`中配置修改

### 其他

如果要调试项目中的方法

建议使用`ipython`

调试前需要开启flask上下文
开启上下文方法已封装在项目中

具体示例如下：
```python
# 终端切换对应虚拟环境
# cd项目根目录
# ipython
from manage import make_shell_ctx
from some_modules import some_method

#开启上下文
make_shell_ctx()
some_method(some argues)
...

```


