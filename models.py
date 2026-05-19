
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, 
    DateTime, UniqueConstraint, text
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import ExcludeConstraint

Base = declarative_base()


# Relationships (Entity-Relationship):

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)

    # USER-ORGANIZATION (1-M)
    organizations = relationship("OrganizationMember", back_populates="user")


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(String(50)) 

    # ORGANIZATION-USER (1-M)
    members = relationship("OrganizationMember", back_populates="organization")

    # ORGANIZATION-BOOKING (1-M)
    bookings = relationship("Booking", back_populates="organization")


class OrganizationMember(Base):
    __tablename__ = 'organization_members'

    # [JUNCTION TABLE]
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), primary_key=True)
    role = Column(String(50), nullable=False)

    # USER-ORGANIZATION (M-M)
    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization", back_populates="members")


class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_name = Column(String(255), nullable=False)
    room_number = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)


    # CREATION OF IDENTICAL ROOMS PREVENTION
    __table_args__ = (
        UniqueConstraint('building_name', 'room_number', name='uix_building_room'),
    )

    # ROOM-BOOKING (1-M)
    bookings = relationship("Booking", back_populates="room")



# CENTRAL HUB

class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default='Pending')

    # ROOM-BOOKING (M-1) 
    room = relationship("Room", back_populates="bookings")

    # ORGANIZATION-BOOKING (M-1)
    organization = relationship("Organization", back_populates="bookings")


    # DOUBLE-BOOKING PREVENTION
    __table_args__ = (
        ExcludeConstraint(
            ('room_id', '='),
            (text("tsrange(start_time, end_time)"), '&&'),
            name='prevent_double_booking',
            using='gist'
        ),
    )



class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String, nullable=False)
    building_name = Column(String, nullable=False)
    reported_date = Column(DateTime, nullable=False)