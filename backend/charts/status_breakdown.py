from database.db import Session
from models.transport_request import TransportRequest
from models.booking import Bookings
from sqlalchemy import func

def get_request_status_breakdown():
    """
    Returns count of transport requests grouped by status.
    Used by: GET /api/admin/charts/status-breakdown
    """
    session = Session()
    try:
        results = session.query(
            TransportRequest.status,
            func.count(TransportRequest.request_id).label('count')
        ).group_by(TransportRequest.status).all()

        return {
            'labels': [r.status for r in results],
            'data':   [r.count for r in results]
        }
    finally:
        session.close()


def get_booking_status_breakdown():
    """
    Returns count of bookings grouped by status.
    Useful if your Bookings model also has a status field
    e.g. CONFIRMED, IN_TRANSIT, COMPLETED, CANCELLED
    """
    session = Session()
    try:
        results = session.query(
            Bookings.status,
            func.count(Bookings.booking_id).label('count')
        ).group_by(Bookings.status).all()

        return {
            'labels': [r.status for r in results],
            'data':   [r.count for r in results]
        }
    finally:
        session.close()