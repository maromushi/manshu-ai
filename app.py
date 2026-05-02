import streamlit as st
from logic import run_ai
import ast

st.title("ボートAI")

# ===============================
# コピペ入力欄
# ===============================
raw_input = st.text_area(
    "データ貼り付け（そのままコピペ）",
    height=300
)

# ===============================
# 計算
# ===============================
if st.button("計算"):

    try:
        # ---------------------------
        # ① 文字列 → 辞書化
        # ---------------------------
        local_vars = {}

        exec(raw_input, {}, local_vars)

        # 必要なキーだけ抽出
        data = {
            "WinRate": local_vars["WinRate"],
            "AvgST": local_vars["AvgST"],
            "ExST": local_vars["ExST"],
            "TurnTime": local_vars["TurnTime"],
            "LapTime": local_vars["LapTime"],
            "Class": local_vars["Class"],
            "ExhibitionF": local_vars["ExhibitionF"],
            "Motor2": [0]*6
        }

        # ---------------------------
        # ② 実行
        # ---------------------------
        result = run_ai(data, venue=None)

        # ---------------------------
        # ③ 出力
        # ---------------------------
        st.write("1着確率")
        for i in range(6):
            st.write(f"{i+1}号艇: {round(result[i],3)}")

    except Exception as e:
        st.error(f"エラー: {e}")