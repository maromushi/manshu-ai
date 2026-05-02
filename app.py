import streamlit as st
from logic import run_ai

st.title("ボートAI")

# ===============================
# 入力UI（←これ追加）
# ===============================
WinRate = st.text_input("WinRate", "6.36,5.59,5.93,5.64,6.57,5.91")
AvgST   = st.text_input("AvgST", "0.13,0.15,0.13,0.16,0.16,0.15")
ExST    = st.text_input("ExST", "0.02,0.00,0.01,0.01,0.06,0.08")

Class   = st.text_input("Class", "A2,A2,A1,A2,A1,A2")
Fcount  = st.text_input("Fcount", "0,1,0,0,0,0")
ExF     = st.text_input("ExhibitionF", "0,0,0,0,1,1")

def to_float_list(s):
    return [float(x) for x in s.split(",")]

def to_int_list(s):
    return [int(x) for x in s.split(",")]

def to_str_list(s):
    return [x.strip() for x in s.split(",")]

# ★ dataをここで作る
data = {
    "WinRate": to_float_list(WinRate),
    "AvgST": to_float_list(AvgST),
    "ExST": to_float_list(ExST),
    "Class": to_str_list(Class),
    "Fcount": to_int_list(Fcount),
    "ExhibitionF": to_int_list(ExF),

    # 仮
    "Motor2":[0]*6,
    "Boat2":[0]*6,
    "Foot":[0]*6,
    "Start":[0]*6,
}

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