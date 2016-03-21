#!/usr/bin/python

from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import String, Integer, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


def make_session(connection_string):
    engine = create_engine(connection_string, echo=True,
                           encoding='utf-8', convert_unicode=True)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def pull_data(from_db, to_db, tables):
    source, source_engine = make_session(from_db)
    source_meta = MetaData(bind=source_engine)
    destination, dest_engine = make_session(to_db)

    for table_name in tables:
        print 'Processing', table_name
        print 'Pulling schema from source server'
        table = Table(table_name, source_meta, autoload=True)
        print 'Creating table on destination server'
        NewRecord = quick_mapper(table)
        NewRecord.metadata.create_all(dest_engine, checkfirst=True)
        columns = table.columns.keys()
        print 'Transferring records'
        for record in source.query(table).all():
            data = dict(
                [(str(column), getattr(record, column)) for column in columns]
            )
            destination.merge(NewRecord(**data))
    print 'Committing changes'
    destination.commit()


def quick_mapper(table):
    Base = declarative_base()

    if table.name == 'auth_mapping':
        class Mapper(Base):
            __tablename__ = 'auth_mapping'
            # verbatim from cauth
            cauth_id = Column(Integer, primary_key=True)
            domain = Column(String(255))
            external_id = Column(String(255))
    elif table.name == 'users':
        class Mapper(Base):
            __tablename__ = 'users'
            # verbatim from managesf
            username = Column(String(255), primary_key=True)
            fullname = Column(String(255), nullable=False)
            email = Column(String(255), nullable=False)
            hashed_password = Column(String(255), nullable=False)
            sshkey = Column(String(1023), nullable=True)
    else:
        class Mapper(Base):
            __table__ = table

    return Mapper


if __name__ == '__main__':
    import imp
    managesf_conf = imp.load_source('managesf_conf',
                                    '/var/www/managesf/config.py')
    cauth_conf = imp.load_source('cauth_conf', '/var/www/cauth/config.py')

    # Default values, should not be valid for all deployments
    MANAGESF_SQLITE_PATH_URL = 'sqlite:////var/lib/managesf/users.db'
    CAUTH_SQLITE_PATH_URL = 'sqlite:////var/lib/cauth/state_mapping.db'

    # pull local users data from managesf
    pull_data(MANAGESF_SQLITE_PATH_URL,
              managesf_conf.sqlalchemy['url'],
              ['users', ])
    #pull auth mappings date from cauth
    try:
        pull_data(CAUTH_SQLITE_PATH_URL,
                  cauth_conf.sqlalchemy['url'],
                  ['auth_mapping', ])
    except exc.NoSuchTableError:
        print "auth_mapping not available in this version of cauth, skipping."
