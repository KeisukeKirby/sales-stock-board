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

    # Common Japanese column names mapping
    col_mapping = {
        '日付': 'Date', '受注日': 'Date', '売上日': 'Date', 'order_date': 'Date',
        '商品名': 'Product', 'アイテム': 'Product', 'product_name': 'Product',
        'カラー': 'Color', '色': 'Color', 'color': 'Color',
        'サイズ': 'Size', 'size': 'Size',
        '数量': 'Sales_Quantity', '売上数量': 'Sales_Quantity', '個数': 'Sales_Quantity', 'quantity': 'Sales_Quantity',
        '金額': 'Sales_Amount', '売上金額': 'Sales_Amount', '販売価格': 'Sales_Amount', 'amount': 'Sales_Amount', 'price': 'Sales_Amount'
    }
    
    # Rename columns that match the mapping
    df = df.rename(columns=col_mapping)
    
    # Ensure minimum required columns exist
    required_cols = ['Date']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Provide a clear error message in the UI since Streamlit Cloud redacts ValueError tracebacks
        import streamlit as st
        st.error(f"必須のカラム (Date) が見つかりません。アップロードされたファイルのカラム名: {list(df.columns)}")
        st.stop()

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
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
