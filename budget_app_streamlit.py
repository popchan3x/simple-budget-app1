import os
import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ── Supabase（環境変数が無ければローカル JSON） ──────────────────────────
try:
    from supabase import create_client  # type: ignore
except ImportError:
    create_client = None

DATA_FILE = Path("budget_data.json")
TABLE_NAME = "budget_records"

# ── データアクセス層 ──────────────────────────────────────────────
def _load_local():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"records": []}


def _save_local(data: dict):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_supabase():
    if create_client is None:
        return None
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def load_data():
    sb = _get_supabase()
    if sb is None:
        return _load_local()
    resp = sb.table(TABLE_NAME).select("*").execute()
    return {"records": resp.data or []}


def append_record(record: dict):
    sb = _get_supabase()
    if sb is None:
        data = load_data()
        data["records"].append(record)
        _save_local(data)
    else:
        sb.table(TABLE_NAME).insert(record).execute()


def clear_all():
    sb = _get_supabase()
    if sb is None:
        _save_local({"records": []})
    else:
        sb.table(TABLE_NAME).delete().neq("id", "null").execute()


# ── Streamlit UI ─────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="簡単家計簿アプリ", page_icon="📝")
    st.title("📝 簡単家計簿アプリ")

    # 入力フォーム --------------------------------------------------
    st.header("新規記録の追加")
    c1, c2, c3 = st.columns(3)
    with c1:
        date = st.date_input("日付", datetime.today())
    with c2:
        category = st.text_input("カテゴリ (例: 食費)")
    with c3:
        amount = st.number_input("金額 (円)", step=1.0, format="%.0f")
    income_flag = st.checkbox("収入にチェック (デフォルト: 支出)")

    if st.button("追加する"):
        record = {
            "date": date.isoformat(),
            "category": category or "未分類",
            "amount": amount if income_flag else -amount,
        }
        append_record(record)
        st.success("記録を追加しました！")

    # データ取得 ----------------------------------------------------
    data = load_data()
    if not data["records"]:
        st.info("まだ記録がありません。上で追加してください！")
        return

    df = pd.DataFrame(data["records"])
    df["date"] = pd.to_datetime(df["date"])

    st.header("履歴")
    st.dataframe(df, hide_index=True, use_container_width=True)

    balance = df["amount"].sum()
    st.subheader(f"💰 現在の残高: {balance:,.0f} 円")

    # 月別サマリー --------------------------------------------------
    st.subheader("📅 月別サマリー")
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month")["amount"].sum()
    st.bar_chart(monthly, height=250)

    # ── カテゴリ別グラフ（支出・収入） ──────────────────────────
    col_exp, col_inc = st.columns(2)

    # 支出（負の金額）-----------
    expense_df = df[df["amount"] < 0].copy()
    with col_exp:
        st.markdown("### 🛒 支出の円グラフ")
        if not expense_df.empty:
            expense_df["abs_amount"] = expense_df["amount"].abs()
            cat_exp = expense_df.groupby("category")["abs_amount"].sum()
            fig, ax = plt.subplots(figsize=(4, 4))
            cat_exp.plot.pie(autopct="%1.1f%%", ax=ax, ylabel="")
            st.pyplot(fig)
        else:
            st.write("支出データがありません。")

    # 収入（正の金額）-----------
    income_df = df[df["amount"] > 0]
    with col_inc:
        st.markdown("### 💹 収入の円グラフ")
        if not income_df.empty:
            cat_inc = income_df.groupby("category")["amount"].sum()
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            cat_inc.plot.pie(autopct="%1.1f%%", ax=ax2, ylabel="")
            st.pyplot(fig2)
        else:
            st.write("収入データがありません。")

    # サイドバー ----------------------------------------------------
    st.sidebar.header("設定")
    if st.sidebar.button("⚠️ データを全削除"):
        if st.sidebar.checkbox("本当に削除しますか？"):
            clear_all()
            st.sidebar.success("全データを削除しました。ページをリロードしてください。")


if __name__ == "__main__":
    main()
