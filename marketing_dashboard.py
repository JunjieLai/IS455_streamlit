import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def marketing_dashboard(conn, start_date, end_date):
    """
    Marketing dashboard showing discount analysis, sales patterns, and price elasticity
    """
    st.markdown("<h1 class='main-header'>Marketing Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    from utils import call_stored_procedure
    
    # Get all product categories for filter
    categories_query = """
    SELECT DISTINCT Category FROM Product 
    ORDER BY Category
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute(categories_query)
    categories = cursor.fetchall()
    cursor.close()
    
    if not categories:
        st.error("No product categories found in the database.")
        return
    
    category_options = [cat['Category'] for cat in categories]
    
    # ==================================================
    # Function 1: Discount Profitability Analysis
    # ==================================================
    st.markdown("<h2 class='sub-header'>Discount Profitability Analysis</h2>", unsafe_allow_html=True)
    
    # Interactive elements for Function 1
    col1, col2 = st.columns(2)
    
    with col1:
        selected_category_1 = st.selectbox(
            "Select Product Category",
            options=category_options,
            key="discount_category"
        )
    
    with col2:
        # Date range for period selection
        period_dates = st.date_input(
            "Select Period",
            value=(start_date, end_date),
            key="discount_period"
        )
        
        if len(period_dates) == 2:
            period_start, period_end = period_dates
        else:
            period_start, period_end = start_date, end_date
    
    # Call the stored procedure for discount profitability analysis
    discount_data = call_stored_procedure(conn, "AnalyzeDiscountProfitability", 
                                        [selected_category_1, period_start, period_end])
    
    if discount_data:
        df_discount = pd.DataFrame(discount_data)
        
        # Create tabs for different Y-axis metrics
        discount_tabs = st.tabs([
            "Quantity Sold", 
            "Unique Products", 
            "Sales Revenue", 
            "Profit"
        ])
        
        # Define consistent colors for discount levels
        discount_colors = {
            '0% (No Discount)': '#1f77b4',
            '0.01% to 10.00%': '#ff7f0e',
            '10.01% to 20.00%': '#2ca02c',
            '20.01% to 30.00%': '#d62728',
            '30.01% to 40.00%': '#9467bd',
            'Over 40.00%': '#8c564b'
        }
        
        # Use actual discount levels from data
        actual_discount_levels = df_discount['DiscountLevel'].unique()
        color_sequence = [discount_colors[level] for level in actual_discount_levels if level in discount_colors]
        
        # Tab 1: Quantity Sold
        with discount_tabs[0]:
            fig = px.bar(
                df_discount,
                x='DiscountLevel',
                y='TotalQuantitySold',
                title=f'Total Quantity Sold by Discount Level for {selected_category_1}',
                color='DiscountLevel',
                color_discrete_sequence=color_sequence,
                text='TotalQuantitySold'
            )
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 2: Unique Products
        with discount_tabs[1]:
            fig = px.bar(
                df_discount,
                x='DiscountLevel',
                y='NumberOfUniqueProductIDsSoldUnderTheDiscountLevel',
                title=f'Number of Unique Products Sold by Discount Level for {selected_category_1}',
                color='DiscountLevel',
                color_discrete_sequence=color_sequence,
                text='NumberOfUniqueProductIDsSoldUnderTheDiscountLevel'
            )
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 3: Sales Revenue
        with discount_tabs[2]:
            fig = px.bar(
                df_discount,
                x='DiscountLevel',
                y='TotalSalesRevenue',
                title=f'Total Sales Revenue by Discount Level for {selected_category_1}',
                color='DiscountLevel',
                color_discrete_sequence=color_sequence,
                text='TotalSalesRevenue'
            )
            fig.update_traces(texttemplate='${%{text:,.2f}}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 4: Profit
        with discount_tabs[3]:
            fig = px.bar(
                df_discount,
                x='DiscountLevel',
                y='TotalProfit',
                title=f'Total Profit by Discount Level for {selected_category_1}',
                color='DiscountLevel',
                color_discrete_sequence=color_sequence,
                text='TotalProfit'
            )
            fig.update_traces(texttemplate='${%{text:,.2f}}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Display summary metrics
        st.markdown("### Summary Metrics")
        summary_cols = st.columns(4)
        
        with summary_cols[0]:
            total_quantity = df_discount['TotalQuantitySold'].sum()
            st.metric("Total Quantity Sold", f"{total_quantity:,.0f}")
            
        with summary_cols[1]:
            total_products = df_discount['NumberOfUniqueProductIDsSoldUnderTheDiscountLevel'].sum()
            st.metric("Total Unique Products", f"{total_products:,.0f}")
            
        with summary_cols[2]:
            total_revenue = df_discount['TotalSalesRevenue'].sum()
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
            
        with summary_cols[3]:
            total_profit = df_discount['TotalProfit'].sum()
            st.metric("Total Profit", f"${total_profit:,.2f}")

    else:
        st.info(f"No discount data available for {selected_category_1} in the selected period.")
    
    # ==================================================
    # Function 2: Quarterly Sales Pattern Analysis
    # ==================================================
    st.markdown("<h2 class='sub-header'>Quarterly Sales Pattern Analysis</h2>", unsafe_allow_html=True)
    
    # Interactive elements for Function 2
    selected_category_2 = st.selectbox(
        "Select Product Category",
        options=category_options,
        key="quarterly_category"
    )
    
    # Call the stored procedure for quarterly sales analysis
    quarterly_data = call_stored_procedure(conn, "QuarterlySalesAnalysis", [selected_category_2])
    
    if quarterly_data:
        df_quarterly = pd.DataFrame(quarterly_data)
        
        # Create tabs for different Y-axis metrics
        quarterly_tabs = st.tabs([
            "Unique Products", 
            "Quantity Sold", 
            "Sales Revenue", 
            "Profit"
        ])
        
        # Tab 1: Unique Products
        with quarterly_tabs[0]:
            fig = px.bar(
                df_quarterly,
                x='Quarter',
                y='NumberOfUniqueProductIDsSoldInTheQuarter',
                title=f'Number of Unique Products Sold by Quarter for {selected_category_2}',
                color='Quarter',
                text='NumberOfUniqueProductIDsSoldInTheQuarter'
            )
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 2: Quantity Sold
        with quarterly_tabs[1]:
            fig = px.bar(
                df_quarterly,
                x='Quarter',
                y='TotalQuantitySoldInTheQuarter',
                title=f'Total Quantity Sold by Quarter for {selected_category_2}',
                color='Quarter',
                text='TotalQuantitySoldInTheQuarter'
            )
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 3: Sales Revenue
        with quarterly_tabs[2]:
            fig = px.bar(
                df_quarterly,
                x='Quarter',
                y='TotalSalesRevenueInTheQuarter',
                title=f'Total Sales Revenue by Quarter for {selected_category_2}',
                color='Quarter',
                text='TotalSalesRevenueInTheQuarter'
            )
            fig.update_traces(texttemplate='${%{text:,.2f}}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 4: Profit
        with quarterly_tabs[3]:
            fig = px.bar(
                df_quarterly,
                x='Quarter',
                y='TotalProfitInTheQuarter',
                title=f'Total Profit by Quarter for {selected_category_2}',
                color='Quarter',
                text='TotalProfitInTheQuarter'
            )
            fig.update_traces(texttemplate='${%{text:,.2f}}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Create a line chart with all metrics combined
        st.markdown("### Quarterly Trend Comparison")
        
        # Normalize data for better visualization
        df_normalized = df_quarterly.copy()
        metrics = [
            'NumberOfUniqueProductIDsSoldInTheQuarter', 
            'TotalQuantitySoldInTheQuarter', 
            'TotalSalesRevenueInTheQuarter', 
            'TotalProfitInTheQuarter'
        ]
        
        # Normalize each metric (0-100%)
        for metric in metrics:
            max_val = df_normalized[metric].max()
            if max_val > 0:
                df_normalized[f'{metric}_Normalized'] = df_normalized[metric] / max_val * 100
            else:
                df_normalized[f'{metric}_Normalized'] = 0
        
        # Create multi-line chart
        fig = go.Figure()
        
        # Add traces for each normalized metric
        fig.add_trace(go.Scatter(
            x=df_normalized['Quarter'],
            y=df_normalized['NumberOfUniqueProductIDsSoldInTheQuarter_Normalized'],
            name='Unique Products',
            line=dict(width=3, dash='solid')
        ))
        
        fig.add_trace(go.Scatter(
            x=df_normalized['Quarter'],
            y=df_normalized['TotalQuantitySoldInTheQuarter_Normalized'],
            name='Quantity Sold',
            line=dict(width=3, dash='dot')
        ))
        
        fig.add_trace(go.Scatter(
            x=df_normalized['Quarter'],
            y=df_normalized['TotalSalesRevenueInTheQuarter_Normalized'],
            name='Revenue',
            line=dict(width=3, dash='dashdot')
        ))
        
        fig.add_trace(go.Scatter(
            x=df_normalized['Quarter'],
            y=df_normalized['TotalProfitInTheQuarter_Normalized'],
            name='Profit',
            line=dict(width=3, dash='longdash')
        ))
        
        fig.update_layout(
            title=f'Normalized Quarterly Trends for {selected_category_2} (% of Maximum)',
            xaxis_title='Quarter',
            yaxis_title='Percentage of Maximum Value',
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
        
    else:
        st.info(f"No quarterly sales data available for {selected_category_2}.")
    
    # ==================================================
    # Function 3: Product Price Elasticity Analysis
    # ==================================================
    st.markdown("<h2 class='sub-header'>Product Price Elasticity Analysis</h2>", unsafe_allow_html=True)
    
    # Interactive elements for Function 3
    selected_category_3 = st.selectbox(
        "Select Product Category",
        options=category_options,
        key="elasticity_category"
    )
    
    # Call the stored procedure for price elasticity analysis
    elasticity_data = call_stored_procedure(conn, "ProductPriceElasticityAnalysis", [selected_category_3])
    
    if elasticity_data:
        df_elasticity = pd.DataFrame(elasticity_data)
        
        # Get product information
        product_id = df_elasticity['ProductID'].iloc[0]
        product_name = df_elasticity['ProductName'].iloc[0]
        original_cost = df_elasticity['OriginalCost'].iloc[0]
        
        # Display product information
        st.markdown(f"### Analysis for Most Popular Product in {selected_category_3}")
        
        info_cols = st.columns(3)
        with info_cols[0]:
            st.metric("Product ID", f"{product_id}")
        with info_cols[1]:
            st.metric("Product Name", f"{product_name}")
        with info_cols[2]:
            st.metric("Original Cost", f"${original_cost:.2f}")
        
        # Create tabs for different Y-axis metrics
        elasticity_tabs = st.tabs([
            "Quantity Sold", 
            "Revenue", 
            "Profit", 
            "Avg Unit Profit"
        ])
        
        # Define consistent colors for markup ranges
        markup_colors = {
            'Under 25%': '#1f77b4',
            '25% to 50%': '#ff7f0e',
            '50% to 75%': '#2ca02c',
            '75% to 100%': '#d62728',
            'Over 100%': '#9467bd'
        }
        
        # Use actual markup ranges from data
        actual_markup_ranges = df_elasticity['MarkupRange'].unique()
        color_sequence = [markup_colors[range_val] for range_val in actual_markup_ranges if range_val in markup_colors]
        
        # Tab 1: Quantity Sold
        with elasticity_tabs[0]:
            fig = px.bar(
                df_elasticity,
                x='MarkupRange',
                y='TotalQuantitySoldForTheMarkup',
                title=f'Quantity Sold by Price Markup Range for {product_name}',
                color='MarkupRange',
                color_discrete_sequence=color_sequence,
                text='TotalQuantitySoldForTheMarkup'
            )
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 2: Revenue
        with elasticity_tabs[1]:
            fig = px.bar(
                df_elasticity,
                x='MarkupRange',
                y='TotalRevenueForTheMarkup',
                title=f'Revenue by Price Markup Range for {product_name}',
                color='MarkupRange',
                color_discrete_sequence=color_sequence,
                text='TotalRevenueForTheMarkup'
            )
            fig.update_traces(texttemplate='${%{text:,.2f}}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 3: Profit
        with elasticity_tabs[2]:
            fig = px.bar(
                df_elasticity,
                x='MarkupRange',
                y='TotalProfitForTheMarkup',
                title=f'Profit by Price Markup Range for {product_name}',
                color='MarkupRange',
                color_discrete_sequence=color_sequence,
                text='TotalProfitForTheMarkup'
            )
            fig.update_traces(texttemplate='${%{text:,.2f}}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 4: Average Unit Profit
        with elasticity_tabs[3]:
            fig = px.bar(
                df_elasticity,
                x='MarkupRange',
                y='AverageUnitProfitForTheMarkup',
                title=f'Average Unit Profit by Price Markup Range for {product_name}',
                color='MarkupRange',
                color_discrete_sequence=color_sequence,
                text='AverageUnitProfitForTheMarkup'
            )
            fig.update_traces(texttemplate='${%{text:,.2f}}', textposition='outside')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

        if len(df_elasticity) > 1:
            st.markdown("### Price Elasticity Curve")
            
            # Sort by markup percentage
            df_elasticity_sorted = df_elasticity.sort_values(by='AvgMarkupPercentageInTheMarkupRange')
            
            # Create scatter plot (fixed code)
            fig = px.scatter(
                df_elasticity_sorted,
                x='AvgMarkupPercentageInTheMarkupRange',
                y='TotalQuantitySoldForTheMarkup',
                # Convert Series to list to avoid errors
                size=[float(x) for x in df_elasticity_sorted['TotalRevenueForTheMarkup']],
                color=[float(x) for x in df_elasticity_sorted['TotalProfitForTheMarkup']],
                hover_name='MarkupRange',
                title=f'Price Elasticity for {product_name}',
                labels={
                    'AvgMarkupPercentageInTheMarkupRange': 'Average Markup Percentage',
                    'TotalQuantitySoldForTheMarkup': 'Quantity Sold',
                    'TotalRevenueForTheMarkup': 'Revenue',
                    'TotalProfitForTheMarkup': 'Profit'
                },
                color_continuous_scale='Viridis'
            )
            
            # Add smooth curve (if there are enough data points)
            if len(df_elasticity) >= 3:
                fig.update_layout(
                    shapes=[
                        dict(
                            type='line',
                            xref='x',
                            yref='y',
                            x0=df_elasticity_sorted['AvgMarkupPercentageInTheMarkupRange'].min(),
                            y0=df_elasticity_sorted['TotalQuantitySoldForTheMarkup'].max(),
                            x1=df_elasticity_sorted['AvgMarkupPercentageInTheMarkupRange'].max(),
                            y1=df_elasticity_sorted['TotalQuantitySoldForTheMarkup'].min(),
                            line=dict(
                                color="Red",
                                width=2,
                                dash="dash",
                            ),
                        )
                    ]
                )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendations
            st.markdown("### Pricing Recommendations")
            
            # Find the markup range with highest profit
            max_profit_row = df_elasticity.loc[df_elasticity['TotalProfitForTheMarkup'].idxmax()]
            max_revenue_row = df_elasticity.loc[df_elasticity['TotalRevenueForTheMarkup'].idxmax()]
            max_quantity_row = df_elasticity.loc[df_elasticity['TotalQuantitySoldForTheMarkup'].idxmax()]
            
            rec_cols = st.columns(3)
            
            with rec_cols[0]:
                st.markdown("#### For Maximum Profit")
                st.markdown(f"**Recommended Markup Range:** {max_profit_row['MarkupRange']}")
                st.markdown(f"**Average Markup:** {max_profit_row['AvgMarkupPercentageInTheMarkupRange']:.2f}%")
                st.markdown(f"**Expected Unit Profit:** ${max_profit_row['AverageUnitProfitForTheMarkup']:.2f}")
            
            with rec_cols[1]:
                st.markdown("#### For Maximum Revenue")
                st.markdown(f"**Recommended Markup Range:** {max_revenue_row['MarkupRange']}")
                st.markdown(f"**Average Markup:** {max_revenue_row['AvgMarkupPercentageInTheMarkupRange']:.2f}%")
                st.markdown(f"**Expected Revenue per Unit:** ${max_revenue_row['TotalRevenueForTheMarkup']/max_revenue_row['TotalQuantitySoldForTheMarkup']:.2f}")
            
            with rec_cols[2]:
                st.markdown("#### For Maximum Volume")
                st.markdown(f"**Recommended Markup Range:** {max_quantity_row['MarkupRange']}")
                st.markdown(f"**Average Markup:** {max_quantity_row['AvgMarkupPercentageInTheMarkupRange']:.2f}%")
                st.markdown(f"**Expected Units Sold:** {max_quantity_row['TotalQuantitySoldForTheMarkup']:.0f}")
    else:
        st.info(f"No price elasticity data available for {selected_category_3}.")