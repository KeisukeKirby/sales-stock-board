import pandas as pd
import streamlit as st

@st.cache_data
def load_and_preprocess_sales(file):
    df = pd.read_csv(file)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate Year, Month, Week for easy grouping
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
    df['YearWeek'] = df['Date'].dt.to_period('W').astype(str)
    
    return df

@st.cache_data
def load_and_preprocess_inventory(file):
    df = pd.read_csv(file)
    return df

def filter_by_date(df, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

def aggregate_sales(df, freq='D'):
    """
    freq: 'D' for Daily, 'W' for Weekly, 'M' for Monthly
    """
    if df.empty:
        return pd.DataFrame(columns=['Date', 'Sales_Amount', 'Sales_Quantity'])
        
    df_agg = df.groupby(pd.Grouper(key='Date', freq=freq))[['Sales_Amount', 'Sales_Quantity']].sum().reset_index()
    return df_agg

def get_product_breakdown(df, group_by_cols):
    """
    group_by_cols: List of columns e.g. ['Product', 'Color']
    """
    if df.empty:
        return pd.DataFrame()
    return df.groupby(group_by_cols)[['Sales_Amount', 'Sales_Quantity']].sum().reset_index()

def calculate_ratios(df, metric='Sales_Amount'):
    """
    Calculate ratio of each product's metric to total
    """
    if df.empty:
        return pd.DataFrame()
    total = df[metric].sum()
    df_ratio = df.groupby('Product')[metric].sum().reset_index()
    df_ratio['Ratio'] = df_ratio[metric] / total * 100
    return df_ratio
