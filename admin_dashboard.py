import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

def admin_dashboard(conn, start_date, end_date):
    """
    Admin dashboard showing comprehensive business analytics
    """
    st.markdown("<h1 class='main-header'>Overall View Dashboard</h1>", unsafe_allow_html=True)

    # Sidebar additional filters for admin dashboard
    st.sidebar.markdown("### Admin Dashboard Filters")
    refresh_frequency = st.sidebar.selectbox(
        "Dashboard Refresh Frequency", 
        ["Real-time", "Daily", "Weekly"],
        index=0
    )
    
    # ==================================================
    # Section 1: Business Overview Dashboard
    # ==================================================
    st.subheader("Business Overview")
    
    from utils import call_stored_procedure
    overview_data = call_stored_procedure(conn, "admin_business_overview", [start_date, end_date])
    
    if overview_data:
        data = overview_data[0]
        
        # Get historical data for trends (last 6 months)
        six_months_ago = (datetime.strptime(str(start_date), '%Y-%m-%d') - timedelta(days=180)).date()
        historical_data = call_stored_procedure(conn, "admin_business_growth_trajectory", 
                                              [six_months_ago, end_date])
        
        if historical_data:
            hist_df = pd.DataFrame(historical_data)
            # Convert 'Month' to datetime for proper sorting
            hist_df['Month'] = pd.to_datetime(hist_df['Month'] + '-01')
            hist_df = hist_df.sort_values('Month')
            
            # Calculate month-over-month changes
            if len(hist_df) > 1:
                revenue_change = ((hist_df['Revenue'].iloc[-1] / hist_df['Revenue'].iloc[-2]) - 1) * 100
                orders_change = ((hist_df['OrderCount'].iloc[-1] / hist_df['OrderCount'].iloc[-2]) - 1) * 100
                customers_change = ((hist_df['UniqueCustomers'].iloc[-1] / hist_df['UniqueCustomers'].iloc[-2]) - 1) * 100
                aov_change = ((hist_df['AvgOrderValue'].iloc[-1] / hist_df['AvgOrderValue'].iloc[-2]) - 1) * 100
            else:
                revenue_change = orders_change = customers_change = aov_change = 0
        else:
            revenue_change = orders_change = customers_change = aov_change = 0
        
        # KPI Cards row 1
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", f"{int(data['TotalUsers'])}")
        
        with col2:
            st.metric("Total Orders", 
                    f"{int(data['TotalOrders']) if data['TotalOrders'] else 0}",
                    f"{orders_change:.1f}%" if orders_change else None,
                    delta_color="normal")
        
        with col3:
            st.metric("Total Revenue", 
                    f"${data['TotalRevenue']/1000:,.2f}K" if data['TotalRevenue'] else "$0.00",
                    f"{revenue_change:.1f}%" if revenue_change else None,
                    delta_color="normal")
        
        with col4:
            st.metric("Avg Order Value", 
                    f"${data['AvgOrderValue']:,.2f}" if data['AvgOrderValue'] else "$0.00",
                    f"{aov_change:.1f}%" if aov_change else None,
                    delta_color="normal")
        
        # KPI Cards row 2
        col5, col6 = st.columns(2)
        
        with col5:
            st.metric("Total Products", 
                    f"{int(data['TotalProducts'])}")
        
        with col6:
            st.metric("Order Completion Rate", 
                    f"{data['OrderCompletionRate']:.1f}%" if data['OrderCompletionRate'] else "0%")

    # ==================================================
    # Section 4: Business Growth Trajectory
    # ==================================================
    st.subheader("Business Growth Trajectory")
    
    # Determine time range for growth analysis
    growth_start_date = (datetime.strptime(str(start_date), '%Y-%m-%d') - timedelta(days=365)).date()
    growth_data = call_stored_procedure(conn, "admin_business_growth_trajectory", 
                                       [growth_start_date, end_date])
    
    if growth_data:
        growth_df = pd.DataFrame(growth_data)
        growth_df['Month'] = pd.to_datetime(growth_df['Month'] + '-01')
        growth_df = growth_df.sort_values('Month')
        
        # Select metrics to display
        metric_columns = {
            "Order Count": "OrderCount",
            "Unique Customers": "UniqueCustomers", 
            "Revenue": "Revenue",
            "Avg Order Value": "AvgOrderValue",
            "Revenue Per Customer": "RevenuePerCustomer",
            "Orders Per 100 Users": "OrdersPerHundredUsers"
        }
        
        selected_metrics = st.multiselect(
            "Select Metrics to Display:",
            options=list(metric_columns.keys()),
            default=["Revenue", "Order Count", "Unique Customers"]
        )
        
        if selected_metrics:
            # Create multi-line chart for selected metrics
            fig = go.Figure()
            
            # Need to create multiple y-axes for different scales
            for i, metric in enumerate(selected_metrics):
                metric_col = metric_columns[metric]
                
                # Determine if this metric should use secondary y-axis
                if metric in ["Revenue"]:
                    yaxis = 'y'
                    line_style = dict(width=3)
                    opacity = 1.0
                else:
                    yaxis = 'y2'
                    line_style = dict(width=2, dash='dot')
                    opacity = 0.8
                
                fig.add_trace(
                    go.Scatter(
                        x=growth_df['Month'], 
                        y=growth_df[metric_col],
                        name=metric,
                        line=line_style,
                        opacity=opacity,
                        yaxis=yaxis
                    )
                )
            
            # Update layout with double y-axis
            fig.update_layout(
                xaxis_title="Month",
                yaxis=dict(
                    title="Revenue ($)",
                    titlefont=dict(color="#1f77b4"),
                    tickfont=dict(color="#1f77b4")
                ),
                yaxis2=dict(
                    title="Count",
                    titlefont=dict(color="#ff7f0e"),
                    tickfont=dict(color="#ff7f0e"),
                    anchor="x",
                    overlaying="y",
                    side="right"
                ),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    # ==================================================
    # Section 2: Product Performance Analysis
    # ==================================================
    st.subheader("Product Performance Analysis")

    # Get all product categories for filter
    categories_query = """
    SELECT DISTINCT Category FROM Product 
    ORDER BY Category
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute(categories_query)
    categories = cursor.fetchall()
    cursor.close()

    # Create multiselect with categories - DEFAULT ALL SELECTED
    if categories:
        category_options = [cat['Category'] for cat in categories]
        selected_categories = st.multiselect(
            "Select Product Categories",
            options=category_options,
            default=category_options  # Default: ALL categories selected
        )
        
        # Format categories for SQL query
        if selected_categories:
            categories_str = "'" + "','".join(selected_categories) + "'"
            
            # Call product performance procedure with category filter
            product_data = call_stored_procedure(conn, "admin_product_performance", 
                                            [start_date, end_date, categories_str])
            
            if product_data:
                df_products = pd.DataFrame(product_data)
                
                # ROW 1: Category Comparison Table
                st.markdown("##### Category Performance Comparison")

                # Aggregate data by category
                category_metrics = df_products.groupby('Category').agg({
                    'OrderCount': 'sum',
                    'TotalQuantitySold': 'sum',
                    'TotalRevenue': 'sum',
                    'AvgSellingPrice': 'mean',
                    'AvgDiscountPercentage': 'mean'
                }).reset_index()

                # Find max and min indices for each metric
                max_indices = {
                    'OrderCount': category_metrics['OrderCount'].idxmax(),
                    'TotalQuantitySold': category_metrics['TotalQuantitySold'].idxmax(),
                    'TotalRevenue': category_metrics['TotalRevenue'].idxmax(),
                    'AvgSellingPrice': category_metrics['AvgSellingPrice'].idxmax(),
                }

                min_indices = {
                    'OrderCount': category_metrics['OrderCount'].idxmin(),
                    'TotalQuantitySold': category_metrics['TotalQuantitySold'].idxmin(),
                    'TotalRevenue': category_metrics['TotalRevenue'].idxmin(),
                    'AvgSellingPrice': category_metrics['AvgSellingPrice'].idxmin(),
                }

                # For discount, reverse the color logic (lower discount is better for profitability)
                max_indices['AvgDiscountPercentage'] = category_metrics['AvgDiscountPercentage'].idxmin()
                min_indices['AvgDiscountPercentage'] = category_metrics['AvgDiscountPercentage'].idxmax()

                # Create a styled dataframe with color highlighting
                # Rename columns for display
                styled_df = category_metrics.rename(columns={
                    'Category': 'Product Category',
                    'OrderCount': 'Order Count',
                    'TotalQuantitySold': 'Units Sold',
                    'TotalRevenue': 'Revenue',
                    'AvgSellingPrice': 'Avg Price',
                    'AvgDiscountPercentage': 'Avg Discount'
                })

                # Define a styling function
                def highlight_max_min(s, props=''):
                    col_name = s.name
                    original_col = {
                        'Order Count': 'OrderCount',
                        'Units Sold': 'TotalQuantitySold',
                        'Revenue': 'TotalRevenue',
                        'Avg Price': 'AvgSellingPrice',
                        'Avg Discount': 'AvgDiscountPercentage'
                    }.get(col_name)
                    
                    if original_col is None:
                        return [''] * len(s)
                    
                    # Get the corresponding indices in the original dataframe
                    max_idx = max_indices.get(original_col)
                    min_idx = min_indices.get(original_col)
                    
                    styles = [''] * len(s)
                    for i in range(len(s)):
                        if i == max_idx:
                            styles[i] = 'background-color: #FF4136; color: white; font-weight: bold'
                        elif i == min_idx:
                            styles[i] = 'background-color: #2ECC40; color: white; font-weight: bold'
                    return styles

                # Format values
                def format_values(df):
                    # Create a copy to avoid modifying the original
                    formatted = df.copy()
                    
                    # Apply formatting to numeric columns
                    formatted['Revenue'] = formatted['Revenue'].apply(lambda x: f"${x:,.2f}")
                    formatted['Avg Price'] = formatted['Avg Price'].apply(lambda x: f"${x:.2f}")
                    formatted['Avg Discount'] = formatted['Avg Discount'].apply(lambda x: f"{x:.1f}%")
                    formatted['Order Count'] = formatted['Order Count'].apply(lambda x: f"{int(x)}")
                    formatted['Units Sold'] = formatted['Units Sold'].apply(lambda x: f"{int(x)}")
                    
                    return formatted

                # Format values first
                formatted_df = format_values(styled_df)

                # Apply styling
                styled_table = styled_df.style.apply(highlight_max_min, axis=0)

                # Set precision for numeric columns 
                styled_table = styled_table.format({
                    'Revenue': '${:,.2f}',
                    'Avg Price': '${:.2f}',
                    'Avg Discount': '{:.1f}%',
                    'Order Count': '{:,}',
                    'Units Sold': '{:,}'
                })

                # Apply additional styling for table consistency
                styled_table = styled_table.set_properties(**{
                    'border': '1px solid #ddd',
                    'padding': '8px',
                    'text-align': 'right'
                })

                # Make the table responsive
                st.markdown(
                    """
                    <style>
                    .dataframe {
                        width: 200% !important;
                        margin-bottom: 20px;
                        border-collapse: collapse;
                    }
                    .dataframe th, .dataframe td {
                        padding: 8px;
                        text-align: right;
                        border: 1px solid #ddd;
                    }
                    .dataframe th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                        text-align: center;
                    }
                    .dataframe tr:nth-child(even) {
                        background-color: #f9f9f9;
                    }
                    .dataframe tr:hover {
                        background-color: #f0f0f0;
                    }
                    </style>
                    """, 
                    unsafe_allow_html=True
                )

                # Display the table
                # Display the table with index=False instead of hide_index()
                st.write(styled_table.set_table_attributes('style="width: 200%"'), unsafe_allow_html=True)
                
                # ROW 2: Product Ranking Chart
                st.markdown("##### Top Products Performance")
                
                # Define metrics for product comparison
                product_metric_options = {
                    "Total Revenue": "TotalRevenue",
                    "Units Sold": "TotalQuantitySold", 
                    "Average Price": "AvgSellingPrice"
                }
                
                product_selected_metric = st.radio(
                    "Display Product Metric:", 
                    options=list(product_metric_options.keys()),
                    horizontal=True
                )
                
                product_metric_col = product_metric_options[product_selected_metric]
                
                # Sort by selected metric
                df_chart = df_products.sort_values(by=product_metric_col, ascending=False).head(10)
                
                # Create horizontal bar chart for products
                fig_products = px.bar(
                    df_chart,
                    y='ProductName',
                    x=product_metric_col,
                    color='Category',
                    labels={
                        'ProductName': 'Product',
                        'TotalRevenue': 'Revenue ($)',
                        'TotalQuantitySold': 'Units Sold',
                        'AvgSellingPrice': 'Avg Price ($)'
                    },
                    title=f'Top 10 Products by {product_selected_metric}',
                    orientation='h',
                    height=500,
                    text=product_metric_col
                )
                
                fig_products.update_traces(texttemplate='%{text:.2s}', textposition='outside')
                fig_products.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                
                st.plotly_chart(fig_products, use_container_width=True)
        else:
            st.info("Please select at least one product category.")
    
    # ==================================================
    # Section 3: Market Penetration by Region
    # ==================================================
    st.subheader("Regional Market Analysis")
    
    region_data = call_stored_procedure(conn, "admin_market_penetration_by_region", [start_date, end_date])
    
    if region_data:
        df_region = pd.DataFrame(region_data)
        
        # Create metric selector
        metric_options = {
            "Total Revenue": "TotalRevenue",
            "Market Share %": "MarketSharePercent",
            "Total Users": "TotalUsers",
            "Total Orders": "TotalOrders",
            "Revenue Per User": "RevenuePerUser"
        }
        
        selected_metric = st.selectbox(
            "Select Map Visualization Metric:",
            options=list(metric_options.keys())
        )
        
        metric_col = metric_options[selected_metric]
        
        # Create map visualization
        # Note: In a real implementation, you would import a proper China province GeoJSON
        # For this example, we'll use a bar chart as a placeholder
        
        fig = px.bar(
            df_region.sort_values(by=metric_col, ascending=False).head(10),
            x='Province',
            y=metric_col,
            color='MarketSharePercent',
            labels={
                'Province': 'Province',
                'TotalRevenue': 'Revenue ($)',
                'MarketSharePercent': 'Market Share (%)',
                'TotalUsers': 'Total Users',
                'TotalOrders': 'Total Orders',
                'RevenuePerUser': 'Revenue Per User ($)'
            },
            title=f'Top 10 Provinces by {selected_metric}',
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Data comparison section
        st.markdown("##### Regional Comparison")
        
        # Allow selecting provinces to compare
        top_provinces = df_region.sort_values(by='TotalRevenue', ascending=False).head(5)['Province'].tolist()
        selected_provinces = st.multiselect(
            "Select Provinces to Compare:",
            options=df_region['Province'].unique().tolist(),
            default=top_provinces[:3] if top_provinces else []
        )
        
        if selected_provinces:
            # Filter data for selected provinces
            compare_df = df_region[df_region['Province'].isin(selected_provinces)]
            
            # Create comparison visualization - Radar chart
            categories = ['TotalUsers', 'TotalOrders', 'TotalRevenue', 'OrdersPerUser', 'RevenuePerUser']
            categories_display = ['Users', 'Orders', 'Revenue', 'Orders/User', 'Revenue/User']
            
            fig = go.Figure()
            
            for province in selected_provinces:
                province_data = compare_df[compare_df['Province'] == province].iloc[0]
                
                # Normalize the values for better visualization
                normalized_values = []
                for cat in categories:
                    max_val = df_region[cat].max()
                    if max_val > 0:
                        normalized_values.append(province_data[cat] / max_val * 100)
                    else:
                        normalized_values.append(0)
                
                fig.add_trace(go.Scatterpolar(
                    r=normalized_values,
                    theta=categories_display,
                    fill='toself',
                    name=province
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                title="Regional Performance Comparison (% of Maximum)",
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)