import streamlit as st
from logic import run_ai

st.title("ボートAI")

# ===============================
# 入力（完全コピペ・空）
# ===============================
input_text = st.text_area("ここに貼る", "", height=250)

# ===============================
# テキスト → data変換
# ===============================
def parse_input(text):
    data = {}
    lines = text.split("\n")

    for line in lines:
        if "=" not in line:
            continue

        key, val = line.split("=", 1)

        try:
            data[key.strip()] = eval(val.strip())
        except:
            pass

    return data

# ===============================
# 実行
# ===============================
if st.button("計算"):

    data = parse_input(input_text)

    result = run_ai(data, None)

    # ===============================
    # ① 買い目
    # ===============================
    ranking = sorted(range(6), key=lambda i: result[i], reverse=True)
    buy = f"{ranking[0]+1}-{ranking[1]+1}-{ranking[2]+1}"

    st.subheader("最終順位")
    st.write(result["rank_final"])
    
    st.subheader("無風世界")
    st.write(result["rank_no"])
    
    st.subheader("弱攻め世界")
    st.write(result["rank_weak"])
    
    st.subheader("攻め世界")
    st.write(result["rank_at"])
    
    st.subheader("STATE")
    st.write(result["state"])

    # ===============================
    # ② コピペ用
    # ===============================
    state_text = "\n".join([
        f"Attackers={state['attackers']}",
        f"AttackSuccess={state['AttackSuccess']}",
        f"AttackWeak={state['AttackWeak']}",
        f"DAS={round(state['DAS'],3)}",
        f"RaceMode={state['RaceMode']}"
    ])

    full_text = (
        input_text.strip() +
        "\n\n" +
        state_text +
        "\n\nBUY=" + buy
    )

    st.subheader("コピペ用")
    st.code(full_text)