import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


engine = create_engine(os.environ["DATABASE_URI"], echo=True)

# Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
