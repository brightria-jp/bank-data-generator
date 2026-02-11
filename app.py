import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="銀行入出金ジェネレーター", layout="wide")

# --- UIデザイン（前回好評だったスタイルを継承） ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetric"] {
        background-color: #ffffff; border: 2px solid #d0d0d0; padding: 20px !important;
        border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-height: 160px;
    }
    [data-testid="stMetricLabel"] { color: #1a1a1a !important; font-weight: bold !important; font-size: 1.1rem !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💳 銀行入出金明細データジェネレーター")

# --- サイドバー設定 ---
with st.sidebar:
    st.header("⚙️ 明細設定")
    init_balance = st.number_input("初期残高（円）", value=1000000, step=100000)
    years = st.slider("生成期間（年）", 1, 3, 1)
    max_rows = st.number_input("表示・保存する最大件数", min_value=1, max_value=5000, value=500)
    
    st.divider()
    user_type = st.radio("アカウント種別", ["個人口座", "法人口座"])
    st.write("Ver.1.0: 銀行明細シミュレーター")

# --- 摘要データ ---
texts_out = ["ｺﾝﾋﾞﾆ", "ｽｰﾊﾟｰﾏｰｹｯﾄ", "ｱﾏｿﾞﾝ ｶｽﾀﾏｰ", "ﾕﾆｸﾛ", "ﾈｯﾄﾌﾘｯｸｽ", "ﾄﾞｺﾓ ｹｰﾀｲ", "東京電力", "水道局"]
texts_in = ["ﾌﾘｺﾐ ｶ) ﾃｽﾄ", "ﾒﾙｶﾘ ｳﾘｱｹ", "利息"]

# --- データ生成ロジック ---
today = datetime.now()
start_date = today - timedelta(days=365 * years)
current_date = start_date
current_balance = init_balance

data = []

while current_date <= today:
    # 毎日何かしら動くわけではない（土日祝やランダムな空白日）
    if random.random() > 0.4: # 約60%の確率で取引発生
        num_tx_today = random.randint(1, 3)
        for _ in range(num_tx_today):
            tx_type = ""
            amount = 0
            description = ""
            
            # 給与（毎月25日）
            if current_date.day == 25:
                tx_type = "入金"
                amount = random.randint(250000, 400000)
                description = "ｷﾞﾖｳﾖ"
            # 家賃・固定費（毎月月末）
            elif current_date.day == 28:
                tx_type = "出金"
                amount = random.randint(50000, 150000)
                description = "ｼﾞﾕｳｷﾖﾋ/ﾌﾘｺﾐ"
            # 通常のランダムな動き
            else:
                if random.random() > 0.8: # 時々入金がある
                    tx_type = "入金"
                    amount = random.randint(1000, 50000)
                    description = random.choice(texts_in)
                else:
                    tx_type = "出金"
                    amount = random.randint(100, 20000)
                    description = random.choice(texts_out)
            
            if tx_type == "入金":
                current_balance += amount
                deposit = amount
                withdrawal = 0
            else:
                current_balance -= amount
                deposit = 0
                withdrawal = amount
            
            data.append({
                "取引日": current_date.strftime('%Y/%m/%d'),
                "摘要": description,
                "お預入れ額": deposit,
                "お引き出し額": withdrawal,
                "差し引き残高": current_balance
            })

    current_date += timedelta(days=1)

# DataFrame化して最新分を切り出し
df = pd.DataFrame(data)
df = df.tail(max_rows)

# --- UI表示 ---
latest = df.iloc[-1]
m1, m2, m3 = st.columns(3)
with m1: st.metric("現在の最終残高", f"¥{int(latest['差し引き残高']):,}")
with m2: st.metric("期間中合計入金", f"¥{int(df['お預入れ額'].sum()):,}")
with m3: st.metric("取引件数", f"{len(df)}件")

st.divider()
st.subheader("📈 残高推移グラフ")
st.line_chart(df.set_index("取引日")["差し引き残高"])

st.subheader("📋 明細プレビュー（最新順）")
st.dataframe(df.sort_index(ascending=False), use_container_width=True)

csv = df.to_csv(index=False).encode('utf-8-sig') # 日本語Excel対策でutf-8-sig
st.download_button("📩 銀行明細CSVをダウンロード", csv, f"bank_statement_{today.strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
