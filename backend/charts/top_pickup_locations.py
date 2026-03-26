from database.db import Session
from models.transport_request import TransportRequest
from sqlalchemy import func

def get_top_pickup_locations(limit=4):
    """
    Returns the most frequently requested pickup locations.
    Used by: GET /api/admin/charts/top-pickup-locations
    """
    session = Session()
    try:
        results = session.query(
            TransportRequest.pickup_location,
            func.count(TransportRequest.request_id).label('count')
        ).group_by(
            TransportRequest.pickup_location
        ).order_by(
            func.count(TransportRequest.request_id).desc()
        ).limit(limit).all()

        return {
            'labels': [r.pickup_location for r in results],
            'data':   [r.count for r in results]
        }
    finally:
        session.close()


def get_top_destination_locations(limit=4):
    """
    Returns the most frequently requested destination locations.
    Easy to add as a second chart alongside pickup locations.
    """
    session = Session()
    try:
        results = session.query(
            TransportRequest.destination_location,
            func.count(TransportRequest.request_id).label('count')
        ).group_by(
            TransportRequest.destination_location
        ).order_by(
            func.count(TransportRequest.request_id).desc()
        ).limit(limit).all()

        return {
            'labels': [r.destination_location for r in results],
            'data':   [r.count for r in results]
        }
    finally:
        session.close()