import string
import random

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
Session = scoped_session(sessionmaker())

STATE_LEN = 16


def gen_state(len):
    lst = [random.choice(string.ascii_letters + string.digits)
           for n in xrange(len)]
    return "".join(lst)


class state_mapping(Base):
    __tablename__ = 'state_mapping'

    index = Column(Integer, primary_key=True)
    state = Column(String(STATE_LEN))
    url = Column(String)


def put_url(url):
    state = gen_state(STATE_LEN)
    cm = state_mapping(state=state, url=url)
    Session.add(cm)
    Session.commit()

    return state


def get_url(state):
    ci = Session.query(state_mapping).filter_by(state=state)
    ret = None if ci.first() is None else ci.first().url
    if ci:
        ci.delete()

    return ret


def reset():
    Session.query(state_mapping).delete()
