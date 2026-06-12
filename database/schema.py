from database.models import Base
from database.database import engine


def init_db():
    Base.metadata.create_all(bind=engine)
