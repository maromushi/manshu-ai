import streamlit as st
from logic import run_ai

st.title("ボートAI")

# ===============================
# 入力（とりあえず固定でもOK）
# ===============================
data = {
    "WinRate":[6.36,5.59,5.93,5.64,6.57,5.91],
    "PlaceRate":[43.86,34.65,31.68,33.61,47.01,39.81],
    "AvgST":[0.13,0.15,0.13,0.16,0.16,0.15],
    "Motor2":[0.0,0.0,0.0,0.0,0.0,0.0],
    "Boat2":[0.0,0.0,0.0,0.0,0.0,0.0],
    "ExTime":[6.65,6.79,6.74,6.74,6.70,6.55],
    "ExST":[0.02,0.00,0.01,0.01,0.06,0.08],
    "TurnTime":[5.68,5.87,5.84,5.80,5.83,5.73],
    "LapTime":[37.00,37.08,37.52,37.77,37.47,36.73],
    "StraightTime":[7.97,7.94,7.93,8.07,8.11,7.91],
    "Class":["A2","A2","A1","A2","A1","A2"],
    "Fcount":[0,1,0,0,0,0],
    "ExhibitionF":[0,0,0,0,1,1],
    "ExEntry":[1,2,3,4,5,6]
}

venue = "omura"

# ===============================
# 実行
# ===============================
if st.button("計算"):

    # ★ run_aiは (P, state) を返す前提
    result, state = run_ai(data, venue)

    # ===============================
    # 表示（見る用）
    # ===============================
    st.subheader("結果")
    for i in range(6):
        st.write(f"{i+1}号艇: {round(result[i],3)}")

    st.subheader("状態")
    st.write(state)

    # ===============================
    # 入力テキスト
    # ===============================
    input_text = "\n".join([
        f"WinRate={data['WinRate']}",
        f"PlaceRate={data['PlaceRate']}",
        f"AvgST={data['AvgST']}",
        f"Motor2={data['Motor2']}",
        f"Boat2={data['Boat2']}",
        f"ExTime={data['ExTime']}",
        f"ExST={data['ExST']}",
        f"TurnTime={data['TurnTime']}",
        f"LapTime={data['LapTime']}",
        f"StraightTime={data['StraightTime']}",
        f"Class={data['Class']}",
        f"Fcount={data['Fcount']}",
        f"ExhibitionF={data['ExhibitionF']}",
        f"ExEntry={data['ExEntry']}",
    ])

    # ===============================
    # 出力テキスト
    # ===============================
    result_text = "\n".join([
        f"{i+1}号艇: {round(result[i],3)}"
        for i in range(6)
    ])

    # ===============================
    # デバッグテキスト
    # ===============================
    debug_text = "\n".join([
        f"Attackers={state['attackers']}",
        f"AttackSuccess={state['AttackSuccess']}",
        f"AttackWeak={state['AttackWeak']}",
        f"DAS={round(state['DAS'],3)}",
        f"RaceMode={state['RaceMode']}"
    ])

    # ===============================
    # ★ 全部まとめ（これが本体）
    # ===============================
    full_text = (
        "【INPUT】\n" + input_text +
        "\n\n【STATE】\n" + debug_text +
        "\n\n【OUTPUT】\n" + result_text
    )

    # ===============================
    # コピー用
    # ===============================
    st.subheader("コピー用")
    st.code(full_text)