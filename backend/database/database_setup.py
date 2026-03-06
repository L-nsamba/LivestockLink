from database.db import engine, Base
from models.user import User

Base.metadata.create_all(engine)
print("Tables created successfully")