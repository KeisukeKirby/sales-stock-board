import pandas as pd
from datetime import timedelta

def forecast_sales(df_sales, metric='Sales_Quantity', forecast_days=30):
    """
    Very simple forecasting using a 7-day moving average or recent average velocity.
    """
    if df_sales.empty:
        return pd.DataFrame()
        
    # Aggregate daily
    df_daily = df_sales.groupby('Date')[metric].sum().reset_index()
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily = df_daily.sort_values(by='Date')
    
    if len(df_daily) < 7:
        # Not enough data for meaningful forecast, just use average
        avg = df_daily[metric].mean()
    else:
        # Use last 7 days average
        avg = df_daily.tail(7)[metric].mean()
        
    last_date = df_daily['Date'].max()
    
    forecast_records = []
    for i in range(1, forecast_days + 1):
        next_date = last_date + timedelta(days=i)
        forecast_records.append({
            'Date': next_date,
            f'Forecast_{metric}': avg
        })
        
    return pd.DataFrame(forecast_records)
