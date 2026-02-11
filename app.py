import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import io
import zipfile

st.set_page_config(page_title="銀行入出金明細ジェネレーター", layout="wide")

# UIデザイン
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetric"] {
        background-color: #ffffff; border: 2px solid #e0e0e0; padding: 15px !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 銀行入出金明細ジェネレーター")

with st.sidebar:
    st.header("⚙️ 明細設定")
    output_mode = st.radio("出力モード", ["全期間一括 (1ファイル)", "月別分割 (ZIP形式)"])
    
    now = datetime.now()
    month_options = [(now - relativedelta(months=i)).strftime("%Y-%m") for i in range(24)]
    
    if output_mode == "全期間一括 (1ファイル)":
        years = st.slider("生成期間（年）", 1, 5, 2)
        start_dt = now - relativedelta(years=years)
        end_dt = now
    else:
        start_month_str = st.selectbox("開始月", month_options, index=5)
        end_month_str = st.selectbox("終了月", month_options, index=0)
        start_dt = datetime.strptime(start_month_str, "%Y-%m")
        end_dt = datetime.strptime(end_month_str, "%Y-%m")

    initial_balance = st.number_input("初期残高（円）", value=1000000)

# --- 銀行データ生成ロジック ---
def generate_bank_data(start, end, start_bal):
    current_date = start
    balance = start_bal
    data = []
    
    while current_date <= end:
        # 5日: 自動車ローン
        if current_date.day == 5:
            amt = 35000
            balance -= amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "ジドウシャローン", "出金額": amt, "入金額": 0, "差し引き残高": balance})
        
        # 10日: クレジットカード引き落とし
        if current_date.day == 10:
            amt = random.randint(30000, 80000)
            balance -= amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "カードヒキオトシ", "出金額": amt, "入金額": 0, "差し引き残高": balance})

        # 25日: 給与入金
        if current_date.day == 25:
            amt = 280000
            balance += amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "キュウヨ", "出金額": 0, "入金額": amt, "差し引き残高": balance})

        # 26日: クレジットカード引き落とし
        if current_date.day == 26:
            amt = random.randint(50000, 150000)
            balance -= amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "カードヒキオトシ", "出金額": amt, "入金額": 0, "差し引き残高": balance})

        # 27日: 家賃
        if current_date.day == 27:
            amt = 85000
            balance -= amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "フリコミ　ヤチン", "出金額": amt, "入金額": 0, "差し引き残高": balance})

        # 月末（30日か31日）: 公共料金
        is_last_day = (current_date + timedelta(days=1)).month != current_date.month
        if is_last_day:
            for utility in ["デンキダイ", "ガスダイ", "スイドウダイ"]:
                amt = random.randint(3000, 12000)
                balance -= amt
                data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": utility, "出金額": amt, "入金額": 0, "差し引き残高": balance})

        # ランダムな現金出金（ATM）
        if random.random() > 0.85:
            amt = random.choice([10000, 20000, 30000, 50000])
            balance -= amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "ＣＤシュツキン", "出金額": amt, "入金額": 0, "差し引き残高": balance})
            
        current_date += timedelta(days=1)
    return pd.DataFrame(data), balance

# --- 実行 ---
if start_dt > end_dt:
    st.error("開始月は終了月より前を選択してください。")
else:
    if output_mode == "全期間一括 (1ファイル)":
        df, final_bal = generate_bank_data(start_dt, end_dt, initial_balance)
        st.metric("現在の推定残高", f"¥{final_bal:,}")
        st.dataframe(df.sort_values("日付", ascending=False), use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📩 銀行明細CSVをダウンロード", csv, "bank_statement.csv", "text/csv", use_container_width=True)

    else:
        zip_buffer = io.BytesIO()
        current_month_start = start_dt
        current_bal = initial_balance
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            while current_month_start <= end_dt:
                month_end = current_month_start + relativedelta(months=1) - timedelta(days=1)
                df_month, next_bal = generate_bank_data(current_month_start, month_end, current_bal)
                
                header = pd.DataFrame([
                    ["銀行取引明細書", f"対象年月: {current_month_start.strftime('%Y/%m')}", "", "", ""],
                    ["口座名義", "SAMPLE USER", "", "", ""],
                    ["前月繰越残高", f"{current_bal:,}", "", "", ""],
                    ["", "", "", "", ""],
                    ["日付", "摘要", "出金額", "入金額", "差し引き残高"]
                ])
                
                final_df = pd.concat([header, df_month], ignore_index=True)
                with st.expander(f"📂 {current_month_start.strftime('%Y-%m')} の明細"):
                    st.dataframe(df_month, use_container_width=True)
                
                csv_data = final_df.to_csv(index=False, header=False).encode('utf-8-sig')
                zf.writestr(f"bank_{current_month_start.strftime('%Y%m')}.csv", csv_data)
                
                current_bal = next_bal
                current_month_start += relativedelta(months=1)

        st.divider()
        st.download_button("📩 月別明細（ZIP）をダウンロード", zip_buffer.getvalue(), f"bank_data_{datetime.now().strftime('%Y%m%d')}.zip", "application/zip", use_container_width=True)
