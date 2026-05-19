import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# CUSTOM ARCHITECTURE MODULES
from database import SessionLocal
from dal import BookingRepository
from analytics import AnalyticsEngine


# --- Architecture & DAL: Caching the Engine ---
@st.cache_resource
def get_analytics_engine():
    """CACHING OF ANALYTICS ENGINE"""
    return AnalyticsEngine()


# INITIALIZATION OF DATA ACCESS LAYERS (Clean, leak-proof allocation)
db_session = SessionLocal()
repo = BookingRepository(db_session)
analytics = get_analytics_engine()


# --- UI Setup ---
st.set_page_config(page_title="Campus Booking System", layout="wide")
st.title("Smart Campus Room & Event Booking")

# DATA FETCH FROM DATABASE
available_rooms = repo.get_all_rooms()

# DATA FETCH FROM DAL
available_orgs = repo.get_all_organizations()

tab1, tab2 = st.tabs(["BOOKING", "Analytical Dashboard"])


# ========================================================
# TAB 1: The Transactional Demo (Golden Path & Edge Case)
# ========================================================

with tab1:
    st.header("Make a Reservation")
    st.markdown("This interface interacts strictly with the PostgreSQL database via the `BookingRepository`.")
    
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            selected_room_id = st.selectbox(
                "Select Room", 
                options=[r.id for r in available_rooms],
                format_func=lambda x: next(f"{r.building_name} - {r.room_number} (Cap: {r.capacity})" for r in available_rooms if r.id == x)
            )
            
            selected_org_id = st.selectbox(
                "Select Organization", 
                options=[o.id for o in available_orgs],
                format_func=lambda x: next(o.name for o in available_orgs if o.id == x)
            )

        with col2:
            start_date = st.date_input("Date", value=datetime.today())
            start_time = st.time_input("Start Time", value=datetime.strptime("14:00", "%H:%M").time())
            duration = st.number_input("Duration (Hours)", min_value=1, max_value=8, value=2)
            
        submit_button = st.form_submit_button(label="Submit Booking")

        if submit_button:
            # DATETIME OBJECT CREATION
            dt_start = datetime.combine(start_date, start_time)
            dt_end = dt_start + timedelta(hours=duration)
            
            try:
                # CREATE BOOKING (Golden Path)
                booking = repo.create_booking(
                    room_id=selected_room_id,
                    organization_id=selected_org_id,
                    start_time=dt_start,
                    end_time=dt_end
                )
                st.success(f"Success! Booked Room ID {booking.room_id} from {dt_start} to {dt_end}.")
                st.balloons()

            except ValueError as e:
                # BOOKING REJECTION (Edge Case: Double-Booking Prevention)
                st.error(f"Booking Rejected: {str(e)}")


# ==========================================
# TAB 2: The Analytics Engine (DuckDB)
# ==========================================

with tab2:
    st.header("System Analytics")
    
    st.subheader("1. Highest-Demand Spaces")
    st.markdown("Ranks rooms by total hours booked using window functions.")

    try:
        ranking_df = analytics.get_utilization_ranking()
        # UPDATED: Replaced use_container_width with width='stretch'
        st.dataframe(ranking_df, width='stretch')
    except Exception as e:
        st.error(f"Could not load ranking: {e}")

    st.divider()

    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("2. Hoarding Analysis")
        st.markdown("Organizations with high cancellation rates.")

        try:
            hoarding_df = analytics.get_hoarding_analysis()
            # UPDATED: Replaced use_container_width with width='stretch'
            st.dataframe(hoarding_df, width='stretch')
        except Exception as e:
             st.error(f"Could not load hoarding analysis: {e}")
             
    with col_b:
        st.subheader("3. Peak Days")
        st.markdown("Total hours booked across the week.")

        try:
            peak_df = analytics.get_peak_booking_days()
            st.bar_chart(peak_df.set_index('day_of_week')['total_hours'])
        except Exception as e:
             st.error(f"Could not load peak days: {e}")
             
    # ============================================
    # 4. Incident Response & Retaliation Analysis
    # ============================================
    st.divider()
    
    st.subheader("4. Graffiti Frequency Correlation")
    st.markdown("Campus vandalism reports before and after administrative intervention (June 2025)")

    try:
        # THRESHOLD
        intervention_date = '2025-06-01'
        
        # DATA RETRIEVAL
        incident_correlation_df = analytics.get_retaliation_correlation(intervention_date)
        
        if not incident_correlation_df.empty:
            col_chart, col_data = st.columns([2, 1])
            
            with col_chart:
                st.line_chart(incident_correlation_df.set_index('activity_month')['graffiti_incidents'])
                
            with col_data:
                # UPDATED: Replaced use_container_width with width='stretch'
                st.dataframe(incident_correlation_df, width='stretch')
        else:
            st.info("No incident correlation data available for the specified timeframe.")

    except Exception as e:
        st.error(f"Failed to load incident analytics: {str(e)}")


db_session.close()