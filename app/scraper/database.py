from sqlalchemy import create_engine#, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(
    'postgresql+psycopg2://nally:Upwork924))@postgre1.cjpmfdzqif3u.us-east-1.rds.amazonaws.com:5432/postgres',
    convert_unicode=True
)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
# metadata = MetaData(bind=engine)
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    from .models import Test, Employees, ScheduleRecon

    Base.metadata.tables['schedulerecon'].drop(engine)
    Base.metadata.create_all(bind=engine)

    # ScheduleRecon.query.delete()
    # db_session.commit()


def rowInsert(table, array):
    insert_query = table.__table__.insert().values(array)
    db_session.execute(insert_query)
    db_session.commit()
    




# Base.metadata.create_all(bind=engine)
##how to get the raw cursor
# connection = engine.raw_connection()
# cur = connection.cursor()
# cur.execute('SELECT version()')
# version = cur.fetchone()[0]
# print(version)
