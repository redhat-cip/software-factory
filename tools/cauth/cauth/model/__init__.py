from sqlalchemy import create_engine
from pecan import conf
from db import Session, Base, reset


def create_from_conf():
    configs = dict(conf.sqlalchemy)
    url = configs.pop('url')
    return create_engine(url, **configs)


def init_model():
    engine = create_from_conf()
    conf.sqlalchemy.engine = engine
    engine.connect()
    #create the tables if not existing
    Base.metadata.create_all(engine)

    start()
    reset()
    clear()


def start():
    Session.bind = conf.sqlalchemy.engine


def commit():
    Session.commit()


def rollback():
    Session.rollback()


def clear():
    Session.remove()
