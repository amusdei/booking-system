from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from models import Booking, Room, Organization, User

class BookingRepository:

    """
    Data Access Object (DAO) for handling all Booking-related database operations.
    Keeps all SQLAlchemy logic completely isolated from the UI layer.
    """

    def __init__(self, session: Session):
        self.session = session

    def is_room_available(self, room_id: int, start_time: datetime, end_time: datetime) -> bool:
        
        """
        Application-level double-booking prevention.
        Checks for overlapping time slots before attempting an insert.
        Two time ranges overlap if: (Start A < End B) AND (End A > Start B)
        """
        
        overlap_exists = self.session.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
            Booking.status != 'Cancelled'  # Cancelled bookings don't block availability
        ).first()
        
        return overlap_exists is None


    def create_booking(self, room_id: int, organization_id: int, start_time: datetime, end_time: datetime) -> Booking:
       
        """
        Creates a new booking, enforcing rules at the application layer and 
        handling potential database-level constraint violations safely.
        """
        
        if not self.is_room_available(room_id, start_time, end_time):
            raise ValueError("Time slot unavailable: Caught by Application Layer check.")

        new_booking = Booking(
            room_id=room_id,
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time,
            status='Approved'
        )
        
        try:
            self.session.add(new_booking)
            self.session.commit()
            return new_booking
        except IntegrityError:
            self.session.rollback()
            raise ValueError("Time slot unavailable: Caught by Postgres Exclusion Constraint.")
        except Exception as e:
            self.session.rollback()
            raise e

    def get_organization_bookings(self, organization_id: int):

        """
        Fetches all bookings for a specific organization, ordering by the most upcoming.
        """
        return self.session.query(Booking).filter(
            Booking.organization_id == organization_id
        ).order_by(Booking.start_time.asc()).all()

    def get_all_rooms(self):

        """
        Retrieves the master list of rooms for UI dropdowns.
        """
        return self.session.query(Room).order_by(Room.building_name, Room.room_number).all()
    
    def get_all_organizations(self):

        """
        Fetches all organizations from the database, ordered alphabetically by name.
        """
        return self.session.query(Organization).order_by(Organization.name).all()