import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import SessionLocal, engine, Base
from models import User, Organization, OrganizationMember, Room, Booking, Incident

fake = Faker()

def reset_database():
    """
    Drops and recreates all tables to ensure the seed script is fully reproducible.
    """
    print("Resetting database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Schema reset complete.")

def seed_data(session: Session):
    print("Seeding Users...")
    users = [
        User(
            full_name=fake.name(), 
            email=fake.unique.email(), 
            is_admin=random.choices([True, False], weights=[0.05, 0.95])[0]
        ) for _ in range(300)
    ]
    session.add_all(users)
    session.commit()

    print("Seeding Organizations...")
    custom_org_names = [
        "Financial Engine Society", 
        "Absurdist Theater Troupe", 
        "Inter-dimensional Literature Club",
        "Data Architecture Association",
        "Syphon Development Group",
        "Quantum Computing Guild",
        "Postmodern Art Collective",
        "Cryptocurrency Enthusiasts",
        "Urban Farming Initiative",
        "Philosophical Debate Society",
        "Graffiti Club"
    ]
    random_orgs = [f"{fake.word().capitalize()} Society" for _ in range(25)]
    
    orgs = [Organization(name=name, type="Student Group") for name in custom_org_names + random_orgs]
    session.add_all(orgs)
    session.commit()

    print("Seeding Rooms...")
    buildings = ["Cataño Science Center", "San Juan Hall", "Main Library"]
    rooms = []
    for bldg in buildings:
        for i in range(1, 21):  # 20 rooms per building = 60 rooms total
            rooms.append(
                Room(
                    building_name=bldg, 
                    room_number=f"{i}0{random.randint(1,9)}", 
                    capacity=random.randint(15, 150)
                )
            )
    session.add_all(rooms)
    session.commit()

    print("Seeding Organization Members (M:N Relationship)...")
    for user in users:
        user_orgs = random.sample(orgs, random.randint(1, 3))
        for org in user_orgs:
            member = OrganizationMember(
                user_id=user.id, 
                organization_id=org.id, 
                role=random.choice(["Member", "President", "Secretary"])
            )
            session.add(member)
    session.commit()

    print("Seeding Bookings (Targeting >2000 rows)...")
    # CHANGED: Start in Jan 2025 so bookings overlap with the Graffiti interventions!
    start_semester = datetime(2025, 1, 1, 8, 0)
    booking_count = 0

    for room in rooms:
        current_time = start_semester
        for _ in range(40):
            gap_hours = random.randint(1, 48)
            current_time += timedelta(hours=gap_hours)
            
            if current_time.hour < 8:
                current_time = current_time.replace(hour=8)
            elif current_time.hour > 20:
                current_time = current_time.replace(hour=8) + timedelta(days=1)

            duration = random.choice([1, 2, 3])
            end_time = current_time + timedelta(hours=duration)
            
            booking = Booking(
                room_id=room.id,
                organization_id=random.choice(orgs).id,
                start_time=current_time,
                end_time=end_time,
                status=random.choices(["Approved", "Pending", "Cancelled"], weights=[0.8, 0.1, 0.1])[0]
            )
            session.add(booking)
            booking_count += 1
            
            current_time = end_time 

    session.commit()
    print(f"Seed complete! Generated {booking_count} bookings.")

def seed_incidents(session: Session):
    """
    Seed incident data with graffiti reports before and after June 1, 2025.
    """
    print("Seeding Incidents (Graffiti Reports)...")
    buildings = ["Cataño Science Center", "San Juan Hall", "Main Library"]
    incidents = []
    
    # Pre-intervention: May 2025 (high frequency)
    for day in range(1, 31):
        if random.random() < 0.4:
            incidents.append(
                Incident(
                    incident_type="Graffiti",
                    building_name=random.choice(buildings),
                    reported_date=datetime(2025, 5, day, random.randint(8, 22), random.randint(0, 59))
                )
            )
    
    # Post-intervention: June 2025 onwards (lower frequency)
    for month in range(6, 9):
        days_in_month = 31 if month in [6, 8] else 30
        for day in range(1, days_in_month + 1):
            if random.random() < 0.15:
                incidents.append(
                    Incident(
                        incident_type="Graffiti",
                        building_name=random.choice(buildings),
                        reported_date=datetime(2025, month, day, random.randint(8, 22), random.randint(0, 59))
                    )
                )
    
    session.add_all(incidents)
    session.commit()
    print(f"Seed complete! Generated {len(incidents)} incident reports.")

def demonstrate_live_edge_case(session: Session):
    """
    Live Demo: Prove database-level double-booking prevention.
    """
    print("\n--- Running Live Demo: Double-Booking Edge Case ---")
    
    room = session.query(Room).first()
    org = session.query(Organization).first()
    
    base_time = datetime(2025, 12, 10, 14, 0)
    
    valid_booking = Booking(
        room_id=room.id,
        organization_id=org.id,
        start_time=base_time,
        end_time=base_time + timedelta(hours=2),
        status="Approved"
    )
    
    try:
        session.add(valid_booking)
        session.commit()
        print(f"[SUCCESS] Valid booking created in {room.building_name} {room.room_number}: 2:00 PM to 4:00 PM.")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to create valid booking: {e}")
        return

    overlapping_booking = Booking(
        room_id=room.id,
        organization_id=org.id,
        start_time=base_time + timedelta(hours=1), 
        end_time=base_time + timedelta(hours=3),
        status="Pending"
    )
    
    print("Attempting to insert overlapping booking (3:00 PM to 5:00 PM)...")
    
    try:
        session.add(overlapping_booking)
        session.commit() 
        print("[CRITICAL FAILURE] The database allowed the double-booking.")
    except IntegrityError:
        session.rollback() 
        print("[DEMO PASSED] Database explicitly rejected the overlapping timeslot.")
        print("Database integrity remains intact via Exclusion Constraint.")

if __name__ == "__main__":
    with SessionLocal() as db_session:
        reset_database()
        seed_data(db_session)
        seed_incidents(db_session)
        demonstrate_live_edge_case(db_session)