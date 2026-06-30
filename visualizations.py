import plotly.express as px
import plotly.graph_objects as go

def plot_time_series(df, metric='Sales_Amount', title='Sales Over Time'):
    if df.empty:
        return None
    fig = px.line(df, x='Date', y=metric, title=title, markers=True)
    return fig

def plot_bar_chart(df, x_col, y_col='Sales_Amount', title='Bar Chart'):
    if df.empty:
        return None
    fig = px.bar(df, x=x_col, y=y_col, title=title)
    return fig

def plot_pie_chart(df, names_col, values_col, title='Ratio'):
    if df.empty:
        return None
    fig = px.pie(df, names=names_col, values=values_col, title=title)
    return fig

def plot_inventory(df):
    if df.empty:
        return None
    df_sorted = df.sort_values(by='Inventory_Count', ascending=False)
    fig = px.bar(df_sorted, x='Product', y='Inventory_Count', color='Color', barmode='group', title='Current Inventory Levels')
    return fig

def plot_forecast(df_sales_hist, df_forecast, metric='Sales_Quantity'):
    if df_sales_hist.empty or df_forecast.empty:
        return None
    fig = go.Figure()
    
    # Historical
    fig.add_trace(go.Scatter(
        x=df_sales_hist['Date'], 
        y=df_sales_hist[metric],
        mode='lines+markers',
        name='Historical Sales'
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=df_forecast['Date'],
        y=df_forecast[f'Forecast_{metric}'],
        mode='lines+markers',
        name='Forecasted Sales',
        line=dict(dash='dash')
    ))
    
    fig.update_layout(title='Sales Forecast')
    return fig
