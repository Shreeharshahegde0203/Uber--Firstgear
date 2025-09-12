from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import User, Ride


def find_driver(db: Session):
    """
    Find the closest available driver for a requested ride.
    For now, 'closeness' = simple string match or priority logic.
    """

    # 1. Get the first ride with status 'requested'
    ride = db.query(Ride).filter(Ride.status == "requested").first()
    if not ride:
        return None, None  # no rides waiting

    # 2. Get available drivers
    available_drivers = db.query(User).filter(
        and_(User.is_driver == True, User.availability == True)
    ).all()

    if not available_drivers:
        return ride, None  # no drivers free

    # 3. Real distance calculation using Haversine formula
    import math
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    closest_driver = None
    min_distance = float('inf')
    for driver in available_drivers:
        if driver.latitude is not None and driver.longitude is not None and ride.start_lat is not None and ride.start_lng is not None:
            dist = haversine(driver.latitude, driver.longitude, ride.start_lat, ride.start_lng)
            if dist < min_distance:
                min_distance = dist
                closest_driver = driver

    # fallback → pick the first available driver
    if not closest_driver:
        closest_driver = available_drivers[0]

    # 4. Assign driver to ride
    ride.driver_id = closest_driver.id
    ride.status = "accepted"
    closest_driver.availability = False  # mark driver busy

    db.commit()
    db.refresh(ride)
    db.refresh(closest_driver)
    
    # Get rider information for mutual visibility
    rider = db.query(User).filter(User.id == ride.rider_id).first()
    ride.rider = rider
    ride.driver = closest_driver

    return ride, closest_driver
