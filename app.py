import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import io
import zipfile

st.set_page_config(page_title="銀行入出金明細ジェネレーター", layout="wide")

# --- UIデザイン ---
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

# --- サイドバー設定 ---
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

    initial_balance = st.number_input("初期残高（円）", value=500000)

# --- データ生成ロジック ---
def generate_bank_data(start, end, start_bal):
    current_date = start
    balance = start_bal
    data = []
    
    while current_date <= end:
        # 給与 (毎月25日)
        if current_date.day == 25:
            amt = 250000
            balance += amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "ギヨウヨ", "お預り金額": amt, "お支払い金額": 0, "差し引き残高": balance})
        
        # 家賃 (毎月末)
        if (current_date + timedelta(days=1)).month != current_date.month:
            amt = 80000
            balance -= amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": "チチンダイ", "お預り金額": 0, "お支払い金額": amt, "差し引き残高": balance})

        # 日々の支払い (ランダム)
        if random.random() > 0.7:
            amt = random.randint(1000, 10000)
            balance -= amt
            data.append({"日付": current_date.strftime("%Y/%m/%d"), "摘要": random.choice(["自販機", "コンビニ", "スーパー", "ドラッグストア"]), "お預り金額": 0, "お支払い金額": amt, "差し引き残高": balance})
            
        current_date += timedelta(days=1)
    return pd.DataFrame(data), balance

# --- 実行と表示 ---
if start_dt > end_dt:
    st.error("開始日は終了日より前である必要があります。")
else:
    if output_mode == "全期間一括 (1ファイル)":
        df, final_bal = generate_bank_data(start_dt, end_dt, initial_balance)
        
        st.metric("現在の推定残高", f"¥{final_bal:,}")
        st.dataframe(df.sort_values("日付", ascending=False), use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📩 銀行明細CSVをダウンロード", csv, "bank_statement_full.csv", "text/csv", use_container_width=True)

    else:
        # 月別モード
        zip_buffer = io.BytesIO()
        current_month_start = start_dt
        current_bal = initial_balance
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            while current_month_start <= end_dt:
                next_month = current_month_start + relativedelta(months=1)
                month_end = next_month - timedelta(days=1)
                
                # その月のデータを生成
                df_month, next_bal = generate_bank_data(current_month_start, month_end, current_bal)
                
                # 月ごとのヘッダー情報を追加
                header = pd.DataFrame([
                    ["銀行明細", f"対象月: {current_month_start.strftime('%Y/%m')}", "", "", ""],
                    ["初期残高", f"{current_bal:,}", "", "", ""],
                    ["", "", "", "", ""],
                    ["日付", "摘要", "お預り金額", "お支払い金額", "差し引き残高"]
                ])
                
                # 明細と結合
                final_df = pd.concat([header, df_month], ignore_index=True)
                
                # 画面表示
                with st.expander(f"📂 {current_month_start.strftime('%Y-%m')} の明細プレビュー"):
                    st.dataframe(df_month, use_container_width=True)
                
                # CSVとしてZIPに追加
                csv_data = final_df.to_csv(index=False, header=False).encode('utf-8-sig')
                zf.writestr(f"bank_statement_{current_month_start.strftime('%Y%m')}.csv", csv_data)
                
                # 次の月へ
                current_bal = next_bal
                current_month_start = next_month

        st.divider()
        st.download_button(
            label="📩 月別明細CSV（ZIP形式）を一括ダウンロード",
            data=zip_buffer.getvalue(),
            file_name=f"bank_statements_{datetime.now().strftime('%Y%m%d')}.zip",
            mime="application/zip",
            use_container_width=True
        )
