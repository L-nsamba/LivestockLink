from database.db import Session
from models.transport_request import TransportRequest
from sqlalchemy import func

def get_requests_per_day():
    """
    Returns daily count of transport requests.
    Used by: GET /api/admin/charts/requests-per-day
    """
    session = Session()
    try:
        results = session.query(
            func.date(TransportRequest.created_at).label('day'),
            func.count(TransportRequest.request_id).label('count')
        ).group_by(
            func.date(TransportRequest.created_at)
        ).order_by(
            func.date(TransportRequest.created_at)
        ).all()

        return {
            'labels': [str(r.day) for r in results],
            'data':   [r.count for r in results]
        }
    finally:
        session.close()


def get_requests_per_month():
    """
    Returns monthly count of transport requests.
    Useful for a broader time-range view on the same chart.
    """
    session = Session()
    try:
        results = session.query(
            func.year(TransportRequest.created_at).label('year'),
            func.month(TransportRequest.created_at).label('month'),
            func.count(TransportRequest.request_id).label('count')
        ).group_by(
            func.year(TransportRequest.created_at),
            func.month(TransportRequest.created_at)
        ).order_by(
            func.year(TransportRequest.created_at),
            func.month(TransportRequest.created_at)
        ).all()

        return {
            'labels': [f"{r.year}-{str(r.month).zfill(2)}" for r in results],
            'data':   [r.count for r in results]
        }
    finally:
        session.close()