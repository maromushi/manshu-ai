import streamlit as st

st.title("万舟AI")

# ====================================
# NORMALIZE
# =====================================

def normalize(values):

    valid = [v for v in values if v is not None]

    if len(valid) == 0:
        return [0]*len(values)

    mn = min(valid)
    mx = max(valid)

    if mx-mn < 1e-6:
        return [0.5 if v is not None else 0 for v in values]

    return [
       ((v-mn)/(mx-mn)) if v is not None else 0
       for v in values
    ]

data = st.text_area("抽出データを貼り付け")

# ===============================
# 風選択
# ===============================
if "wind" not in st.session_state:
    st.session_state.wind = "なし"

st.markdown("### 風")

wind_labels = ["なし","向かい風","追い風"]

cols = st.columns(3)

for i, w in enumerate(wind_labels):
    with cols[i]:
        if st.button(w, use_container_width=True):
            st.session_state.wind = w

wind = st.session_state.wind

st.write(f"風：{wind}")

# ===============================
# ★ 会場ボタン（横並び完全版）
# ===============================
if "venue" not in st.session_state:
    st.session_state.venue = "浜名湖"

st.markdown("### 会場選択")

labels = ["浜名湖","桐生","住之江","丸亀","多摩川","びわこ","常滑"]

# 2列
for i in range(0, len(labels), 2):
    cols = st.columns(2)

    for j in range(2):
        if i + j < len(labels):
            with cols[j]:
                if st.button(labels[i + j], use_container_width=True):
                    st.session_state.venue = labels[i + j]

venue = st.session_state.venue

st.write(f"選択中：{venue}")

if "run" not in st.session_state:
    st.session_state.run = False

if st.button("計算"):
    st.session_state.run = True

if st.session_state.run:

    if not data:
        st.write("データを貼ってください")
        st.stop()

    local_vars={}

    try:
        exec(data,{"__builtins__":{}},local_vars)
    except:
        st.write("抽出データの形式が正しくありません")
        st.stop()
        
    WinRate=local_vars.get("WinRate",[0]*6)
    PlaceRate=local_vars.get("PlaceRate",[0]*6)

    AvgST=local_vars.get("AvgST",[0]*6)

    Motor2=local_vars.get("Motor2",[0]*6)
    Boat2=local_vars.get("Boat2",[0]*6)

    ExTime=local_vars.get("ExTime",[0]*6)
    ExST=local_vars.get("ExST",[0]*6)

    TurnTime=local_vars.get("TurnTime",[0]*6)
    LapTime=local_vars.get("LapTime",[0]*6)
    StraightTime=local_vars.get("StraightTime",[0]*6)

    Class=local_vars.get("Class",["B1"]*6)
    Fcount=local_vars.get("Fcount",[0]*6)
    ExEntry=local_vars.get("ExEntry",[1,2,3,4,5,6])

    Boat=[1,2,3,4,5,6]

    # ↓ここから万舟AIコード

    # ===============================
    # シンプル安定AI（完成版）
    # ===============================
    
    import itertools

    
    # ===== 基本スコア =====
    StartScore = [0.30 - x for x in AvgST]
    ExScore = [0.30 - x for x in ExST]
    
    TurnScore = normalize([max(TurnTime)-x for x in TurnTime])
    
    ClassScore = [
        1.0 if c=="A1" else
        0.8 if c=="A2" else
        0.6 if c=="B1" else 0.4
        for c in Class
    ]
    
    # ===== 1着スコア =====
    FirstScore = [
        0.50*StartScore[i] +
        0.25*TurnScore[i] +
        0.15*ExScore[i] +
        0.10*ClassScore[i]
        for i in range(6)
    ]

    
    # ===== レース分類 =====
    st_spread = max(StartScore) - min(StartScore)

    inside_gap = FirstScore[0] - max(FirstScore[1:])
    
    if FirstScore[0] < 0.45 and inside_gap < -0.05:
        race_type = "inside_weak"
    
    elif st_spread > 0.10:
        race_type = "chaos"
    
    elif st_spread > 0.06:
        race_type = "middle"
    
    else:
        race_type = "normal"
        
    #風補正
    if wind == "向かい風":
        FirstScore[0] *= 1.03
    
    elif wind == "追い風":
        FirstScore[0] *= 0.97
    
    # ===== 分岐補正（ここだけ） =====
    if race_type == "inside_weak":
        FirstScore[0] *= 0.75
        FirstScore[1] *= 1.10
        FirstScore[2] *= 1.08
    
    elif race_type == "chaos":
        for i in range(3,6):
            FirstScore[i] *= 1.10
    
    elif race_type == "middle":
        FirstScore[2] *= 1.05
        FirstScore[3] *= 1.05
    
    # ===== 2着スコア =====
    SecondScore = [
        0.40*TurnScore[i] +
        0.30*StartScore[i] +
        0.20*ClassScore[i] +
        0.10*(1/(i+1))
        for i in range(6)
    ]
    
    # ===== 3着スコア（万舟） =====
    ThirdScore = [
        0.30*TurnScore[i] +
        0.25*StartScore[i] +
        0.25*(Motor2[i]/100) +
        0.20*(1 if i>=3 else 0)
        for i in range(6)
    ]
    
    # ===== 万舟補正 =====
    if race_type == "chaos":
        for i in range(3,6):
            ThirdScore[i] *= 1.20
    
    elif race_type == "inside_weak":
        for i in range(2,6):
            ThirdScore[i] *= 1.10
    
    # ===== 順位抽出 =====
    first_idx = sorted(range(6), key=lambda i: FirstScore[i], reverse=True)[:2]
    second_idx = sorted(range(6), key=lambda i: SecondScore[i], reverse=True)[:3]
    third_idx = sorted(range(6), key=lambda i: ThirdScore[i], reverse=True)
    
    # ===== 組み立て（スコア付き） =====
    scored_results = []
    
    for a in first_idx:
        for b in second_idx:
            if b == a:
                continue
            for c in third_idx:
                if c in [a,b]:
                    continue
                
                score = (
                    FirstScore[a]*0.7 +
                    SecondScore[b]*0.2 +
                    ThirdScore[c]*0.1
                )
                
                scored_results.append(((a+1,b+1,c+1), score))
    
    # ===== 並び替え =====
    scored_results = sorted(scored_results, key=lambda x: x[1], reverse=True)
    
    # ===== 上位表示 =====
    st.markdown("### ▼ レースタイプ")
    st.write(race_type)
    
    st.markdown("### ▼ 買い目")
    
    output_text = ""

    for r, s in scored_results[:10]:
        line = f"{r[0]}-{r[1]}-{r[2]}"
        
        # スコア表示
        st.write(f"{line}  ({round(s,3)})")
        
        output_text += f"{line} ({round(s,3)})\n"
    
    # ===== 最終コピー用（入力＋結果まとめ） =====
    final_output = "【入力データ】\n"
    final_output += data.strip() + "\n\n"
    final_output += "【レースタイプ】\n"
    final_output += race_type + "\n\n"
    final_output += "【買い目】\n"
    final_output += output_text
    
    st.markdown("### ▼ まとめてコピー")
    st.code(final_output)
