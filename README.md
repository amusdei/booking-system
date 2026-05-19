# Smart Campus Room Booking System



## Entity-Relationship Diagram (ERD)

erDiagram
    USERS {
        int id PK
        string username
        string email
        int organization_id FK
    }
    ORGANIZATIONS {
        int id PK
        string name
        string type
    }
    ROOMS {
        int id PK
        string room_number
        string building
        int capacity
    }
    BOOKINGS {
        int id PK
        int user_id FK
        int room_id FK
        int organization_id FK
        datetime start_time
        datetime end_time
        string status
    }
    INCIDENTS {
        int id PK
        string incident_type
        string building_name
        datetime reported_date
        float repair_cost
    }

    ORGANIZATIONS ||--o{ USERS : "has members"
    ORGANIZATIONS ||--o{ BOOKINGS : "places"
    USERS ||--o{ BOOKINGS : "manages"
    ROOMS ||--o{ BOOKINGS : "hosts"



## Project Structure

├── app.py             # Streamlit front-end UI
├── database.py        # Database initialization & engine setup
├── models.py          # SQLAlchemy ORM blueprints & constraints
├── dal.py             # Data Access Layer (transactional queries)
├── analytics.py       # DuckDB OLAP engine for complex reporting
├── seed.py            # Faker script to generate 1,000+ test records
├── .env               # Hidden environment variables (DO NOT COMMIT)
└── README.md          # You are here




### Prerequisites & System Requirements

Before running this project, ensure you have the following installed:
* **Python 3.9+**
* **PostgreSQL (v13 or higher)** running locally or hosted.
* **psql** command-line tool (optional, but recommended for database inspection).


## Key Design Decisions

* **Double-Booking Prevention:** Handled strictly at the database level using a PostgreSQL `ExcludeConstraint` rather than relying on application-level Python logic.
* **Compute Isolation:** Analytics queries are routed through DuckDB to prevent heavy analytical processing from slowing down transactional room bookings.
* **Time Increments:** The system assumes all bookings are made in solid hour/minute blocks; recurring bookings.
* **Incident Tracking:** A separate `Incidents` table is included to track a particular incident, which can be correlated with booking data for additional insight.




## Analytics Dashboard Highlights

1. **Highest-Demand Spaces:** Ranks rooms by total hours booked using window functions.
2. **Organization Utilization:** Compares booking hours across different organizations.
3. **Peak Days:** Total hours booked across the week.
4. **Graffiti Frequency Correlation:** Campus vandalism reports before and after administrative intervention (June 2025).


# Data Architecture Rationale

Primary Transactional Store (PostgreSQL): PostgreSQL was chosen due to the requirement for strict ACID compliance in order to guarantee data integrity. Double-bookings and other such conflicts are prevented at the database layer using a native PostgreSQL Exclusion Constraint (tsrange over a GiST index). Attempted bookings within any point of an already existing booking's timeframe will be rejected.

Analytical Engine (DuckDB): Due to the resource-intensiveness of database operations, DuckDB was chosen as the analytical engine of this project in order to perform all analytical queries. Utilizing the embedded postgres_scanner extension, DuckDB directly attaches to the live PostgreSQL tables, streaming transactional records into an in-memory execution pipeline without degrading user interface response times.

These two design choices effectively separate the operational transaction processing (OLTP) of the application from its analytical query workloads (OLAP).


