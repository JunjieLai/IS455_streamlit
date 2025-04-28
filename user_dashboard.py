import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def user_dashboard(conn, start_date, end_date):
    """
    Dashboard for analyzing user activity, retention, and regional distribution
    """
    st.markdown("<h1 class='main-header'>User Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    from utils import call_stored_procedure
    
    # =================================================
    # 1. Provincial User Analysis
    # =================================================
    st.subheader("User Distribution by Province")
    
    # Get provincial data
    province_data = call_stored_procedure(conn, "ProvincialUserAnalysis", [])
    df_province = pd.DataFrame(province_data)
    
    if province_data and len(province_data) > 0:

        # Create metrics
        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.metric("Total Provinces", f"{len(df_province)}")
        with metric_cols[1]:
            st.metric("Total Users", f"{df_province['UserCount'].sum():,}")
        with metric_cols[2]:
            st.metric("VIP Users", f"{df_province['VIPUserCount'].sum():,}")

        # Interactive elements - User Type Filter
        user_type = st.selectbox(
            "Select User Type", 
            ["All Users", "VIP Users Only", "Non-VIP Users Only"],
            index=0
        )

        # Filter data based on user type selection
        if user_type == "VIP Users Only":
            # Create a new dataframe with only VIP data
            df_filtered = df_province.copy()
            df_filtered["UserCount"] = df_filtered["VIPUserCount"]
            df_filtered = df_filtered[["Province", "UserCount", "TotalRevenue", "AvgOrderValue"]]
            title_suffix = "VIP Users"
        elif user_type == "Non-VIP Users Only":
            # Create a new dataframe with non-VIP data
            df_filtered = df_province.copy()
            df_filtered["UserCount"] = df_filtered["UserCount"] - df_filtered["VIPUserCount"]
            df_filtered = df_filtered[["Province", "UserCount", "TotalRevenue", "AvgOrderValue"]]
            title_suffix = "Non-VIP Users"
        else:
            # Use all users
            df_filtered = df_province[["Province", "UserCount", "TotalRevenue", "AvgOrderValue"]]
            title_suffix = "All Users"
        
        # Sort by user count
        df_filtered = df_filtered.sort_values(by="UserCount", ascending=False).head(10)
        
        # Create visualization
        st.markdown("##### Top 10 Provinces by User Count")
        
        fig = px.bar(
            df_filtered,
            x="Province",
            y="UserCount",
            color="Province",
            labels={"Province": "Province", "UserCount": "Number of Users"},
            height=500
        )
        
        fig.update_layout(
            xaxis={'categoryorder': 'total descending'},
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a map visualization placeholder
        st.markdown("### Geographic Distribution")
        
        # Interactive elements - Metric Selection for Map
        map_metric = st.radio(
            "Select Map Metric",
            ["User Count", "VIP Percentage", "Average Order Value", "Average Spend per User"],
            horizontal=True
        )
        
        # Map the selection to dataframe columns
        metric_mapping = {
            "User Count": "UserCount",
            "VIP Percentage": "VIPPercentage",
            "Average Order Value": "AvgOrderValue",
            "Average Spend per User": "AvgUserSpend"
        }
        
        selected_metric = metric_mapping[map_metric]
        
        # For a real implementation, replace this with a proper map visualization
        # This is a placeholder using a horizontal bar chart
        df_map = df_province.sort_values(by=selected_metric, ascending=False).head(10)
        
        fig = px.bar(
            df_map,
            y="Province",
            x=selected_metric,
            orientation='h',
            title=f"Top 10 Provinces by {map_metric}",
            color=selected_metric,
            color_continuous_scale="Viridis",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No provincial data available.")

    # =================================================
    # 3. VIP vs Non-VIP Comparison
    # =================================================
    st.markdown("<h2 class='sub-header'>VIP vs Non-VIP User Comparison</h2>", unsafe_allow_html=True)
    
    # Get VIP comparison data
    vip_data = call_stored_procedure(conn, "VIPUserComparison", [])
    
    if vip_data and len(vip_data) > 0:
        # The procedure returns two result sets
        df_vip_metrics = pd.DataFrame(vip_data)
        
        # Interactive element - Comparison Metric
        comparison_metric = st.selectbox(
            "Select Comparison Metric",
            ["User Count", "Orders per User", "Spending per User", "Average Order Value"],
            index=0
        )
        
        # Map selection to corresponding columns
        metric_mapping = {
            "User Count": "UserCount",
            "Orders per User": lambda df: df["TotalOrders"] / df["UserCount"],
            "Spending per User": "AvgSpentPerUser",
            "Average Order Value": "AvgOrderValue"
        }
        
        # Create a new dataframe with the selected metric
        df_compare = df_vip_metrics.copy()
        
        if callable(metric_mapping[comparison_metric]):
            df_compare["SelectedMetric"] = metric_mapping[comparison_metric](df_compare)
        else:
            df_compare["SelectedMetric"] = df_compare[metric_mapping[comparison_metric]]
        
        # Create comparison bar chart
        fig = px.bar(
            df_compare,
            x='UserType',
            y='SelectedMetric',
            color='UserType',
            color_discrete_map={'VIP': '#FF9900', 'Non-VIP': '#232F3E'},
            text='SelectedMetric',
            labels={'UserType': 'User Type', 'SelectedMetric': comparison_metric}
        )
        
        # Format the text labels based on the metric
        if comparison_metric == "User Count":
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        elif comparison_metric in ["Spending per User", "Average Order Value"]:
            fig.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
        else:
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        
        st.plotly_chart(fig, use_container_width=True)
    
    # =================================================
    # 4. User Retention Analysis
    # =================================================
    st.subheader("User Retention Analysis")

    # Get retention data
    retention_data = call_stored_procedure(conn, "UserRetentionAnalysis", [2024])
    
    if retention_data and len(retention_data) > 0:
        df_retention = pd.DataFrame(retention_data)
        
        # Filter out the total row for the chart
        df_chart = df_retention[~df_retention['RegMonth'].str.contains('-Total')]
        
        # Sort by month
        df_chart['MonthOrder'] = pd.to_datetime(df_chart['RegMonth'] + '-01')
        df_chart = df_chart.sort_values('MonthOrder')
        
        # Create dual-line chart for retention rates
        fig = go.Figure()
        
        # Add 7-day retention line
        fig.add_trace(go.Scatter(
            x=df_chart['RegMonth'],
            y=df_chart['Retention_7_Day'],
            name='7-Day Retention',
            line=dict(color='#36C2F6', width=3),
            mode='lines+markers'
        ))
        
        # Add 30-day retention line
        fig.add_trace(go.Scatter(
            x=df_chart['RegMonth'],
            y=df_chart['Retention_30_Day'],
            name='30-Day Retention',
            line=dict(color='#FF9900', width=3),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            xaxis_title='Registration Month',
            yaxis_title='Retention Rate (%)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Extract total retention data
        total_row = df_retention[df_retention['RegMonth'].str.contains('-Total')]
        
        if not total_row.empty:
            st.markdown(f"##### Annual Retention Summary")
            
            metric_cols = st.columns(3)
            
            with metric_cols[0]:
                st.metric("Total New Users", f"{int(total_row['UserCount'].iloc[0]):,}")
            
            with metric_cols[1]:
                st.metric("7-Day Retention Rate", f"{total_row['Retention_7_Day'].iloc[0]}%")
            
            with metric_cols[2]:
                st.metric("30-Day Retention Rate", f"{total_row['Retention_30_Day'].iloc[0]}%")

        else:
            st.info(f"No retention data available for 2024.")
    
    # =================================================
    # 2. User Activity Analysis
    # =================================================
    st.subheader("User Activity Analysis")
    
    # Get activity data
    activity_data = call_stored_procedure(conn, "UserActivityAnalysis", [])
    
    if activity_data and len(activity_data) > 0:
        df_activity = pd.DataFrame(activity_data)
        
        # Sort to get consistent order
        activity_order = ['Active', 'Silent', 'Lost', 'No Orders']
        df_activity['SortOrder'] = df_activity['ActivityLabel'].apply(
            lambda x: activity_order.index(x) if x in activity_order else len(activity_order)
        )
        df_activity = df_activity.sort_values('SortOrder')
        
        # Create consistent color mapping
        color_map = {
            'Active': '#36C2F6',
            'Silent': '#FF9900',
            'Lost': '#E41F1F',
            'No Orders': '#9E9E9E'
        }

        # Create visualization
        fig = px.pie(
            df_activity,
            values='UserCount',
            names='ActivityLabel',
            color='ActivityLabel',
            color_discrete_map=color_map,
            hole=0.4
        )
            
        fig.update_traces(textposition='inside', textinfo='percent+label')       
        st.plotly_chart(fig, use_container_width=True)

        # Create metrics
        metric_cols = st.columns(4)
        
        for i, label in enumerate(['Active', 'Silent', 'Lost', 'No Orders']):
            with metric_cols[i]:
                if label in df_activity['ActivityLabel'].values:
                    user_count = df_activity[df_activity['ActivityLabel'] == label]['UserCount'].iloc[0]
                    st.metric(f"{label} Users", f"{int(user_count):,}")
                else:
                    st.metric(f"{label} Users", "0", "0%")
        

    else:
        st.info("No user activity data available.")