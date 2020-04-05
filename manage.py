#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import os
# from app.config import Config
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell, Server
from app import create_app, db


app = create_app(os.getenv('FLASK_ENV', 'dev'))

app.debug = True
manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command('shell', Shell())
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(use_debugger=True))


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@manager.command
def del_version():
    from sqlalchemy import text
    db_session = db.create_scoped_session(options={'autocommit': False, 'autoflush': False})
    sql = text('DELETE FROM alembic_version')
    db_session.execute(sql)
    db_session.flush()
    try:
        db_session.commit()
    except:
        print('提交失败')


if __name__ == '__main__':
    manager.run()
