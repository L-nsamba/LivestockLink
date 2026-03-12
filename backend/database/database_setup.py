from database.db import engine, Base
from models.user import User
from models.farmer import Farmer
from models.transporter import Transporter
from models.transport_request import TransportRequest
from models.booking import Bookings
from models.rating import Rating

Base.metadata.create_all(engine)
print("Tables created successfully")