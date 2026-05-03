import streamlit as st
from logic import run_ai

st.title("ボートAI")

# ===============================
# 入力欄
# ===============================
def input_list(label, default):
    txt = st.text_input(label, ",".join(map(str, default)))
    return [float(x) if "." in x else int(x) for x in txt.split(",")]

WinRate = input_list("WinRate", [6.36,5.59,5.93,5.64,6.57,5.91])
AvgST   = input_list("AvgST",   [0.13,0.15,0.13,0.16,0.16,0.15])
ExST    = input_list("ExST",    [0.02,0.00,0.01,0.01,0.06,0.08])
Turn    = input_list("Turn",    [5.68,5.87,5.84,5.80,5.83,5.73])
Foot    = input_list("Foot",    [0.5,0.5,0.5,0.5,0.5,0.5])

Class = st.text_input("Class", "A2,A2,A1,A2,A1,A2").split(",")
Fcount = input_list("Fcount", [0,1,0,0,0,0])
ExF = input_list("ExhibitionF", [0,0,0,0,1,1])

data = {
    "WinRate": WinRate,
    "AvgST": AvgST,
    "ExST": ExST,
    "Turn": Turn,
    "Foot": Foot,
    "Class": Class,
    "Fcount": Fcount,
    "ExhibitionF": ExF,
}

# ===============================
# 実行
# ===============================
if st.button("計算"):

    result, state = run_ai(data, None)

    # ===============================
    # ① 買い目
    # ===============================
    ranking = sorted(range(6), key=lambda i: result[i], reverse=True)

    buy = f"{ranking[0]+1}-{ranking[1]+1}-{ranking[2]+1}"

    st.subheader("買い目")
    st.write(buy)

    # ===============================
    # ② コピペ用（本体）
    # ===============================
    input_text = "\n".join([
        f"WinRate={WinRate}",
        f"AvgST={AvgST}",
        f"ExST={ExST}",
        f"Turn={Turn}",
        f"Foot={Foot}",
        f"Class={Class}",
        f"Fcount={Fcount}",
        f"ExhibitionF={ExF}",
    ])

    state_text = "\n".join([
        f"Attackers={state['attackers']}",
        f"AttackSuccess={state['AttackSuccess']}",
        f"AttackWeak={state['AttackWeak']}",
        f"DAS={round(state['DAS'],3)}",
        f"RaceMode={state['RaceMode']}"
    ])

    full_text = (
        input_text +
        "\n\n" +
        state_text +
        "\n\nBUY=" + buy
    )

    st.subheader("コピペ用")
    st.code(full_text)