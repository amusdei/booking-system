
import os
import duckdb
from dotenv import load_dotenv


class AnalyticsEngine:

    """
    Analytical Access Layer (DAL)
    """

    def __init__(self):
        load_dotenv()
        self.pg_url = os.getenv("DATABASE_URL")
        if not self.pg_url:
            raise ValueError("DATABASE_URL is missing from .env")
        

        # DuckDB INITIALIZATION
        self.conn = duckdb.connect(database=':memory:')
        

        # PostgreSQL SETUP
        self.conn.execute("LOAD postgres;")


        # DATABASE SCHEMA CREATION
        attach_query = f"ATTACH '{self.pg_url}' AS pg (TYPE POSTGRES);"
        self.conn.execute(attach_query)



    # QUERIES

    def get_utilization_ranking(self):
        
        """
        Ranking of total hours booked per room (highest demand to lowest)
        """

        query = """
            SELECT 
                r.building_name, 
                r.room_number,
                SUM(EXTRACT(EPOCH FROM (b.end_time - b.start_time))/3600) AS total_hours_booked,
                RANK() OVER (ORDER BY SUM(EXTRACT(EPOCH FROM (b.end_time - b.start_time))/3600) DESC) as demand_rank
            FROM pg.bookings b
            JOIN pg.rooms r ON b.room_id = r.id
            WHERE b.status = 'Approved'
            GROUP BY r.building_name, r.room_number
            ORDER BY demand_rank;
        """
        return self.conn.execute(query).df()
    

    def get_hoarding_analysis(self):
       
        """
        Organizations with the highest cancellation rates
        """

        query = """
            WITH org_totals AS (
                SELECT o.id, o.name, COUNT(*) as total_requests
                FROM pg.bookings b
                JOIN pg.organizations o ON b.organization_id = o.id
                GROUP BY o.id, o.name
            ),
            org_cancellations AS (
                SELECT o.id, COUNT(*) as cancelled_requests
                FROM pg.bookings b
                JOIN pg.organizations o ON b.organization_id = o.id
                WHERE b.status = 'Cancelled'
                GROUP BY o.id
            )
            SELECT 
                t.name, 
                t.total_requests, 
                COALESCE(c.cancelled_requests, 0) as cancellations,
                (CAST(COALESCE(c.cancelled_requests, 0) AS FLOAT) / t.total_requests) * 100 as cancellation_rate_pct
            FROM org_totals t
            LEFT JOIN org_cancellations c ON t.id = c.id
            WHERE t.total_requests > 5
            ORDER BY cancellation_rate_pct DESC;
        """
        return self.conn.execute(query).df()



    def get_space_inefficiency(self, minimum_capacity: int = 50):

        """
        Large rooms that are rarely booked (wasted space)
        """

        query = """
            SELECT 
                r.building_name, 
                r.room_number, 
                r.capacity, 
                COUNT(b.id) as total_bookings
            FROM pg.rooms r
            LEFT JOIN pg.bookings b ON r.id = b.room_id AND b.status = 'Approved'
            GROUP BY r.building_name, r.room_number, r.capacity
            HAVING COUNT(b.id) < 5 AND r.capacity >= ?
            ORDER BY r.capacity DESC, total_bookings ASC;
        """
        return self.conn.execute(query, [minimum_capacity]).df()
    


    def get_peak_booking_days(self):

        """
        Highest number of bookings across days of the week
        """
        query = """
            SELECT 
                DAYNAME(start_time) as day_of_week,
                COUNT(*) as total_events,
                SUM(EXTRACT(EPOCH FROM (end_time - start_time))/3600) as total_hours
            FROM pg.bookings
            WHERE status = 'Approved'
            GROUP BY day_of_week
            ORDER BY total_events DESC;
        """
        return self.conn.execute(query).df()
    


    def get_retaliation_correlation(self, intervention_date: str = '2025-06-01'):
        """
        Correlation between Graffiti Club meetings and campus graffiti vandalism 
        (before and after administration "intervention")
        """

        query = """
            WITH monthly_incidents AS (
                SELECT 
                    DATE_TRUNC('month', reported_date) AS month, 
                    COUNT(*) AS incident_count
                FROM pg.incidents
                WHERE incident_type = 'Graffiti'
                GROUP BY 1
            ),
            monthly_meetings AS (
                SELECT 
                    DATE_TRUNC('month', b.start_time) AS month, 
                    COUNT(*) AS meeting_count
                FROM pg.bookings b
                JOIN pg.organizations o ON b.organization_id = o.id
                WHERE o.name = 'Graffiti Club' AND b.status = 'Approved'
                GROUP BY 1
            )
            SELECT 
                CAST(COALESCE(i.month, m.month) AS DATE) AS activity_month,
                COALESCE(i.incident_count, 0) AS graffiti_incidents,
                COALESCE(m.meeting_count, 0) AS club_meetings,
                CASE 
                    WHEN COALESCE(i.month, m.month) >= ?::DATE THEN 'Post-Intervention'
                    ELSE 'Pre-Intervention'
                END AS timeline_phase
            FROM monthly_incidents i
            FULL OUTER JOIN monthly_meetings m ON i.month = m.month
            ORDER BY activity_month;
        """
        
        # Executes perfectly because 1 placeholder (?) matches 1 parameter
        return self.conn.execute(query, [intervention_date]).df()