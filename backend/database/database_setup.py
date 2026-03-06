from database.db import engine, Base
from models.user import User
from models.farmer import Farmer
from models.transporter import Transporter

Base.metadata.create_all(engine)
print("Tables created successfully")