import streamlit as st

# Load CSS styles
def load_css():
    """
    Load custom CSS styles for the application
    """
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #FF9900;
            text-align: center;
            margin-bottom: 1rem;
            font-weight: bold;
        }
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            background-color: #f9f9f9;
            box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        }
        .sub-header {
            font-size: 1.5rem;
            color: #232F3E;
            margin-bottom: 1rem;
            font-weight: bold;
        }
        .card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f9f9f9;
            box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
            margin-bottom: 1.5rem;
        }
        .metric-container {
            display: flex;
            justify-content: space-evenly;
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 0.15rem 0.5rem 0 rgba(58, 59, 69, 0.15);
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #FF9900;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #232F3E;
        }
        .role-tag {
            background-color: #FF9900;
            color: white;
            padding: 0.3rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }
        
        /* Custom styles for dashboard elements */
        .stPlotlyChart {
            background-color: white;
            border-radius: 0.5rem;
            padding: 0.5rem;
            box-shadow: 0 0.1rem 0.25rem 0 rgba(58, 59, 69, 0.1);
        }
        
        .stMetric {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 0.1rem 0.25rem 0 rgba(58, 59, 69, 0.1);
        }
        
        /* Footer style */
        .footer {
            text-align: center;
            padding-top: 2rem;
            margin-top: 2rem;
            color: #6c757d;
            font-size: 0.9rem;
            border-top: 1px solid #e9ecef;
        }
    </style>
    """, unsafe_allow_html=True)