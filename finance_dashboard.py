import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

def finance_dashboard(conn, start_date, end_date):
    """
    Dashboard for analyzing financial metrics, revenue trends, and payment methods
    """
    st.markdown("<h1 class='main-header'>Finance Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    from utils import call_stored_procedure
    
    # =================================================
    # 1. Monthly Revenue Trend
    # =================================================
    st.subheader("Monthly Revenue Trend")
    
    # Get revenue data
    revenue_data = call_stored_procedure(conn, "MonthlyRevenueTrendAnalysis", [])
    
    if revenue_data and len(revenue_data) > 0:
        df_revenue = pd.DataFrame(revenue_data)
        
        # Convert Month to datetime for proper sorting
        df_revenue['MonthDate'] = pd.to_datetime(df_revenue['Month'] + '-01')
        df_revenue = df_revenue.sort_values('MonthDate')
        
        # Calculate month-over-month growth rate
        df_revenue['PrevRevenue'] = df_revenue['TotalRevenue'].shift(1)
        df_revenue['MonthlyGrowth'] = (
            (df_revenue['TotalRevenue'] - df_revenue['PrevRevenue']) / 
            df_revenue['PrevRevenue'].replace(0, np.nan) * 100
        )
        
        # Display summary metrics
        total_revenue = df_revenue['TotalRevenue'].sum()
        avg_monthly_revenue = df_revenue['TotalRevenue'].mean()
        
        if len(df_revenue) >= 2:
            latest_growth = df_revenue['MonthlyGrowth'].iloc[-1]
        else:
            latest_growth = None
        
        metric_cols = st.columns(3)
        
        with metric_cols[0]:
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        
        with metric_cols[1]:
            st.metric("Avg Monthly Revenue", f"${avg_monthly_revenue:,.2f}")
        
        with metric_cols[2]:
            if latest_growth is not None:
                # Show positive growth in green, negative in red
                delta_color = "normal" if latest_growth >= 0 else "inverse"
                st.metric("Latest Monthly Growth",
                         f"{latest_growth:.2f}%", 
                         delta_color=delta_color)
            else:
                st.metric("Latest Monthly Growth", "N/A")
        
        # Create a dual-axis line chart
        fig = go.Figure()
        
        # Total revenue trend line
        fig.add_trace(go.Scatter(
            x=df_revenue['Month'],
            y=df_revenue['TotalRevenue'],
            mode='lines+markers',
            name='Revenue',
            line=dict(color='#FF9900', width=3),
            fill='tozeroy',
            fillcolor='rgba(255, 153, 0, 0.2)'
        ))
        
        # Add growth rate line (secondary y-axis)
        if len(df_revenue) >= 2:
            fig.add_trace(go.Scatter(
                x=df_revenue['Month'][1:],  # Skip first month (no growth data)
                y=df_revenue['MonthlyGrowth'][1:],
                mode='lines+markers',
                name='Monthly Growth (%)',
                line=dict(color='#36C2F6', width=2, dash='dot'),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title='Monthly Revenue Trend and Growth Rate',
                xaxis=dict(title='Month'),
                yaxis=dict(
                    title='Revenue ($)',
                    titlefont=dict(color='#FF9900'),
                    tickfont=dict(color='#FF9900')
                ),
                yaxis2=dict(
                    title='Growth Rate (%)',
                    titlefont=dict(color='#36C2F6'),
                    tickfont=dict(color='#36C2F6'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                height=500
            )
        else:
            fig.update_layout(
                title='Monthly Revenue Trend',
                xaxis=dict(title='Month'),
                yaxis=dict(title='Revenue ($)'),
                height=500
            )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # =================================================
    # 2. Payment Method Analysis
    # =================================================
    st.subheader("Payment Method Analysis")
    
    # Interactive element - Visualization Type
    viz_type = st.radio(
        "Select Visualization",
        ["Payment Method Distribution", "Success Rate Comparison"],
        horizontal=True,
        key="payment_viz_type"
    )
    
    # Get payment method data
    payment_data = call_stored_procedure(conn, "PaymentMethodAnalysis", [])
    
    if payment_data and len(payment_data) > 0:
        df_payment = pd.DataFrame(payment_data)
        
        if viz_type == "Payment Method Distribution":
            # Create pie chart of payment method distribution
            fig = px.pie(
                df_payment,
                values='TotalPayments',
                names='PaymentType',
                hover_data=['SuccessRate'],
                labels={'SuccessRate': 'Success Rate (%)'},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:  # Success Rate Comparison
            # Sort by success rate
            df_payment = df_payment.sort_values('SuccessRate', ascending=False)
            
            # Create a bar chart for success rates
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df_payment['PaymentType'],
                y=df_payment['SuccessRate'],
                name='Success Rate',
                marker_color='#36C2F6',
                text=df_payment['SuccessRate'].apply(lambda x: f"{x:.2f}%"),
                textposition='outside'
            ))
            
            # Add a line for total payments
            fig.add_trace(go.Scatter(
                x=df_payment['PaymentType'],
                y=df_payment['TotalPayments'],
                name='Total Payments',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='#FF9900', width=3)
            ))
            
            fig.update_layout(
                xaxis=dict(title='Payment Method'),
                yaxis=dict(
                    title='Success Rate (%)',
                    titlefont=dict(color='#36C2F6'),
                    tickfont=dict(color='#36C2F6'),
                    range=[0, 100]
                ),
                yaxis2=dict(
                    title='Total Payments',
                    titlefont=dict(color='#FF9900'),
                    tickfont=dict(color='#FF9900'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                height=555
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.info("No payment method data available.")

    # =================================================
    # 3. Failed Payments Analysis
    # =================================================
    st.subheader("Failed Payments Analysis")

    # Get failed payments data
    failed_payments_data = call_stored_procedure(conn, "FailedPaymentsAnalysis", [2024])

    # Create DataFrames from the unique structure
    try:
        # First, create empty lists to store the data
        dates = []
        payments = []
        
        # Extract data from all result sets (daily data)
        for item in failed_payments_data:
            if isinstance(item, dict):
                # If it's a dictionary, extract values directly
                if 'FailedDate' in item and 'FailedPayments' in item:
                    dates.append(item['FailedDate'])
                    payments.append(item['FailedPayments'])
            elif isinstance(item, list) and len(item) > 0:
                # If it's a list, extract values from first item
                if isinstance(item[0], dict):
                    if 'FailedDate' in item[0] and 'FailedPayments' in item[0]:
                        dates.append(item[0]['FailedDate'])
                        payments.append(item[0]['FailedPayments'])
        
        # Create DataFrame for daily data
        df_daily = pd.DataFrame({
            'FailedDate': dates,
            'FailedPayments': payments
        })
        
        # Ensure dates are in correct format
        df_daily['FailedDate'] = pd.to_datetime(df_daily['FailedDate'])
        
        # Sort by date
        df_daily = df_daily.sort_values('FailedDate')
        
        # Create top 10 data by sorting by failed payments count
        df_top10 = df_daily.sort_values('FailedPayments', ascending=False).head(10)
        
        # Create visualizations
        if not df_daily.empty:
            # Add month and quarter columns for aggregation
            df_daily['Month'] = df_daily['FailedDate'].dt.strftime('%Y-%m')
            df_daily['Quarter'] = df_daily['FailedDate'].dt.to_period('Q').astype(str)
            
            # Group by month and quarter
            df_monthly = df_daily.groupby('Month')['FailedPayments'].sum().reset_index()
            df_quarterly = df_daily.groupby('Quarter')['FailedPayments'].sum().reset_index()
            
            # Create tabs
            tabs = st.tabs(["Daily View", "Monthly View", "Quarterly View", "Top Problem Days"])
            
            # Tab 1: Daily view
            with tabs[0]:
                fig = px.line(
                    df_daily,
                    x='FailedDate',
                    y='FailedPayments',
                    title='Daily Failed Payments (2024)',
                    labels={'FailedDate': 'Date', 'FailedPayments': 'Failed Payments'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Tab 2: Monthly view
            with tabs[1]:
                # Create a bar chart with line overlay
                fig = go.Figure()
                
                # Add bars for monthly failed payments
                fig.add_trace(go.Bar(
                    x=df_monthly['Month'],
                    y=df_monthly['FailedPayments'],
                    name='Failed Payments',
                    marker_color='#e41a1c',
                    text=df_monthly['FailedPayments'],
                    textposition='outside'
                ))
                
                # Add line for trend
                fig.add_trace(go.Scatter(
                    x=df_monthly['Month'],
                    y=df_monthly['FailedPayments'],
                    mode='lines+markers',
                    name='Trend',
                    line=dict(color='#377eb8', width=2),
                    marker=dict(color='#377eb8', size=8)
                ))
                
                fig.update_layout(
                    title='Monthly Failed Payments (2024)',
                    xaxis=dict(title='Month'),
                    yaxis=dict(title='Failed Payments'),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Tab 3: Quarterly view (new)
            with tabs[2]:
                # Create a bar chart with line overlay for quarterly data
                fig = go.Figure()
                
                # Add bars for quarterly failed payments
                fig.add_trace(go.Bar(
                    x=df_quarterly['Quarter'],
                    y=df_quarterly['FailedPayments'],
                    name='Failed Payments',
                    marker_color='#e41a1c',
                    text=df_quarterly['FailedPayments'],
                    textposition='outside'
                ))
                
                # Add line for trend
                fig.add_trace(go.Scatter(
                    x=df_quarterly['Quarter'],
                    y=df_quarterly['FailedPayments'],
                    mode='lines+markers',
                    name='Trend',
                    line=dict(color='#377eb8', width=2),
                    marker=dict(color='#377eb8', size=8)
                ))
                
                fig.update_layout(
                    title='Quarterly Failed Payments (2024)',
                    xaxis=dict(title='Quarter'),
                    yaxis=dict(title='Failed Payments'),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Tab 4: Top 10 - Improved visualization
            with tabs[3]:
                # Format the dates for better display
                df_top10['FormattedDate'] = df_top10['FailedDate'].dt.strftime('%b %d, %Y')
                
                # Add a column for bar coloring intensity
                max_failures = df_top10['FailedPayments'].max()
                df_top10['FailurePercentage'] = (df_top10['FailedPayments'] / max_failures) * 100
                
                # Sort by failures descending
                df_top10 = df_top10.sort_values('FailedPayments', ascending=False)
                
                # Create a horizontal bar chart for better visibility
                fig = px.bar(
                    df_top10,
                    y='FormattedDate',
                    x='FailedPayments',
                    orientation='h',
                    title='Top 10 Days with Most Failed Payments (2024)',
                    labels={'FormattedDate': 'Date', 'FailedPayments': 'Failed Payments'},
                    text='FailedPayments',
                    color='FailurePercentage',
                    color_continuous_scale='Reds',
                    height=600
                )
                
                # Improve text positioning and size
                fig.update_traces(
                    texttemplate='%{text}', 
                    textposition='outside',
                    textfont=dict(size=14)
                )
                
                # Improve layout to make dates more readable
                fig.update_layout(
                    yaxis=dict(
                        title='',
                        autorange="reversed",  # Reverse y-axis to have highest at top
                        tickfont=dict(size=14)
                    ),
                    xaxis=dict(title='Number of Failed Payments'),
                    coloraxis_showscale=False,  # Hide the color scale
                    margin=dict(l=150)  # Add more margin on the left for dates
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Display summary metrics            
            total_failed = df_daily['FailedPayments'].sum()
            avg_daily_failed = df_daily['FailedPayments'].mean()
            max_failed_day = df_daily.loc[df_daily['FailedPayments'].idxmax()]
            
            cols = st.columns(3)
            with cols[0]:
                st.metric("Total Failed Payments", f"{total_failed:,}")
            with cols[1]:
                st.metric("Avg Daily Failed Payments", f"{avg_daily_failed:.2f}")
            with cols[2]:
                st.metric("Worst Day", 
                    f"{max_failed_day['FailedDate'].strftime('%b %d, %Y')}: {max_failed_day['FailedPayments']:,}")
            
    except Exception as e:
        st.error(f"Error processing data: {e}")
        st.write("Error details:", e.__class__.__name__)
        import traceback
        st.code(traceback.format_exc())
    
    # =================================================
    # 4. User Spending Tiers Analysis
    # =================================================
    st.subheader("User Spending Tiers")
    
    # Get user tier data
    tier_data = call_stored_procedure(conn, "UserTierAnalysis", [])
    
    if tier_data and len(tier_data) > 0:
        df_tiers = pd.DataFrame(tier_data)
        
        # Calculate percentages
        total_users = df_tiers['UserCount'].sum()
        df_tiers['Percentage'] = (df_tiers['UserCount'] / total_users * 100).round(2)
        
        # Create consistent color mapping for tiers
        color_map = {
            'Platinum': '#B0B0B0',  # Silver-gray
            'Gold': '#FFD700',      # Gold
            'Silver': '#C0C0C0',    # Silver
            'Bronze': '#CD7F32'     # Bronze
        }
        
        # Create pie chart visualization
        fig = px.pie(
            df_tiers,
            values='UserCount',
            names='UserTier',
            color='UserTier',
            color_discrete_map=color_map,
            hover_data=['Percentage'],
            labels={'Percentage': 'Percentage (%)'}
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display tier metrics
        metric_cols = st.columns(4)
        
        tier_names = ['Platinum', 'Gold', 'Silver', 'Bronze']
        
        for i, tier in enumerate(tier_names):
            with metric_cols[i]:
                if tier in df_tiers['UserTier'].values:
                    tier_row = df_tiers[df_tiers['UserTier'] == tier].iloc[0]
                    count = tier_row['UserCount']
                    percentage = tier_row['Percentage']
                    st.metric(f"{tier} Users", f"{int(count):,}")
                else:
                    st.metric(f"{tier} Users", "0", "0%")
    else:
        st.info("No user tier data available.")