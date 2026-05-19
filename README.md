# Smart Campus Room Booking System



## Entity-Relationship Diagram (ERD)


```mermaid
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
```
    ORGANIZATIONS ||--o{ USERS : "has members"
    ORGANIZATIONS ||--o{ BOOKINGS : "places"
    USERS ||--o{ BOOKINGS : "manages"
    ROOMS ||--o{ BOOKINGS : "hosts"



## Project Structure
```text
├── app.py             # Streamlit front-end UI
├── database.py        # Database initialization & engine setup
├── models.py          # SQLAlchemy ORM blueprints & constraints
├── dal.py             # Data Access Layer (transactional queries)
├── analytics.py       # DuckDB OLAP engine for complex reporting
├── seed.py            # Faker script to generate 1,000+ test records
├── requirements.txt   # Python dependency list
├── .env               # Hidden environment variables (DO NOT COMMIT)
├── .gitignore         # Files and folders excluded from version control
└── README.md          # Architecture documentation & rationale
```



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

Analytical Engine (DuckDB): Due to the resource-intensiveness of database operations, DuckDB was chosen as the analytical engine of this project in order to perform each analytical query, which requires heavy-lifting in its own right, such as parsing large datasets, window functions, complex filters, and multiple Common Table Expressions. Utilizing the embedded postgres_scanner extension, DuckDB directly attaches to the live PostgreSQL tables, streaming transactional records into an in-memory execution pipeline without degrading user interface response times.

These two design choices effectively separate the operational transaction processing (OLTP) of the application from its analytical query workloads (OLAP).



## Instructions for Running the Application

**MacOS/Linux [Bash]:**

1. Create a virtual environment and activate it:
   `python3 -m venv venv`
   `source venv/bin/activate`

2. Install the requirements:
   `pip install -r requirements.txt`

3. Make sure you have a `.env` file with your Postgres `DATABASE_URL`, following the format:
   `DATABASE_URL=postgresql://username:password@localhost:5432/your_database_name`

4. Load the fake data:
   `python seed.py`

5. Build the tables:
   `python database.py`

6. Start the dashboard:
   `streamlit run app.py`  


**Windows [DOS]:**

1. Create a virtual environment and activate it:
   `python -m venv venv`
   `venv\Scripts\activate`

2. Install the requirements:
   `pip install -r requirements.txt`

3. Make sure you have a `.env` file with your Postgres `DATABASE_URL`, following the format:
   `DATABASE_URL=postgresql://username:password@localhost:5432/your_database_name`

4. Load the fake data:
   `python seed.py`

5. Build the tables:
   `python database.py`

6. Start the dashboard:
   `streamlit run app.py`