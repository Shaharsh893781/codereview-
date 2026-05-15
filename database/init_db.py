from database.session import Base, engine
from models.user import User
from models.scan import Scan


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
