import streamlit as st
import json
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("budget_data.json")


def load_data():
    """Load existing budget records from the JSON file."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default structure if file doesn't exist
    return {"records": []}


def save_data(data):
    """Persist current records to disk."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_records():
    """Delete records only after confirmation, before the next render."""
    if not st.session_state.get("confirm_delete", False):
        return
    data = load_data()
    data["records"].clear()
    save_data(data)
    st.session_state["confirm_delete"] = False
    st.session_state["delete_succeeded"] = True


def main():
    st.title("📝 簡単家計簿アプリ")

    data = load_data()

    # ------------- Input Section ------------- #
    st.header("新規記録の追加")
    col1, col2, col3 = st.columns(3)

    with col1:
        date = st.date_input("日付", datetime.today())
    with col2:
        category = st.text_input("カテゴリ (例: 食費)")
    with col3:
        amount = st.number_input("金額 (円)", step=1.0, format="%.0f")

    income_flag = st.checkbox("収入にチェック (デフォルト: 支出)")

    if st.button("追加する"):
        # Store negative value for expenses, positive for income
        record = {
            "date": date.isoformat(),
            "category": category or "未分類",
            "amount": amount if income_flag else -amount,
        }
        data["records"].append(record)
        save_data(data)
        st.success("記録を追加しました！")

    # ------------- History Section ------------- #
    st.header("履歴")
    if data["records"]:
        # Display records as a table
        st.dataframe(data["records"], use_container_width=True, hide_index=True)

        # Calculate running balance
        total = sum(item["amount"] for item in data["records"])
        st.subheader(f"💰 現在の残高: {total:,.0f} 円")
    else:
        st.info("まだ記録がありません。上で追加してください！")

    # ------------- Sidebar: Settings ------------- #
    st.sidebar.header("設定")
    st.sidebar.checkbox("本当に削除しますか？", key="confirm_delete")
    st.sidebar.button("⚠️ データを全削除", on_click=delete_records)
    if st.session_state.pop("delete_succeeded", False):
        st.sidebar.success("全ての記録を削除しました。")


if __name__ == "__main__":
    # Run the Streamlit app
    main()
