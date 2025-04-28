# utils.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Call stored procedure function
@st.cache_data(ttl=600)
def call_stored_procedure(_conn, proc_name, params=None):
    """
    Executes a stored procedure and returns the results
    Caches results for improved performance
    
    Args:
        _conn: Database connection (prefixed with underscore to skip hashing)
        proc_name: Name of the stored procedure to call
        params: List of parameters to pass to the procedure
        
    Returns:
        List of dictionaries containing the result data
    """
    if not _conn:
        return []
    
    cursor = _conn.cursor(dictionary=True)
    try:
        if params:
            cursor.callproc(proc_name, params)
        else:
            cursor.callproc(proc_name)
        
        # Get results
        result_sets = []
        for result in cursor.stored_results():
            result_sets.append(result.fetchall())
        
        return result_sets[0] if result_sets else []
    except Exception as e:
        st.error(f"Stored procedure error: {e}")
        return []
    finally:
        cursor.close()

# Get min and max date range from database
def get_date_range(_conn):
    """
    Get minimum and maximum order dates from database
    Used for initializing date filters
    
    Args:
        _conn: Database connection (prefixed with underscore to skip hashing)
    """
    if not _conn:
        return datetime.now() - timedelta(days=365), datetime.now()
        
    cursor = _conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT MIN(OrderDate) as min_date, MAX(OrderDate) as max_date FROM `Order`")
        result = cursor.fetchone()
        if result and result['min_date'] and result['max_date']:
            return result['min_date'], result['max_date']
        return datetime.now() - timedelta(days=365), datetime.now()
    except Exception as e:
        st.error(f"Error fetching date range: {e}")
        return datetime.now() - timedelta(days=365), datetime.now()
    finally:
        cursor.close()

# Format currency values
def format_currency(value):
    """Format a value as currency with $ symbol and two decimal places"""
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"

# Format percentage values
def format_percentage(value):
    """Format a value as percentage with two decimal places"""
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2f}%"

# 格式化数字为货币形式
def format_currency(value):
    """Format a value as currency with $ symbol and two decimal places"""
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"

# 格式化百分比
def format_percentage(value):
    """Format a value as percentage with two decimal places"""
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2f}%"

# 获取类别列表
def get_categories(_conn):
    """Get all product categories from the database"""
    if not _conn:
        return []
    
    cursor = _conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT DISTINCT Category FROM Product ORDER BY Category")
        categories = cursor.fetchall()
        return [cat['Category'] for cat in categories]
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []
    finally:
        cursor.close()

# 颜色映射辅助函数
def get_discount_colors():
    """Return consistent color mapping for discount levels"""
    return {
        '0% (No Discount)': '#1f77b4',
        '0.01% to 10.00%': '#ff7f0e',
        '10.01% to 20.00%': '#2ca02c',
        '20.01% to 30.00%': '#d62728',
        '30.01% to 40.00%': '#9467bd',
        'Over 40.00%': '#8c564b'
    }

def get_markup_colors():
    """Return consistent color mapping for markup ranges"""
    return {
        'Under 25%': '#1f77b4',
        '25% to 50%': '#ff7f0e',
        '50% to 75%': '#2ca02c',
        '75% to 100%': '#d62728',
        'Over 100%': '#9467bd'
    }

def get_quarter_colors():
    """Return consistent color mapping for quarters"""
    return {
        'Q1 (Jan-Mar)': '#1f77b4',
        'Q2 (Apr-Jun)': '#ff7f0e',
        'Q3 (Jul-Sep)': '#2ca02c',
        'Q4 (Oct-Dec)': '#d62728'
    }

# 帮助生成归一化值的辅助函数
def normalize_series(series):
    """Normalize a pandas series to 0-100 range"""
    if series.max() == series.min():
        return pd.Series([50] * len(series))
    return ((series - series.min()) / (series.max() - series.min())) * 100