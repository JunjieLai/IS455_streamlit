import streamlit as st
import time
from datetime import datetime, timedelta

# Import utility functions and styles
from utils import call_stored_procedure, get_date_range
from styles import load_css

# Import different dashboards
from admin_dashboard import admin_dashboard
from finance_dashboard import finance_dashboard
from user_dashboard import user_dashboard
from marketing_dashboard import marketing_dashboard

# Function to initialize database connection based on user credentials
@st.cache_resource
def init_connection(username, password):
    """
    Connect to the database using credentials tied to the user's role
    """
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host="amazon-database-amazon-database.h.aivencloud.com",
            port='25693',
            user=username,
            password=password,
            database="amazon_database"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Initialize session state variables for authentication
def init_auth_state():
    """
    Set default session state for authentication and filters
    """
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ""
    if 'conn' not in st.session_state:
        st.session_state.conn = None
    if 'start_date' not in st.session_state:
        st.session_state.start_date = None
    if 'end_date' not in st.session_state:
        st.session_state.end_date = None

# Authentication function
def login(username, password):
    """
    Authenticate user credentials and set role-based session values
    """
    credentials = {
        "db_admin": "Admin@2025!Secure",
        "user_analyst": "UserTeam@2025!",
        "finance_analyst": "Finance@2025!Secure",
        "marketing_analyst": "Marketing@2025!Secure"
    }
    
    if username in credentials and password == credentials[username]:
        conn = init_connection(username, password)
        if conn:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.conn = conn

            if username == "db_admin":
                st.session_state.user_role = "admin_role"
            elif username == "user_analyst":
                st.session_state.user_role = "user_analyst_role"
            elif username == "finance_analyst":
                st.session_state.user_role = "finance_analyst_role"
            elif username == "marketing_analyst":
                st.session_state.user_role = "marketing_analyst_role"

            return True
    return False


# Logout and clear session state
def logout():
    """
    Log out the user and clean up session state
    """
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.user_role = ""
    if st.session_state.conn:
        st.session_state.conn.close()
    st.session_state.conn = None

# Display the login screen
def display_login_page():
    """
    Show the login UI and role instructions
    """
    st.markdown("<h1 class='main-header'>Amazon E-Commerce Analytics Platform</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center;'>
        <img src='https://www.prideindustries.com/wp-content/uploads/2021/06/Customer-logo_Amazon-1-1024x512.png.webp' width='300'>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        login_button = st.button("Login", use_container_width=True)

    if login_button:
        if login(username, password):
            st.success("Login successful! Redirecting...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Invalid username or password")

    with st.expander("Available Roles"):
        st.markdown("""
        - **Database Admin** (username: `db_admin`)
          - Full access to all dashboards
          - Admin@2025!Secure

        - **User Analyst** (username: `user_analyst`)
          - Access to user behavior and segmentation
          - UserTeam@2025!

        - **Finance Analyst** (username: `finance_analyst`)
          - Access to revenue and financial metrics
          - Finance@2025!Secure

        - **Marketing Analyst** (username: `marketing_analyst`)
          - Access to discount analysis and product performance
          - "Marketing@2025!Secure
        """)

    st.markdown("</div>", unsafe_allow_html=True)

# Sidebar with user info and date filter
def setup_sidebar():
    """
    Render sidebar with user info and global filters
    """
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}")
        st.markdown(f"<span class='role-tag'>{st.session_state.user_role}</span>", unsafe_allow_html=True)
        st.divider()

        st.subheader("Filters")
        min_date, max_date = get_date_range(st.session_state.conn)
        date_range = st.date_input(
            "Select Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )

        if len(date_range) == 2:
            st.session_state.start_date, st.session_state.end_date = date_range
        else:
            st.session_state.start_date, st.session_state.end_date = min_date.date(), max_date.date()

        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()

        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

# Main function that controls app flow
def main():
    """
    Launch the full Streamlit application
    """
    st.set_page_config(
        page_title="Amazon E-Commerce Analytics Platform",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    load_css()
    init_auth_state()

    if not st.session_state.authenticated:
        display_login_page()
    else:
        setup_sidebar()
        
        if st.session_state.user_role == "admin_role":
            admin_dashboard(st.session_state.conn, st.session_state.start_date, st.session_state.end_date)
        elif st.session_state.user_role == "user_analyst_role":
            user_dashboard(st.session_state.conn, st.session_state.start_date, st.session_state.end_date)
        elif st.session_state.user_role == "finance_analyst_role":
            finance_dashboard(st.session_state.conn, st.session_state.start_date, st.session_state.end_date)
        elif st.session_state.user_role == "marketing_analyst_role":
            marketing_dashboard(st.session_state.conn, st.session_state.start_date, st.session_state.end_date)

if __name__ == "__main__":
    main()