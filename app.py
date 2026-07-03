import streamlit as st
import pandas as pd
import data_processing as dp
import visualizations as viz
import forecasting as fcst

st.set_page_config(page_title="Sales & Inventory Dashboard", layout="wide")

st.title("📊 販売・在庫 実績分析ダッシュボード")

# Initialize the SQLite Inventory DB
dp.init_db("mock_inventory.csv")

# Sidebar for file uploads
st.sidebar.header("📂 データアップロード")
sales_file = st.sidebar.file_uploader("販売実績CSVをアップロード", type=['csv'])

# Default to mock data if files not provided
if sales_file is not None:
    df_sales = dp.load_and_preprocess_sales(sales_file)
else:
    try:
        df_sales = dp.load_and_preprocess_sales("mock_sales.csv")
        st.sidebar.info("デモデータ (mock_sales.csv) を表示しています")
    except:
        df_sales = pd.DataFrame()

# Load inventory from SQLite DB
df_inventory = dp.get_inventory_from_db()

if df_sales.empty:
    st.warning("販売データがありません。CSVをアップロードしてください。")
else:
    # Sidebar Filters
    st.sidebar.header("🔍 フィルター設定")
    
    min_date = df_sales['Date'].min().date()
    max_date = df_sales['Date'].max().date()
    
    date_range = st.sidebar.date_input("分析期間を指定", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = dp.filter_by_date(df_sales, start_date, end_date)
    else:
        df_filtered = df_sales

    st.sidebar.header("📊 比較期間設定 (オプション)")
    enable_compare = st.sidebar.checkbox("別の期間と比較する")
    if enable_compare:
        comp_date_range = st.sidebar.date_input("比較対象期間を指定", [min_date, max_date], min_value=min_date, max_value=max_date, key="comp")
        if len(comp_date_range) == 2:
            comp_start, comp_end = comp_date_range
            df_comp = dp.filter_by_date(df_sales, comp_start, comp_end)
        else:
            df_comp = pd.DataFrame()
            
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 売上推移 (期間別)", "🛍️ 商品別分析", "🥧 売上比率", "📦 在庫・予測"])
    
    with tab1:
        st.subheader("売上実績の推移")
        
        freq_option = st.radio("集計単位", ["日別", "週別", "月別"], horizontal=True)
        freq_map = {"日別": "D", "週別": "W", "月別": "M"}
        
        metric_option = st.selectbox("表示指標", ["売上金額 (THB)", "売上個数"])
        metric_col = "Sales_Amount" if "金額" in metric_option else "Sales_Quantity"
        
        df_agg = dp.aggregate_sales(df_filtered, freq=freq_map[freq_option])
        
        if enable_compare and not df_comp.empty:
            df_comp_agg = dp.aggregate_sales(df_comp, freq=freq_map[freq_option])
            # Simple combined plot
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_agg['Date'], y=df_agg[metric_col], mode='lines+markers', name='指定期間'))
            # For comparison, we usually align the x-axis or just show two lines
            # Here we just show the two lines on their respective dates
            fig.add_trace(go.Scatter(x=df_comp_agg['Date'], y=df_comp_agg[metric_col], mode='lines+markers', name='比較期間', line=dict(dash='dash')))
            fig.update_layout(title=f"{freq_option} {metric_option} 比較")
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = viz.plot_time_series(df_agg, metric=metric_col, title=f"{freq_option} {metric_option}")
            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:
        st.subheader("商品別・カラー別・サイズ別 分析")
        
        breakdown_level = st.multiselect(
            "ブレイクダウンする項目を選択 (追加すると詳細に分割されます)", 
            ["Product_Line", "Color", "Size", "Product"], 
            default=["Product_Line"]
        )
        
        if breakdown_level:
            df_breakdown = dp.get_product_breakdown(df_filtered, breakdown_level)
            st.dataframe(df_breakdown.sort_values(by=metric_col, ascending=False))
            
            # Show a bar chart for the primary breakdown
            primary_col = breakdown_level[0]
            fig_bar = viz.plot_bar_chart(df_breakdown, x_col=primary_col, y_col=metric_col, title=f"{primary_col}別 {metric_option}")
            st.plotly_chart(fig_bar, use_container_width=True)
            
    with tab3:
        st.subheader("商品ライン別売上比率")
        
        col1, col2 = st.columns(2)
        
        # We also need to group by Product_Line for the pie charts in tab3
        df_ratio_amt = dp.calculate_ratios(df_filtered.rename(columns={'Product_Line': 'Product'}), 'Sales_Amount')
        fig_pie_amt = viz.plot_pie_chart(df_ratio_amt, 'Product', 'Sales_Amount', '売上金額 (THB) 比率')
        
        df_ratio_qty = dp.calculate_ratios(df_filtered.rename(columns={'Product_Line': 'Product'}), 'Sales_Quantity')
        fig_pie_qty = viz.plot_pie_chart(df_ratio_qty, 'Product', 'Sales_Quantity', '売上個数 比率')
        
        with col1:
            st.plotly_chart(fig_pie_amt, use_container_width=True)
            
        with col2:
            st.plotly_chart(fig_pie_qty, use_container_width=True)
            
    with tab4:
        st.subheader("在庫状況と予測")
        
        st.markdown("### 📝 在庫データの編集")
        st.info("表のセルを直接クリックして数値を編集したり、一番下に行を追加できます。")
        
        # Interactive data editor for Inventory
        edited_df = st.data_editor(
            df_inventory,
            num_rows="dynamic",
            use_container_width=True,
            key="inventory_editor"
        )
        
        if st.button("💾 変更を保存"):
            dp.update_inventory_db(edited_df)
            st.success("在庫データをデータベースに保存しました！")
            df_inventory = edited_df  # update local reference for plots
        
        st.divider()
        
        if not df_inventory.empty:
            st.write("現在の在庫レベル")
            fig_inv = viz.plot_inventory(df_inventory)
            st.plotly_chart(fig_inv, use_container_width=True)
            
            st.write("在庫予測 (直近の販売ペースに基づく今後の需要予測)")
            # Simple forecast based on overall sales quantity
            df_hist = dp.aggregate_sales(df_filtered, freq='D')
            df_fcast = fcst.forecast_sales(df_filtered, metric='Sales_Quantity', forecast_days=30)
            
            fig_fcast = viz.plot_forecast(df_hist, df_fcast, metric='Sales_Quantity')
            st.plotly_chart(fig_fcast, use_container_width=True)
        else:
            st.warning("在庫データがありません。")

