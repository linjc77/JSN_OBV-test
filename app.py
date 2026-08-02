import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 設定網頁標題與手機版面適應
st.set_page_config(page_title="5分線 OBV 監控", page_icon="📈", layout="centered")

st.title("📈 台股 5分線 OBV 監控")
st.write("輸入股號查看當下 5 分線 OBV 與均線狀態")

# 使用者輸入區塊
col1, col2 = st.columns(2)
with col1:
    symbol_input = st.text_input("請輸入股號 (如: 2330)", "2330")
with col2:
    # 讓你可以自由調整均線週期，預設為 20 均線
    ma_window = st.number_input("OBV均線週期 (預設20)", min_value=1, max_value=200, value=20)

if st.button("查詢當下狀態", type="primary"):
    if symbol_input:
        # 自動處理台股代號：輸入純數字預設加上 .TW (上市)
        ticker = f"{symbol_input}.TW" if symbol_input.isdigit() else symbol_input
        
        with st.spinner("抓取最新 5 分線資料中..."):
            try:
                # 透過 yfinance 抓取最近 5 天的 5 分鐘線資料
                df = yf.download(ticker, period="5d", interval="5m", progress=False)
                
                if df.empty:
                    st.error(f"找不到 {ticker} 的資料。若是上櫃股票請加上 .TWO (例如: 3231.TWO)")
                else:
                    # --- 計算 OBV ---
                    # 1. 取得收盤價的漲跌差額
                    close_diff = df['Close'].diff()
                    # 2. 判斷方向：漲為 1，跌為 -1，平盤為 0
                    direction = np.where(close_diff > 0, 1, np.where(close_diff < 0, -1, 0))
                    direction[0] = 0 # 第一筆設為 0
                    
                    # 3. 將方向乘上成交量，並進行累加得出 OBV
                    df['OBV'] = (direction * df['Volume']).cumsum()
                    
                    # --- 計算 OBV 移動平均線 ---
                    df['OBV_MA'] = df['OBV'].rolling(window=ma_window).mean()
                    
                    # 取得當下最新的一筆 K 棒資料
                    latest = df.iloc[-1]
                    # yfinance 回傳的欄位可能是 MultiIndex，確保取值正確
                    current_obv = float(latest['OBV'].iloc[0]) if isinstance(latest['OBV'], pd.Series) else float(latest['OBV'])
                    current_obv_ma = float(latest['OBV_MA'].iloc[0]) if isinstance(latest['OBV_MA'], pd.Series) else float(latest['OBV_MA'])
                    
                    # --- 判斷多空狀態 ---
                    if current_obv > current_obv_ma:
                        status_text = "🟢 目前 OBV 在平均線【之上】 (偏多)"
                    elif current_obv < current_obv_ma:
                        status_text = "🔴 目前 OBV 在平均線【之下】 (偏空)"
                    else:
                        status_text = "⚪ 目前 OBV 與平均線【重合】"

                    # --- 顯示結果 ---
                    st.divider()
                    st.subheader(f"📊 {ticker} 最新狀態")
                    st.caption(f"資料時間 (K棒): {latest.name.strftime('%Y-%m-%d %H:%M')}")
                    
                    # 顯示數值面板
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.metric(label="當下 OBV", value=f"{current_obv:,.0f}")
                    with metric_col2:
                        st.metric(label=f"OBV {ma_window}T 均線", value=f"{current_obv_ma:,.0f}")
                    
                    # 顯示結論
                    if current_obv > current_obv_ma:
                        st.success(f"**結論：** {status_text}")
                    else:
                        st.error(f"**結論：** {status_text}")
                    
            except Exception as e:
                st.error(f"發生錯誤: {e}")