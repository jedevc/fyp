import os
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)


engine = create_engine(os.environ["DATABASE_URI"], echo = True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

session = Session()

