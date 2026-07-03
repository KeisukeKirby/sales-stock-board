import pandas as pd
import streamlit as st
import sqlite3
import os

@st.cache_data
def load_and_preprocess_sales(file):
    try:
        if hasattr(file, 'seek'):
            file.seek(0)
        df = pd.read_csv(file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            if hasattr(file, 'seek'):
                file.seek(0)
            df = pd.read_csv(file, encoding='cp932')
        except UnicodeDecodeError:
            if hasattr(file, 'seek'):
                file.seek(0)
            df = pd.read_csv(file, encoding='utf-8-sig', errors='replace')

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

# --- SQLite Database Functions for Inventory ---

DB_PATH = "inventory.db"

def init_db(mock_csv_path="mock_inventory.csv"):
    """
    Initialize SQLite database and table.
    If the table doesn't exist, seed it with data from mock_inventory.csv.
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory';")
    exists = cursor.fetchone()
    
    if not exists:
        # Create table if it doesn't exist
        if os.path.exists(mock_csv_path):
            df = pd.read_csv(mock_csv_path)
        else:
            # Fallback empty dataframe if no mock csv
            df = pd.DataFrame(columns=['Product', 'Color', 'Size', 'Inventory_Count'])
            
        df.to_sql("inventory", conn, if_exists="replace", index=False)
        
    conn.close()

def get_inventory_from_db():
    """Read inventory data from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM inventory", conn)
    conn.close()
    return df

def update_inventory_db(df):
    """Overwrite the entire inventory table with the updated dataframe."""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("inventory", conn, if_exists="replace", index=False)
    conn.close()
