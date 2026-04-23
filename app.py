import streamlit as st

WEAK = 0.06
MID = 0.09
STRONG = 0.13

st.title("万舟AI")

# ====================================
# NORMALIZE
# =====================================

def normalize_minmax(values):
    valid = [v for v in values if v is not None]
    if not valid:
        return [0]*len(values)

    mn = min(valid)
    mx = max(valid)

    if mx - mn < 1e-6:
        return [0.5]*len(values)

    return [(v - mn)/(mx - mn) if v is not None else 0 for v in values]


def normalize_sum(arr):
    s = sum(arr) + 1e-6
    return [x/s for x in arr]

data = st.text_area("抽出データを貼り付け")

# ===============================
# ★ 会場ボタン（横並び完全版）
# ===============================
if "venue" not in st.session_state:
    st.session_state.venue = "浜名湖"

st.markdown("### 会場選択")

labels = ["浜名湖","桐生","住之江","丸亀","多摩川","びわこ","常滑","三国"]

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

if st.button("計算"):

    if not data:
        st.write("データを貼ってください")
        st.stop()

    local_vars = {}

    try:
        safe_builtins = {
            "range": range,
            "len": len,
            "min": min,
            "max": max,
            "sum": sum
        }
    
        exec(data.strip(), {"__builtins__": safe_builtins}, local_vars)
    
    except Exception as e:
        st.write("抽出データエラー:", e)
        st.stop()
    
    WinRate = local_vars.get("WinRate",[0]*6)
    PlaceRate = local_vars.get("PlaceRate",[0]*6)
    
    AvgST = local_vars.get("AvgST",[0]*6)
    
    Motor2 = local_vars.get("Motor2",[0]*6)
    Boat2 = local_vars.get("Boat2",[0]*6)
    
    ExTime = local_vars.get("ExTime",[0]*6)
    ExST = local_vars.get("ExST",[0]*6)
    
    TurnTime = local_vars.get("TurnTime",[0]*6)
    LapTime = local_vars.get("LapTime",[0]*6)
    StraightTime = local_vars.get("StraightTime",[0]*6)
    
    Class = local_vars.get("Class",["B1"]*6)
    Fcount = local_vars.get("Fcount",[0]*6)
    ExEntry = local_vars.get("ExEntry",[1,2,3,4,5,6])
    
    Boat = [1,2,3,4,5,6]

    # ↓ここから万舟AIコード

    import itertools
            

    # =====================================
    # FIX FUNCTIONS
    # =====================================

    def fix_length(arr, fill=0):

        arr=list(arr)

        if len(arr)<6:
            arr+=[fill]*(6-len(arr))

        return arr[:6]

    def to_float_list(arr):

        out=[]

        for x in arr:

            try:
                out.append(float(x))
            except:
                out.append(0.0)

        return out

    def to_int_list(arr):

        out=[]

        for x in arr:

            try:
                out.append(int(x))
            except:
                out.append(0)

        return out

    def clamp(arr, lo, hi):

        out=[]

        for x in arr:

            if x<lo or x>hi:
                out.append(0.0)
            else:
                out.append(x)

        return out

    def fix_class(arr):

        allowed=["A1","A2","B1","B2"]

        out=[]

        for x in arr:

            if x in allowed:
                out.append(x)
            else:
                out.append("B1")

        return fix_length(out,"B1")

    def fix_exentry(arr):

        try:
            arr=[int(x) for x in arr]
        except:
            return [1,2,3,4,5,6]

        if len(arr)!=6:
            return [1,2,3,4,5,6]

        if set(arr)!={1,2,3,4,5,6}:
            return [1,2,3,4,5,6]

        return arr
        
    def convert_exst(x):
        # 展示ST → 実戦STに寄せる変換
    
        if x <= 0:
            return 0.18
    
        # 速い展示は少し割引（過信防止）
        if x < 0.10:
            return x * 0.85 + 0.015
    
        # 普通帯
        elif x < 0.20:
            return x * 0.90 + 0.01
    
        # 遅い展示はそのまま寄せる
        else:
            return x * 0.95
            
    F_TABLE = {
        "A1": {"F1": 0.90, "F2": 0.80},
        "A2": {"F1": 0.88, "F2": 0.78},
        "B1": {"F1": 0.85, "F2": 0.75},
        "B2": {"F1": 0.82, "F2": 0.70},
    }

    # =====================================
    # SANITIZE INPUT
    # =====================================

    # ① 先に欠場判定
    Active = [1]*6

    for i in range(6):
        if (
            WinRate[i]==0
            and PlaceRate[i]==0
            and Motor2[i]==0
        ):
            Active[i]=0
            
    # ★ 欠場艇の完全除外フラグ（追加）
    for i in range(6):
        if (
            WinRate[i] == 0
            and PlaceRate[i] == 0
            and Motor2[i] == 0
            and Boat2[i] == 0
        ):
            Active[i] = 0

    # ② そのあと補正
    avg_win = sum([WinRate[i] for i in range(6) if Active[i]==1])/max(1,sum(Active))

    WinRate=[
        x if Active[i]==1 else 0
        for i,x in enumerate(WinRate)
    ]
    PlaceRate=clamp(to_float_list(fix_length(PlaceRate)),0,100)

    AvgST=clamp(to_float_list(fix_length(AvgST)),0,0.40)

    Motor2=clamp(to_float_list(fix_length(Motor2)),0,100)
    Boat2=clamp(to_float_list(fix_length(Boat2)),0,100)

    # モーター0補正
    avg_motor = sum([Motor2[i] for i in range(6) if Active[i]==1]) / max(1,sum(Active))
    Motor2 = [
        Motor2[i] if Active[i]==1 else 0.0
        for i in range(6)
    ]

    avg_boat = sum([Boat2[i] for i in range(6) if Active[i]==1]) / max(1,sum(Active))

    Boat2 = [
        Boat2[i] if Active[i]==1 else 0.0
        for i in range(6)
    ]
    
    ExTime=clamp(to_float_list(fix_length(ExTime)),6,8)
    def clamp_exst(arr):
        out=[]
        for x in arr:
            if x <= 0:
                out.append(0.18)   # 平均扱い
            elif x > 0.50:
                out.append(0.50)   # 上限だけ抑える
            else:
                out.append(x)
        return out
    
    ExST = clamp_exst(to_float_list(fix_length(ExST)))

    TurnTime=to_float_list(fix_length(TurnTime))
    LapTime=to_float_list(fix_length(LapTime))
    StraightTime=to_float_list(fix_length(StraightTime))

    Class=fix_class(Class)

    Fcount=to_int_list(fix_length(Fcount))

    ExEntry=fix_exentry(ExEntry)
    
    # ★ 欠場艇を進入から除外（修正版）
    valid = [i+1 for i in range(6) if Active[i] == 1]
    
    # 有効な艇だけ残す
    ExEntry = [e for e in ExEntry if e in valid]
    
    # 足りない分を後ろに追加
    for i in valid:
        if i not in ExEntry:
            ExEntry.append(i)
    
    # 念のため6に揃える
    ExEntry = ExEntry[:6]

    ExhibitionF = local_vars.get("ExhibitionF",[0]*6)
    ExhibitionF = to_int_list(fix_length(ExhibitionF))
    
    # ===============================
    # ★ 勝率0ペナルティ
    # ===============================
    for i in range(6):
    
        if WinRate[i] == 0 and Active[i] == 1:
            WinRate[i] = avg_win * 0.6   # ←弱め補正
    
    

    # =====================================
    # AI CORE
    # =====================================

    def run_no_attack(order):
        return run_core(order, mode="no")
    
    def run_weak(order):
        return run_core(order, mode="weak")
    
    def run_attack(order):
        return run_core(order, mode="attack")
        
    def normalize(arr):
        s = sum(arr) + 1e-6
        return [x/s for x in arr]
            
    def run_core(order, mode):
        print("=== CHECK ExhibitionF ===")
        for i in range(6):
            print(f"{i+1}号艇  ExST={ExST[i]}  F={ExhibitionF[i]}")
        print("========================")
        
        AttackWeak = 0
        AttackSuccess = 0
        DoubleAttackScore = 0.0
        DAS = 0.0

        debug_log = []
        debug_text = []
        
        results = []

        FC=[Fcount[i] for i in order]
        CLS=[Class[i] for i in order]
        ExF = [ExhibitionF[i] for i in order]
        
        boats = [
            Boat[i] if Active[i]==1 else -1
            for i in order
        ]

        WR=[WinRate[i] for i in order]
        PR=[PlaceRate[i] for i in order]

        ST=[AvgST[i] for i in order]
        RawST = ST.copy() 

        M=[Motor2[i] for i in order]
        BO=[Boat2[i] for i in order]

        ET=[ExTime[i] for i in order]
        EST=[ExST[i] for i in order]

        TT=[TurnTime[i] for i in order]
        LT=[LapTime[i] for i in order]
        STT=[StraightTime[i] for i in order]
        
        real_lane = order
        
        # ===============================
        # ★ 展示F補正（最重要）
        # ===============================
        BadST = [0]*6
        
        for i in range(6):
        
            # 明確F
            is_f = ExF[i] == 1
            
            # 異常スタート（疑似F）
            is_abnormal = EST[i] <= 0.02
        
            # ===============================
            # ■ 本物F（強ペナ）
            # ===============================
            if is_f:
        
                BadST[i] = 1
        
                base = 0.20
        
                if CLS[i] == "A1":
                    base = 0.16
                elif CLS[i] == "A2":
                    base = 0.18
        
                EST[i] = 0.7 * base + 0.3 * max(EST[i], 0.05)
        
            # ===============================
            # ■ 疑似F（中ペナ）
            # ===============================
            elif is_abnormal:
        
                BadST[i] = 1
        
                if CLS[i] == "A1":
                    EST[i] = max(0.11, EST[i] * 0.5 + 0.07)
                elif CLS[i] == "A2":
                    EST[i] = max(0.115, EST[i] * 0.5 + 0.075)
                else:
                    EST[i] = max(0.13, EST[i] * 0.5 + 0.09)
        # ===============================
        # SKILL（修正版）
        # ===============================
        
        # --- Win ---
        WinRaw = WR[:]
        min_val = min(WinRaw)
        if min_val < 0:
            WinRaw = [x - min_val + 1e-6 for x in WinRaw]
        
        WinScore = normalize_sum(WinRaw)
        
        
        # --- Place ---
        PlaceRaw = PR[:]
        min_val = min(PlaceRaw)
        if min_val < 0:
            PlaceRaw = [x - min_val + 1e-6 for x in PlaceRaw]
        
        PlaceScore = normalize_sum(PlaceRaw)
        
        
        # --- 合成
        SkillRaw = []
        
        for i in range(6):
        
            base = 0.7*WinScore[i] + 0.3*PlaceScore[i]
        
            # 欠損軽減
            if WR[i] == 0 and PR[i] == 0:
                base *= 0.7
        
            SkillRaw.append(base)
        
        
        # --- マイナス対策
        min_val = min(SkillRaw)
        if min_val < 0:
            SkillRaw = [x - min_val + 1e-6 for x in SkillRaw]
        
        
        # ★ 最後これ必須
        Skill = normalize_sum(SkillRaw)
                
        
        # ===============================
        # ENGINE（修正版）
        # ===============================
        
        # --- Motor ---
        MotorRaw = M[:]
        
        min_val = min(MotorRaw)
        if min_val < 0:
            MotorRaw = [x - min_val + 1e-6 for x in MotorRaw]
        
        MotorScore = normalize_sum(MotorRaw)
        
        
        # --- Skillも一応揃える（重要）
        SkillRaw = Skill[:]
        
        min_val = min(SkillRaw)
        if min_val < 0:
            SkillRaw = [x - min_val + 1e-6 for x in SkillRaw]
        
        SkillScore = normalize_sum(SkillRaw)
        
        
        # --- order揃え
        Active_local = [1 if boats[i] != -1 else 0 for i in range(6)]
        
        
        # --- Engine合成
        EngineRaw = []
        
        for i in range(6):
        
            if Active_local[i] == 0:
                EngineRaw.append(0)
                continue
        
            val = 0.6 * MotorScore[i] + 0.4 * SkillScore[i]
        
            # 弱モーター補正
            if MotorScore[i] < 0.10:
                val *= 0.85
        
            EngineRaw.append(val)
        
        
        # --- マイナス対策
        min_val = min(EngineRaw)
        if min_val < 0:
            EngineRaw = [x - min_val + 1e-6 for x in EngineRaw]
        
        
        # ★ 最後これ必須
        Engine = normalize_sum(EngineRaw)

        # ===============================
        # EXHIBIT
        # ===============================
        
        # --- Time（展示タイム） ---
        AvgEx = sum(ET)/6
        TimeRaw = [AvgEx - x for x in ET]
        
        min_val = min(TimeRaw)
        if min_val < 0:
            TimeRaw = [x - min_val + 1e-6 for x in TimeRaw]
        
        TimeScore = normalize_sum(TimeRaw)
        
        
        # --- ExST（展示ST） ---
        # 速いほど良い＝小さいほど良い → 逆転＋クランプ
        ExSTRaw = [max(0.0, 0.25 - x) for x in EST]
        
        min_val = min(ExSTRaw)
        if min_val < 0:
            ExSTRaw = [x - min_val + 1e-6 for x in ExSTRaw]
        
        ExSTScore = normalize_sum(ExSTRaw)
        
        
        # --- Exhibit合成 ---
        ExhibitRaw = [
            0.80*TimeScore[i] + 0.20*ExSTScore[i]
            for i in range(6)
        ]
        
        # マイナス対策
        min_val = min(ExhibitRaw)
        if min_val < 0:
            ExhibitRaw = [x - min_val + 1e-6 for x in ExhibitRaw]
        
        
        # --- クラス補正 ---
        ExhibitAdj = []
        
        for i in range(6):
            cls = CLS[i]
        
            if cls == "A1":
                factor = 1.00
            elif cls == "A2":
                factor = 0.92
            elif cls == "B1":
                factor = 0.80
            else:
                factor = 0.65
        
            ExhibitAdj.append(ExhibitRaw[i] * factor)
        
        
        # ★ 最後これ必須
        min_val = min(ExhibitAdj)
        if min_val < 0:
            ExhibitAdj = [x - min_val + 1e-6 for x in ExhibitAdj]
        
        Exhibit = normalize_sum(ExhibitAdj)
        
        # ===============================
        # TIME SCORE（安定＋展開ハイブリッド）
        # ===============================
        
        # Turn
        avg_tt = sum(TT)/6
        max_tt = max(TT)
        
        TurnRaw = [
            0.7*(avg_tt - x) + 0.3*(max_tt - x)
            for x in TT
        ]
        
        min_val = min(TurnRaw)
        if min_val < 0:
            TurnRaw = [x - min_val + 1e-6 for x in TurnRaw]
        
        TurnScore = normalize_sum(TurnRaw)
        
        
        # Lap
        avg_lt = sum(LT)/6
        max_lt = max(LT)
        
        LapRaw = [
            0.7*(avg_lt - x) + 0.3*(max_lt - x)
            for x in LT
        ]
        
        min_val = min(LapRaw)
        if min_val < 0:
            LapRaw = [x - min_val + 1e-6 for x in LapRaw]
        
        LapScore = normalize_sum(LapRaw)
        
        
        # Straight
        avg_st = sum(STT)/6
        max_st = max(STT)
        
        StraightRaw = [
            0.7*(avg_st - x) + 0.3*(max_st - x)
            for x in STT
        ]
        
        min_val = min(StraightRaw)
        if min_val < 0:
            StraightRaw = [x - min_val + 1e-6 for x in StraightRaw]
        
        StraightScore = normalize_sum(StraightRaw)
        
        # ===============================
        # FOOT
        # ===============================

        # Exhibit処理
        ExhibitRaw = Exhibit[:]
        min_val = min(ExhibitRaw)
        if min_val < 0:
            ExhibitRaw = [x - min_val + 1e-6 for x in ExhibitRaw]
        ExhibitScore = normalize_sum(ExhibitRaw)
        
        # Foot合成
        RawFoot = [
            0.42*TurnScore[i]+
            0.28*LapScore[i]+
            0.25*StraightScore[i]+
            0.08*ExhibitScore[i]
            for i in range(6)
        ]
        
        # マイナス対策
        min_val = min(RawFoot)
        if min_val < 0:
            RawFoot = [x - min_val + 1e-6 for x in RawFoot]
        
        Foot = normalize_sum(RawFoot)
        
        # TimeScore
        TimeScore = [
            0.4*TurnScore[i] +
            0.3*LapScore[i] +
            0.3*StraightScore[i]
            for i in range(6)
        ]
        TimeScore = normalize_sum(TimeScore)
        
        # order適用（全部揃える）
        Foot = [Foot[i] for i in order]
        TimeScore = [TimeScore[i] for i in order]
        Turn = [TurnScore[i] for i in order]
        Lap  = [LapScore[i] for i in order]
        Active_local = [Active[i] for i in order]


        # ===============================
        # START（精度版）
        # ===============================
        
        adj_exst = []

        for i in range(6):
        
            x = EST[i]
        
            # ★ ここだけにする（唯一のF処理）
            if BadST[i] == 1:
                x = max(0.12, x + 0.06)
        
            x = convert_exst(x)
        
            adj_exst.append(x)
        

        # ===============================
        # ① 展示信頼度
        # ===============================
        trust = []
        
        for i in range(6):

            diff = abs(EST[i] - ST[i])
        
            t = 1.0
        
            if diff > 0.12:
                t *= 0.7
        
            if diff > 0.20:
                t *= 0.5
        
            if EST[i] >= 0.30:
                t *= 0.4
        
            elif EST[i] <= 0.10:
                t *= 1.05
        
            if CLS[i] in ["B1","B2"] and EST[i] >= 0.25:
                t *= 0.8
        
            # ★ ここに入れる（これが正解）
            if BadST[i] == 1:
        
                if CLS[i] == "A1":
                    t *= 0.7
        
                elif CLS[i] == "A2":
                    t *= 0.6
        
                elif CLS[i] == "B1":

                    if Foot[i] >= 0.45:
                        t *= 0.7
                    else:
                        t *= 0.5
                        
                else:
                    t *= 0.45
        
            trust.append(t)
                
        # ===============================
        # ② Start計算
        # ===============================
        Start = []
        
        for i in range(6):
        
            avg = 0.30 - ST[i]
            ex  = 0.30 - adj_exst[i]
        
            t = trust[i]
        
            val = (1 - t)*avg + t*ex
        
            Start.append(val)
            
        # ===============================
        # ★ 疑似攻め
        # ===============================
        PseudoAttackFlag = (
            max(Start[2] - Start[1], Start[3] - Start[2]) > 0.015
        )
        
        # ===============================
        # ★ 展示STフラグ（分離）
        # ===============================
        BadST_flag = [
            1 if (BadST[i] == 1 or EST[i] >= 0.30) else 0
            for i in range(6)
        ]
        GoodST = [1 if x <= 0.10 else 0 for x in EST]
        
        # ===============================
        # ★ Start補正（軽量）
        # ===============================
        for i in range(6):
        
            cls = CLS[i]
        
            factor = 1.0
        
            if FC[i] == 1:
                factor = F_TABLE[cls]["F1"]
        
            elif FC[i] >= 2:
                factor = F_TABLE[cls]["F2"]
        
            # ★ 弱く効かせる（重要）
            Start[i] *= (0.9 + 0.1 * factor)
        
            # 展示STは別処理
            if EST[i] <= 0.10:
                Start[i] *= 1.03
        
            elif EST[i] <= 0.13:
                Start[i] *= 1.02
        
            elif EST[i] >= 0.20:
                Start[i] *= 0.95   
                
        # ===============================
        # ★ スタート崩壊検知
        # ===============================
        StartCollapse = 0
        
        if Start[0] < max(Start[1:4]) - 0.03:
            StartCollapse = 1
            
            
        
            
        # --- 並び順作成（0-index）---
        entry_order = [x-1 for x in ExEntry]
        
        # 逆引き（どの艇が何番目か）
        pos = [0]*6
        for i, boat in enumerate(entry_order):
            pos[boat] = i
        
        
        # --- Class係数 ---
        ClassCoef = []
        for c in Class:
            if c == "A1":
                ClassCoef.append(1.15)
            elif c == "A2":
                ClassCoef.append(1.05)
            elif c == "B1":
                ClassCoef.append(0.95)
            else:
                ClassCoef.append(0.85)
        
        
        # --- Fペナルティ ---
        FPenalty = []
        for f in Fcount:
            if f >= 2:
                FPenalty.append(0.75)
            elif f == 1:
                FPenalty.append(0.88)
            else:
                FPenalty.append(1.0)
                
        # ===============================
        # ★ 外統一判定（追加）
        # ===============================
        outer_ok = [False]*6
        
        for i in range(1,6):
        
            is_fast = Start[i] > Start[i-1] + 0.01
        
            outer_ok[i] = (
                is_fast
                and (
                    DAS < 0.12
                    or AttackSuccess == 1
                    or AttackWeak == 1
                )
            )
        
        
        # --- 壁強度（進入順ベース）---
        Wall = [0]*6
        
        for i in range(6):
            p = pos[i]
        
            if p == 0:
                Wall[i] = 0
            else:
                w = 0
                for k in range(p):
                    j = entry_order[k]
        
                    base = (0.6*Start[j] + 0.4*Foot[j])
                    base *= ClassCoef[j]
                    base *= FPenalty[j]
        
                    w += base
        
                Wall[i] = w / p
        
        
        # --- 壁制約 ---
        for i in range(6):
            if pos[i] >= 3:
                penalty = 1 - (0.35 * Wall[i])
        
                Turn[i] *= penalty
                Lap[i]  *= penalty
        
                Start[i] += 0.015 * Wall[i]
        
        
        # --- 外上限 ---
        for i in range(6):
            if pos[i] >= 4:
                Foot[i] = min(Foot[i], 0.55)
        
        # ===============================
        # ★ 壁崩れ検知
        # ===============================
        # --- 壁崩れ ---
        WallBreak = [0]*6
        
        for i in range(6):
            p = pos[i]
        
            if p == 0:
                continue
        
            score = 0
        
            for k in range(p):
                j = entry_order[k]
        
                st_diff = Start[i] - Start[j]
                f_factor = 1 - FPenalty[j]
                foot_diff = Foot[i] - Foot[j]
        
                score += 0.5*st_diff + 0.3*f_factor + 0.2*foot_diff
        
            WallBreak[i] = max(0, score)
        
        
        # --- 壁緩和 ---
        for i in range(6):
            if pos[i] >= 3:
                relax = 1 + 0.5 * WallBreak[i]
        
                Turn[i] *= relax
                Lap[i]  *= relax
                
        # 壁制約＆緩和のあと

        Foot = [
            0.42*Turn[i]+
            0.28*Lap[i]+
            0.25*StraightScore[i]+
            0.08*Exhibit[i]
            for i in range(6)
        ]
        
        
        # ===============================
        # ★ FrontBreak（最終）
        # ===============================
        FrontBreak = (
            StartCollapse == 1
            or max(WallBreak) > 0.25
            or (
                max(Start[1:4]) - Start[0] > 0.05
            )
        )

        # ===============================
        # VELOCITY
        # ===============================

        VelocityRaw=[0.45*Foot[i]+0.35*Engine[i]+0.20*Start[i] for i in range(6)]
        Velocity=VelocityRaw

        for i in range(6):
            if i >= 4:
                if Engine[i] > 0.60 and Foot[i] > 0.50:
                    Velocity[i] *= 1.08

        # ===============================
        # INSIDE SURVIVAL
        # ===============================

        InsideSurvival=[
            0.40*Skill[i]+
            0.25*Engine[i]+
            0.22*Start[i]+
            0.13*Foot[i]
            for i in range(6)
        ]
        
        for i in range(6):

            if BadST[i] == 1:
        
                InsideSurvival[i] *= 0.90

        # ===============================
        # CPI
        # ===============================

        CPI=[
            0.18*Skill[i]+
            0.20*Engine[i]+
            0.22*Foot[i]+
            0.22*Turn[i]+
            0.18*Velocity[i]
            for i in range(6)
        ]

        AttackCPI=[
        0.35*Foot[i]+
        0.25*Turn[i]+
        0.20*Start[i]+
        0.20*Engine[i]
        for i in range(6)
        ]

        AttackIndex = [
            0.20*Start[i] +
            0.45*Foot[i] +
            0.25*Turn[i] +
            0.10*Engine[i]
            for i in range(6)
        ]
        
        
        # ===============================
        # ★ AttackIndex補正（統合）
        # ===============================
        for i in range(6):
        
            # モーター（条件付きで強化）
            if MotorScore[i] > 0.60 and Foot[i] > 0.50:
                AttackIndex[i] += 0.03
            elif MotorScore[i] > 0.55:
                AttackIndex[i] += 0.02
        
            # 展示F
            if BadST[i] == 1:
        
                if Foot[i] > 0.50 and Turn[i] > 0.50:
                    AttackIndex[i] *= 1.02
                else:
                    AttackIndex[i] *= 0.90
        
            # 良ST
            elif GoodST[i] == 1:
                AttackIndex[i] *= 1.05
    
        # ===============================
        # ★ attackers決定（最終版）
        # ===============================
        
        attackers = []

        for i in range(1,6):
        
            start_attack = (
                Start[i] > Start[i-1] + 0.015
            )
        
            can_attack = (
                AttackIndex[i] >= AttackIndex[i-1] - 0.02
                and (
                    Foot[i] >= Foot[i-1] - 0.03
                    or Turn[i] >= Turn[i-1] - 0.02
                )
            )
        
            chance_flag = (
                CPI[i] >= CPI[i-1] - 0.04
                and (
                    Foot[i] > Foot[i-1]
                    or Engine[i] > Engine[i-1]
                )
            )
        
            strong = (
                AttackIndex[i] >= max(AttackIndex) - 0.05
                or Turn[i] >= max(Turn) - 0.03
            )
        
            # ===============================
            # 外の壁チェック（ここに入れる）
            # ===============================
            if i >= 4:
        
                wall_block = (
                    CPI[i] < CPI[i-1] - 0.02
                    or Turn[i] < Turn[i-1] - 0.01
                )
        
                weak_start = (
                    Start[i] > Start[i-1] + 0.01
                )
        
                if wall_block and weak_start:
                    continue
        
            # ===============================
            # 攻め判定
            # ===============================
            if (
                can_attack
                or (start_attack and strong)
                or (chance_flag and strong)
            ):
                attackers.append(i)
        
        # 重複削除
        attackers = list(set(attackers))
                    
        # ===============================
        # ★ DoubleAttackScore（最終版）
        # ===============================
        
        if len(attackers) == 0:
            DAS = 0
                   
        attackers = sorted(
            attackers,
            key=lambda x: (
                0.35 * AttackIndex[x]
                + 0.25 * Start[x]
                + 0.20 * Turn[x]
                + 0.15 * Foot[x]
                + 0.05 * Engine[x]
                + (0.05 * max(0, Start[x] - Start[x-1]) if x > 0 else 0)
            ),
            reverse=True
        )
        
                
        AttackSuccess = 0
        AttackFail = 0
        
        if len(attackers) > 0:
        
            atk = attackers[0]
        
            if atk > 0:
        
                # ===============================
                # ① スタート勝ち（まくり）
                # ===============================
                st_win = (
                    Start[atk] > Start[atk-1] + 0.015
                )
        
                # ===============================
                # ② ターン勝ち（差し）
                # ===============================
                turn_win = (
                    Turn[atk] > Turn[atk-1] + 0.03
                    and Start[atk] >= Start[atk-1] - 0.02
                )
        
                # ===============================
                # ③ 展開勝ち
                # ===============================
                flow_win = (
                    Start[atk-1] < min(Start) + 0.01
                    or StartCollapse == 1
                )
        
                # ===============================
                # ④ 攻めの強さ（追加部分）
                # ===============================
                power = AttackIndex[atk] - AttackIndex[atk-1]
                
                power_win = (
                    power > 0.04
                    and (
                        Foot[atk] > Foot[atk-1]
                        or Turn[atk] > Turn[atk-1]
                    )
                )
                        
                # ===============================
                # ★ 成功判定
                # ===============================
                if (
                    st_win
                    or turn_win
                    or flow_win
                    or power_win
                ):
                    AttackSuccess = 1
        
                # ===============================
                # ★ 失敗判定
                # ===============================
                if (
                    Start[atk] < Start[atk-1] - 0.02
                    and Turn[atk] < Turn[atk-1] - 0.02
                ):
                    AttackFail = 1
                    
        AttackWeak = 0

        if len(attackers) > 0:
        
            atk = attackers[0]
        
            if atk > 0:
        
                # ===============================
                # ■ 攻めてるか
                # ===============================
                attack_try = (
                    Start[atk] >= Start[atk-1] - 0.02
                    or Turn[atk] >= Turn[atk-1] - 0.02
                )
        
                # ===============================
                # ■ 勝ち切れてない
                # ===============================
                not_win = (AttackSuccess == 0)
        
                # ===============================
                # ■ 完全失敗ではない
                # ===============================
                not_fail = not (
                    Start[atk] < Start[atk-1] - 0.03
                    and Turn[atk] < Turn[atk-1] - 0.03
                )
        
                # ===============================
                # ★ 弱攻め成立
                # ===============================
                if attack_try and not_win and not_fail:
                    AttackWeak = 1
                    
        # ★ 弱攻めフィルター（ここに入れる）
        if AttackWeak == 1:
        
            if (
                AttackIndex[atk] < AttackIndex[atk-1] - 0.07
                and Foot[atk] < Foot[atk-1] - 0.05
            ):
                AttackWeak = 0
                    
        # ===============================
        # ★ モード初期制御（ここ重要）
        # ===============================
        if mode == "no":
            DAS = 0
            AttackSuccess = 0
            AttackWeak = 0
        
        elif mode == "weak":
            AttackWeak = 1
            AttackSuccess = 0
        
            # ★ 攻めスコアを少し抑える
            DAS *= 0.7
        
        elif mode == "attack":
            pass
                    
        # ===============================
        # ★ 弱攻め判定（追加）
        # ===============================
        
        atk = attackers[0] if len(attackers) > 0 else 0
        
        if atk > 0:

            st_cond = Start[atk] > Start[atk-1] + 0.005
            turn_cond = Turn[atk] > Turn[atk-1] + 0.01
        
            if st_cond or turn_cond:
        
                # ★ 弱すぎる攻めは除外
                if AttackIndex[atk] > AttackIndex[atk-1] - 0.05:
                    AttackWeak = 1
                
        # ===============================
        # ★ 疑似主役（弱攻め）
        # ===============================
        WeakLeader = None
        
        if (
            AttackWeak == 1
            and AttackSuccess == 0
            and DAS > WEAK
        ):
            WeakLeader = max(
                range(2,5),
                key=lambda i: (
                    0.40 * AttackIndex[i]
                    + 0.30 * Start[i]
                    + 0.20 * Turn[i]
                    + 0.10 * Foot[i]
                )
            )
        
        
        # ===============================
        # ★ 外クラスタ
        # ===============================
        OuterCluster = max(CPI[3:6]) - min(CPI[3:6])
        OuterClusterFlag = 1 if OuterCluster <= 0.06 else 0
        
        
        # ===============================
        # ★ 6頭検知フラグ
        # ===============================
        SixHeadFlag = 0
        
        if (
            CPI[5] >= max(CPI[3:6]) - 0.01
            and AttackIndex[5] >= max(AttackIndex[3:6]) - 0.03
            and Start[5] >= Start[3] - 0.01
            and Engine[5] >= 0.58
            and (
                InsideSurvival[0] < 0.55
                or Start[0] < Start[1] - 0.03
            )
        ):
            SixHeadFlag = 1

        # ===============================
        # MID CLUSTER
        # ===============================
        
        MidCluster = max(CPI[1:4]) - min(CPI[1:4])
        MidClusterFlag = 1 if MidCluster <= 0.05 else 0
        
        PerformanceSpread = max(CPI) - min(CPI)
        StartSpread = max(Start) - min(Start)
        
        InsideCollapse = 1 if (
            Start[0] < max(Start[1:4]) - 0.04
            and OuterClusterFlag == 1
        ) else 0
        
        
        # ===============================
        # EXHIBIT LEADER
        # ===============================
        
        min_exst = min(EST)
        
        ExhibitLeader = [0]*6
        
        for i in range(6):
            if EST[i] <= min_exst + 0.01:
                ExhibitLeader[i] = 1
        
        
        # ===============================
        # SASHI CHANCE
        # ===============================
        
        SashiGap = [0]*6
        SashiFlag = [0]*6
        
        for i in range(1,6):
            SashiGap[i] = max(0, Start[i] - Start[i-1])
        
            if SashiGap[i] > 0.02 and Turn[i] >= Turn[i-1] - 0.01:
                SashiFlag[i] = 1    
        # ===============================
        # ATTACK FLAG
        # ===============================

        TwoLaneAttackFlag = 1 if (
            Start[1] >= Start[0] - 0.01
            and Turn[1] >= Turn[0] - 0.02
        ) else 0
        
        ThreeLaneAttackFlag = 1 if (
            Start[2] >= Start[1] - 0.01
            and Turn[2] >= Turn[1] - 0.02
        ) else 0
        
        FourLaneAttackFlag = 1 if (
            Start[3] >= max(Start[1], Start[2]) - 0.02
            and Turn[3] >= max(Turn[1], Turn[2]) - 0.02
        ) else 0

        # ===============================
        # ATTACK SCORE
        # ===============================

        TwoLaneAttackScore = (
            0.22 * TwoLaneAttackFlag +
            0.28 * max(0, Start[1] - Start[0]) +
            0.22 * max(0, AttackCPI[1] - AttackCPI[0]) +
            0.15 * max(0, Engine[1] - Engine[0]) +
            0.13 * max(0, Turn[1] - Turn[0])
        )
        
        ThreeLaneAttackScore = (
            0.22 * ThreeLaneAttackFlag +
            0.28 * max(0, Start[2] - Start[1]) +
            0.22 * max(0, AttackCPI[2] - AttackCPI[1]) +
            0.15 * max(0, Engine[2] - Engine[1]) +
            0.13 * max(0, Turn[2] - Turn[1])
        )
        
        FourLaneAttackScore = (
            0.22 * FourLaneAttackFlag +
            0.28 * max(0, Start[3] - Start[2]) +
            0.22 * max(0, AttackCPI[3] - AttackCPI[2]) +
            0.15 * max(0, Engine[3] - Engine[2]) +
            0.13 * max(0, Turn[3] - Turn[2])
        )
        
        OutsideFlow = (
            0.6 * ThreeLaneAttackScore +
            0.8 * FourLaneAttackScore
        )
        
        DAS = (
            0.6 * max(ThreeLaneAttackScore, FourLaneAttackScore)
            +
            0.4 * (ThreeLaneAttackScore * FourLaneAttackScore)
            +
            0.3 * (TwoLaneAttackScore * ThreeLaneAttackScore)
        )
        
        if AttackSuccess == 0:
            DAS *= 0.70
            
        AttackFlag = 1 if DAS > 0.08 else 0

        if DAS <= 0.08:
            AttackLevel = 0
        elif DAS <= 0.13:
            AttackLevel = 1
        else:
            AttackLevel = 2
        
        # ===============================
        # ★ 崩れは攻め扱い（主トリガー）
        # ===============================
        if StartCollapse == 1:
            AttackWeak = 1
            DAS = max(DAS, 0.08)
        
        # ===============================
        # ★ 疑似攻め（微調整）
        # ===============================
        PseudoAttack = max([
            max(0, Start[2] - Start[1]),
            max(0, Start[3] - Start[2]),
            max(0, Start[4] - Start[3])
        ])
        
        DAS += PseudoAttack * 0.05  
        
        # ===============================
        # ★ attackers救済（正しい位置）
        # ===============================
        if len(attackers) == 0 and DAS > 0.09:

            atk = max(
                range(2,5),
                key=lambda i: (
                    0.6 * Start[i] +
                    0.25 * Turn[i] +
                    0.15 * Foot[i]
                )
            )
        
            attackers.append(atk)
        
        # ===============================
        # ★ ズレ展開フラグ（NEW）
        # ===============================
        ZureWeak = (
            AttackWeak == 1
            and AttackSuccess == 0
            and Start[1] >= Start[0] - 0.01
            and max(Start[3:6]) >= Start[2] - 0.01
        )
        
        ZureSilent = (
            AttackSuccess == 0
            and DAS < 0.06
            and max(Start) - min(Start) > 0.05
            and InsideSurvival[0] < 0.65
        )
        
        ZureFlag = ZureWeak or ZureSilent
    
            
        debug_log.append(("attackers", attackers))
        debug_log.append(("AttackWeak", AttackWeak))
        debug_log.append(("AttackSuccess", AttackSuccess))
        debug_log.append(("DAS", round(DAS,4)))
        debug_log.append(("WEAK/MID/STRONG", (WEAK, MID, STRONG)))
        debug_log.append(("DAS", round(DAS,4)))
        
        # ===============================
        # ★ 弱イン判定（追加）
        # ===============================
        WeakInside = (
            Skill[0] < 0.48
            or Start[0] < max(Start[1:3]) - 0.015
            or InsideSurvival[0] < 0.58
            or ExST[0] >= 0.25
        )
        
        # ===============================
        # ★ スタート崩壊検知（最重要）
        # ===============================
        
        if Start[0] < max(Start[1:4]) - 0.03:
            StartCollapse = 1
        
        # ===============================
        # ★ 疑似展開（補助だけ）
        # ===============================
        PseudoAttack2 = max([
            max(0, Start[2] - Start[1]),
            max(0, Start[3] - Start[2]),
            max(0, Start[4] - Start[3])
        ])
        
        # ★ 崩壊時は軽く補助だけ
        if StartCollapse == 1:
            DAS += PseudoAttack2 * 0.05
        
        # ===============================
        # ★ 無風判定（シンプル版）
        # ===============================
        NoAttackFlag = 1
        
        if (
            AttackSuccess == 1
            or DAS > WEAK
            or max(Start) - min(Start) >= 0.06
            or WeakInside
            or StartCollapse == 1
        ):
            NoAttackFlag = 0
    
        
        # ★ 無風時のズレ制御（ここに入れる）
        if NoAttackFlag == 1:
            ZureFlag = ZureWeak or ZureSilent
        elif DAS > 0.04:
            ZureFlag = True
            
        # ===============================
        # ★ 外スルーフラグ（追加）
        # ===============================
        OuterSlip = (
            AttackWeak == 1
            and AttackSuccess == 0
            and DAS < MID
            and max(Start[4:6]) >= max(Start[2:6]) - 0.01
        )
            
        # ===============================
        # ★ レースモード（最終版）
        # ===============================
        
        has_attack = (
            DAS > WEAK
            or AttackSuccess == 1
        )
        
        if NoAttackFlag == 1:
            RaceMode = "no_attack"
        
        elif has_attack and AttackSuccess == 1:
            RaceMode = "attack_success"
        
        elif has_attack and AttackSuccess == 0:
        
            if AttackWeak == 1 and DAS < MID:
                RaceMode = "attack_weak"
        
            else:
                crash_flag = any(
                    (
                        Start[atk] < Start[atk-1] - 0.02
                        and Turn[atk] < Turn[atk-1] - 0.02
                    )
                    for atk in attackers
                )
        
                if crash_flag:
                    RaceMode = "attack_crash"
                else:
                    RaceMode = "attack_fail"
        
        else:
            RaceMode = "no_attack"
                
        # ===============================
        # 攻め主体判定（改良版）
        # ===============================

        Attack2 = 1 if (
            Start[1] >= Start[0] - 0.01
            and AttackIndex[1] > AttackIndex[0]
            and (Foot[1] >= Foot[0] or Engine[1] >= Engine[0])
        ) else 0
        
        
        Attack3 = 1 if (
            Start[2] >= Start[1] - 0.01
            and AttackIndex[2] > AttackIndex[1]
            and (Foot[2] >= Foot[1] or Engine[2] >= Engine[1])
            and (
                CLS[2] in ["A1","A2"]
                or (
                    ExST[2] <= 0.08
                )
            )
        ) else 0
        
        
        Attack3Power = (
            0.5 * max(0, Start[2] - Start[1]) +
            0.3 * max(0, AttackIndex[2] - AttackIndex[1]) +
            0.2 * max(0, Turn[2] - Turn[1])
        )
        
        
        InsideBreak = 1 if (
            Start[0] < Start[1] - 0.02
            and Attack3 == 1
        ) else 0
        
        # ===============================
        # CHAOS CORE
        # ===============================

        OuterPower = (
            0.4 * max(CPI[3:6]) +
            0.3 * sorted(CPI[3:6])[-2] +
            0.3 * (sum(CPI[3:6]) / 3)
        )
        
        InsideWeak = 1 - InsideSurvival[0]
        
        ChaosScore = (
            0.20 * OuterPower +
            0.25 * InsideWeak +
            0.18 * StartSpread +
            0.14 * PerformanceSpread +
            0.07 * TwoLaneAttackFlag +
            0.10 * ThreeLaneAttackFlag +
            0.07 * FourLaneAttackFlag +
            0.06 * MidClusterFlag
        )
        
        ChaosScore = max(0, min(1, ChaosScore))

        if ChaosScore < 0.45:
            chaos_weight = 0.75
        elif ChaosScore < 0.65:
            chaos_weight = 1.0
        else:
            chaos_weight = 1.25
            
        # ===============================
        # AUTO MODE 判定
        # ===============================
        
        race_score = 0

        # ===============================
        # イン弱さ（強め）
        # ===============================
        if Skill[0] < 0.48:
            race_score += 1.2
        
        if Start[0] < max(Start[1:3]) - 0.02:
            race_score += 1.0
        
        if InsideSurvival[0] < 0.55:
            race_score += 1.0
        
        
        # ===============================
        # スタートばらつき
        # ===============================
        if max(Start) - min(Start) > 0.06:
            race_score += 0.8
        
        
        # ===============================
        # 外の強さ
        # ===============================
        if max(CPI[3:6]) > CPI[0]:
            race_score += 1.0
        
        
        # ===============================
        # 展開（ここ重要）
        # ===============================
        if AttackLevel == 2:
            race_score += 1.2
        
        elif AttackLevel == 1:
            race_score += 0.6
        
        
        # ===============================
        # 最終判定
        # ===============================
        use_mode = "ana" if race_score >= 2.2 else "safe"

        
        # ===============================
        # STAGE17
        # ===============================

        AvgStart=sum(Start)/6

        StartBoost=[]

        for i in range(6):

            value = 1 + (0.12 + 0.18*ChaosScore) * (Start[i] - AvgStart)

            value=max(0.80,value)

            StartBoost.append(value)

        DynamicInsideFactor=1

        if StartSpread >= 0.12:
            DynamicInsideFactor = 0.78
        elif StartSpread >= 0.08:
            DynamicInsideFactor = 0.88

        DynamicInsideFactor=max(0.60,DynamicInsideFactor)

        # ===== イン過信抑制 =====

        if (
            NoAttackFlag == 0
            and AttackSuccess == 1
            and CPI[1] >= CPI[0] - 0.05
            and Start[1] <= Start[0] + 0.04
            
        ):
            DynamicInsideFactor *= 0.92

        LaneWin=[

            0.55*DynamicInsideFactor*(1-0.25*ChaosScore),
        
            0.19+(0.45*(1-DynamicInsideFactor)*0.40)*(1+0.20*ChaosScore),
        
            0.18+(0.45*(1-DynamicInsideFactor)*0.32)*(1+0.25*ChaosScore),  # ←UP
        
            0.15+(0.45*(1-DynamicInsideFactor)*0.22)*(1+0.30*ChaosScore),  # ←UP
        
            0.08+(0.45*(1-DynamicInsideFactor)*0.08)*(1+0.35*ChaosScore),
        
            0.05+(0.45*(1-DynamicInsideFactor)*0.04)*(1+0.40*ChaosScore)
        
        ]

        # ===============================
        # ★ FirstScoreフラグ箱
        # ===============================
        
        def norm(arr):
            mn = min(arr)
            mx = max(arr)
            return [(x - mn) / (mx - mn + 1e-6) for x in arr]
        
        Turn_n = norm(Turn)
        Foot_n = norm(Foot)
        
        FirstScore_no = []
        FirstScore_attack = []
        
        for i in range(6):
        
            val = (
                0.32*Start[i]
                +0.16*Skill[i]
                +0.14*Foot_n[i]
                +0.18*Turn_n[i]
                +0.12*LaneWin[i]
            )
            
            if AttackFlag:
                boost = max(0, AttackIndex[i] - AttackIndex[1])  # ←2基準
                val *= (1 + 0.10 * boost)
            # ノーアタック世界
            val_no = val
            if i >= 4:
                val_no *= 0.05
        
            # アタック世界
            val_at = val
            if i >= 4:
                if outer_ok[i]:
                    val_at *= 1.05
                else:
                    val_at *= 0.3
        
            FirstScore_no.append(val_no)
            FirstScore_attack.append(val_at)
        
        
        P1_no = normalize_sum(FirstScore_no)
        P1_at = normalize_sum(FirstScore_attack)
        
        w_no = 0.4
        w_at = 0.6
        
        P1 = [
            w_no * P1_no[i] + w_at * P1_at[i]
            for i in range(6)
        ]
        
        # ★ここに入れる
        if NoAttackFlag == 0 and DAS > 0.08:

            reduction = 0.95 - 0.15 * (DAS - 0.08)   # ←弱くする
            reduction = max(0.88, reduction)         # ←底上げ
        
            if InsideSurvival[0] > 0.55:
                reduction += 0.02   # ←少し弱く
        
            P1[0] *= reduction
        
        # 最後に正規化（これ必須）
        P1 = normalize_sum(P1)
                
        # ===============================
        # ★ 強制2頭分岐
        # ===============================
        heads = sorted(range(6), key=lambda i: P1[i], reverse=True)
        
        main_head = heads[0]
        second_head = heads[1]
        
        force_heads = [main_head]
        
        # 差がそこまで大きくないなら2頭採用
        if P1[second_head] > P1[main_head] * 0.7:
            force_heads.append(second_head)

        
        # ===============================
        # ★ P1圧縮ガード（完成版）
        # ===============================
        P1_pre = P1.copy()
        
        debug_log.append(("=== FIRST ===", ""))

        for i in range(6):
            debug_log.append((
                f"{i+1}",
                {
                    "attack": round(AttackIndex[i],4),
                    "start": round(Start[i],4),
                    "P1": round(P1_pre[i],4)
                }
            ))
        
        top = sorted(P1_pre, reverse=True)
        
        # 上位拮抗なら上位3艇を少し持ち上げる
        if top[0] - top[1] < 0.12:
        
            for i in range(6):
                if P1_pre[i] in top[:3]:
                    P1[i] *= 1.08
        
        
        SecondCore = None

        for i in range(6):
            if i != 0 and P1[i] >= P1[0] * 0.75:
                SecondCore = i
                break

        # ===============================
        # ATTACK BOOST
        # ===============================

        OuterPowerCheck = max(AttackCPI[3:6])

        AttackBoost1 = max(
        0.70,
        1 - 0.25 * max(
        TwoLaneAttackScore,
        ThreeLaneAttackScore,
        FourLaneAttackScore
        )
        )

        AttackBoost2 = 1 + 0.20 * TwoLaneAttackScore
        AttackBoost3 = 1 + 0.30 * ThreeLaneAttackScore
        AttackBoost4 = 1 + 0.25 * FourLaneAttackScore
        if AttackSuccess == 1:
            AttackBoost5 = 1 + 0.35 * DAS
            AttackBoost6 = 1 + 0.25 * DAS
        else:
            AttackBoost5 = 1.0
            AttackBoost6 = 1.0

        AttackBoost=[
        AttackBoost1,
        AttackBoost2,
        AttackBoost3,
        AttackBoost4,
        AttackBoost5,
        AttackBoost6
        ]
        


        if OuterPowerCheck < 0.55:
            AttackBoost[3] *= 0.85
            AttackBoost[4] *= 0.80
            AttackBoost[5] *= 0.75

        outer_attackers = AttackIndex[3:6]

        max_outer = max(outer_attackers)

        main_attacker = None

        if OuterClusterFlag == 1:
            for j in range(3,6):
                AttackBoost[j] *= 1.10

        if max_outer > AttackIndex[2] + 0.03:
            main_attacker = outer_attackers.index(max_outer) + 3

        # ===============================
        # ★ 無風時は展開を完全停止（これが本質）
        # ===============================
        if NoAttackFlag == 1:
            AttackBoost = [1.0 + 0.05*(Start[i] - avg(Start)) for i in range(6)]

        # ===============================
        # 展開モデル
        # ===============================

        CrashFactor=[1.0]*6
        SashiBoost=[1.0]*6
        
        if NoAttackFlag == 1:
            CrashFactor = [1.0]*6
            SashiBoost = [1.0]*6
            main_attacker = None

        if main_attacker is not None:

            attack_power = DAS

            # 前潰れ
            for j in range(main_attacker):
                CrashFactor[j] = 1 - 0.15*attack_power

            # 差し
            for j in range(main_attacker+1,6):
                SashiBoost[j] = 1 + 0.12*attack_power
          
        LaneCPI=[]

        for i in range(6):

            if Active[i] == 0:
                LaneCPI.append(0)
                continue

            value=(
                CPI[i]*
                LaneWin[i]*
                (0.8+0.2*StartBoost[i]*chaos_weight)*
                CrashFactor[i]*
                SashiBoost[i]*
                AttackBoost[i]
            )
            
            if NoAttackFlag == 1 and i >= 4:
                value *= 0.75
            # ★ ここ追加（超重要）
            


            if i == 0 and InsideBreak == 1:
                value *= 0.70

            if i == 0 and CLS[0] in ["A1","A2"]:
                value *= 1.15

            # イン崩壊
            if InsideCollapse == 1:
                if i <= 2:
                    value *= 0.88

            # 外まとまり
            if OuterClusterFlag == 1:
                if i >= 4:
                    value *= 1.01
                    

            # ===============================
            # 2まくり（弱め）
            # ===============================
            if Attack2 == 1:

                if i == 0:
                    value *= 0.90

                if i == 1:
                    value *= 1.18

                if i == 2:
                    value *= 0.92

                if i >= 3:
                    value *= 1.05

            # ===============================
            # 3まくり（弱め）
            # ===============================
            if Attack3 == 1:

                if i == 0:
                    value *= 0.85

                if i == 1:
                    value *= 0.90

                if i == 2:

                    if CLS[2] in ["B1","B2"]:

                        if Attack3Power < 0.05:
                            value *= 0.90

                        elif Attack3Power < 0.10:
                            value *= 1.00

                        else:
                            value *= 1.10

                    else:
                        value *= 1.10

                if i >= 3:
                    value *= 1.06

            if Attack3 == 1 and CLS[2] in ["B1","B2"] and i >= 4:
                value *= 0.85

            if Attack3 == 1 and Attack3Power < 0.08:

                if i == 1:
                    value *= 1.20

                if i == 0:
                    value *= 1.05
            
            # 展開艇補正
            if ExhibitLeader[i] == 1 and i >= 3 and NoAttackFlag == 0:
                value *= 1.08

            # 差し補正
            if i==1:
                value*=1+0.22*SashiGap[i]
            elif i==2:
                value*=1+0.15*SashiGap[i]
            elif i==3:
                value*=1+0.08*SashiGap[i]
            elif i==4:
                value*=1+0.04*SashiGap[i]
        
            if main_attacker is not None:

                if i == main_attacker:
                    value = value*(1+0.20*DAS)

                elif i > main_attacker:
                    value = value*(1+0.08*DAS)

                elif i == main_attacker - 1:
                    value *= (1+0.06*DAS)

            LaneCPI.append(value)
            
                
        
            
        #デバック
        FirstScore = [
            w_no * FirstScore_no[i] + w_at * FirstScore_attack[i]
            for i in range(6)
        ]
        
        FinalFirst = [FirstScore[i] for i in range(6)]

        
        debug_log.append(("FirstScore", [round(x,3) for x in FinalFirst]))
        debug_log.append(("順位", sorted(range(6), key=lambda i: FinalFirst[i], reverse=True)))
        debug_log.append(("CPI", [round(x,3) for x in CPI]))
        debug_log.append(("Start", [round(x,3) for x in Start]))
        start_rank = sorted(range(6), key=lambda i: (-Start[i], i))
        debug_log.append(("StartRank", start_rank))
        
        # ★ デバッグ追加（ここ！！）
        if len(debug_log) > 50:
            debug_log = debug_log[-50:]
        debug_log.append(("First_final", [round(x,4) for x in FinalFirst]))
        
        
        TotalFirst = sum([FinalFirst[i] for i in range(6) if Active[i]==1])
        
        TotalFirst = sum([FinalFirst[i] for i in range(6) if Active[i]==1])
    
            
        # ===============================
        # ★ 外の能力ゴリ押し禁止
        # ===============================
        for i in range(4,6):
        
            if DAS < 0.12:
        
                # 能力だけで1位になってる場合
                if P1[i] == max(P1):
                    P1[i] *= 0.55
        
        # ★ 無風時：イン優先ロック（修正版）
        if NoAttackFlag == 1:
        
            if InsideSurvival[0] >= 0.55:
        
                # 2と3を同時に抑える（これが本質）
                if P1[1] > P1[0] * 0.80:
                    P1[1] *= 0.80
        
                if P1[2] > P1[0] * 0.85:
                    P1[2] *= 0.75
                
        # ===============================
        # ★ 外の頭禁止（最重要）
        # ===============================
        for i in range(4,6):
            if not FrontBreak and DAS < 0.10:
                P1[i] *= 0.50
        
            can_break = (
                DAS > 0.12
                or AttackSuccess == 1
                or StartCollapse == 1
                or max(WallBreak) > 0.25
                or Start[1] < Start[0] - 0.02
                or Start[2] < Start[1] - 0.02
                or max(Start[1:4]) - Start[0] > 0.04

            )
        

        # ===============================
        # トップ集中ブースト
        # ===============================
        top = max(P1)

        for i in range(6):
            if P1[i] == top:
                if ChaosScore < 0.45:
                    P1[i] *= 1.05   # ←弱める
                else:
                    P1[i] *= 1.02   # ←ほぼ消す
            
        # ===== 内繰り上がり補正（ここに入れる）=====
        inner_mode = (
            AttackSuccess == 1
            and DAS > 0.12
            and StraightTime[5] >= 7.9
        )
        
        if inner_mode:
            P1[0] *= 0.8   # 1削る
            P1[1] *= 1.15  # 2上げる（重要）
            P1[2] *= 1.2   # 3上げる
        
        # ★ ここに追加
        if (
            AttackSuccess == 1
            and DAS > 0.13
            and Start[0] < Start[2]
            and Turn[0] < Turn[2]   # ←これ追加すると神精度
        ):
            P1[0] *= 0.88
            
        # ===============================
        # ★ FINAL P1（ここが正解）
        # ===============================
        
        # ① 強制（2頭に寄せる）
        for i in force_heads:
            P1[i] += 0.01 #効かなければ1.4〜1.5までOK
        
        # ② 差分分散（これが効く）
        top = max(P1)
        for i in range(6):
            if P1[i] >= top * 0.7:
                P1[i] *= 1.05   
        
        # ③ 最後に1回だけ正規化
        P1 = normalize_sum(P1)
        
        # ===============================
        # ★ 1位保護（条件付き）
        # ===============================
        top_idx = P1.index(max(P1))
        
        if (
            top_idx == 0
            and NoAttackFlag == 1
            and InsideSurvival[0] >= 0.55
            and Start[1] >= Start[0] - 0.02
        ):
        
            if P1[1] > P1[0] * 0.90:
                P1[1] *= 0.85
        
            if P1[2] > P1[0] * 0.95:
                P1[2] *= 0.90
                
                
            for i in force_heads:
                P1[i] *= 1.4
            # 再正規化
            total = sum(P1)
            P1 = [p / total for p in P1]
                

        LaneBonus=[0.08,0.075,0.07,0.065,0.06,0.055]

        SecondScore=[
        0.33*Turn[i]+
        0.27*Foot[i]+
        0.20*Engine[i]+
        0.10*Velocity[i]+
        0.10*LaneBonus[i]
        + 0.05*Start[i]
        for i in range(6)
        ]
        
        # ===============================
        # ★ 攻め強度分類（整理版）
        # ===============================
        weak_attack = (
            0.06 < DAS <= 0.09
            and NoAttackFlag == 0
        )
        
        mid_attack = (
            0.09 < DAS <= 0.13
            and NoAttackFlag == 0
        )
        
        strong_attack = (
            DAS > 0.13
            and NoAttackFlag == 0
        )
        
        # ===============================
        # ★ 外残りフラグ（5・6用）
        # ===============================
        
        FlowOuter = (
            DAS > MID
            or OuterClusterFlag == 1
        )
        
        FiveFlowFlag = (
            FlowOuter
            and Foot[4] >= 0.50
            and CPI[4] >= 0.48
            and Start[4] >= Start[2] - 0.02
        )
        
        SixFlowFlag = (
            FlowOuter
            and Foot[5] >= 0.52
            and CPI[5] >= 0.50
            and Start[5] >= Start[3] - 0.02
        )
        
        # ===============================
        # ★ 攻め状態分類（追加）
        # ===============================
        
        MidAttack = (
            0.07 < DAS <= 0.13
        )
        
        
        SecondAdj = SecondScore.copy()
        SecondAdj_base = SecondAdj.copy()
        # ★ デバッグ（ここが正解）
        debug_log.append(("SecondAdj_pre", [round(x,4) for x in SecondAdj]))
        debug_log.append(("=== SECOND ===", ""))

        for i in range(6):
            debug_log.append((
                f"{i+1}",
                {
                    "attack": round(AttackIndex[i],4),
                    "start": round(Start[i],4),
                    "Second": round(SecondAdj[i],4)
                }
            ))
        # ===============================
        # ★ 2着モード制御（ここ重要）
        # ===============================
        
        if mode == "no":
            for i in range(4,6):
                SecondAdj[i] *= 0.75
        
        elif mode == "weak":
            for i in range(4,6):
                if DAS < 0.10:
                    SecondAdj[i] *= 0.85
        
        elif mode == "attack":
            for i in range(4,6):
                SecondAdj[i] *= 1.03
                
        
        
        
        ThirdAdj = [
            1.06,  # 1
            1.05,  # 2
            1.08,  # 3
            1.05,  # 4
            0.97,  # 5
            0.95   # 6
        ]
        
        debug_log.append(("ThirdAdj_pre", [round(x,4) for x in ThirdAdj]))
        debug_log.append(("=== THIRD ===", ""))

        for i in range(6):
            debug_log.append((
                f"{i+1}",
                {
                    "attack": round(AttackIndex[i],4),
                    "start": round(Start[i],4),
                    "Third": round(ThirdAdj[i],4)
                }
            ))
        # ===============================
        # ★ 3着モード制御
        # ===============================
        
        if mode == "no":
            for i in range(4,6):
                ThirdAdj[i] *= 0.85
        
        elif mode == "weak":
            for i in range(4,6):
                if DAS < 0.10:
                    ThirdAdj[i] *= 0.90
        
        elif mode == "attack":
            for i in range(4,6):
                ThirdAdj[i] *= 1.05
        
     
        # ===============================
        # ★ 6の最低制限（ここに入れる）
        # ===============================
        if Fcount[5] >= 2 and Start[5] < Start[3]:
            SecondAdj[5] *= 0.6
            ThirdAdj[5] *= 0.6
        
        # ===============================
        # ★ 攻め失敗（修正版）
        # ===============================
        if RaceMode == "attack_fail":
        
            # インは少しだけ耐える（弱める）
            SecondAdj[0] *= 1.03
            ThirdAdj[0]  *= 1.02
        
            # 攻め艇はしっかり削る
            for atk in attackers:
                SecondAdj[atk] *= 0.88
                ThirdAdj[atk]  *= 0.90
        
            # 3が繰り上がる
            if CPI[2] >= CPI[1] - 0.03:
                SecondAdj[2] *= 1.08
                ThirdAdj[2]  *= 1.05
        
        
        # ===============================
        # ★ 攻め潰れ（これが本命）
        # ===============================
        if RaceMode == "attack_crash":
        
            # 1は残るけど少し弱る
            SecondAdj[0] *= 1.00
            ThirdAdj[0]  *= 0.97
        
            # 攻め艇は飛ぶ
            for atk in attackers:
                SecondAdj[atk] *= 0.75
                ThirdAdj[atk]  *= 0.80
        
            # 内が繰り上がる
            SecondAdj[1] *= 1.08
            ThirdAdj[1]  *= 1.05
        
            SecondAdj[2] *= 1.10
            ThirdAdj[2]  *= 1.08
        
            # 4が展開拾う（重要）
            if Start[3] >= Start[2] - 0.02:
                SecondAdj[3] *= 1.08
                ThirdAdj[3]  *= 1.12
        
            # 外は軽くだけ
            for i in range(4,6):
                ThirdAdj[i] *= 1.08
                
        
        
        # ===============================
        # ★ 無風処理（整理版）
        # ===============================
        if NoAttackFlag == 1:
        
            # 外は軽く削る
            for i in range(4,6):
                SecondAdj[i] *= 0.80
                ThirdAdj[i]  *= 0.85
        
            # ST順の安定構造
            for i in range(1,6):
        
                diff = Start[i] - Start[i-1]
        
                if diff > 0.03:
                    SecondAdj[i] *= 1.15
                    SecondAdj[i-1] *= 0.75
        
                elif diff > 0.02:
                    SecondAdj[i] *= 1.03
                    SecondAdj[i-1] *= 0.85
        
            # 2 vs センター
            idx2 = 1
            center = max(range(2,5), key=lambda i: CPI[i] + Start[i])
        
            diff = (
                0.5*(CPI[center] - CPI[idx2]) +
                0.5*(Start[center] - Start[idx2])
            )
        
            if diff > 0.02:
                SecondAdj[center] *= 1.12
                SecondAdj[idx2]   *= 0.90
        
            elif diff < -0.02:
                SecondAdj[idx2]   *= 1.10
                SecondAdj[center] *= 0.92
        
            else:
                SecondAdj[idx2]   *= 1.03
                SecondAdj[center] *= 1.03
        
                            
        # ===============================
        # ★ weakゾーンのイン2着制御（ここ追加）
        # ===============================
        if RaceMode == "attack_weak":
        
            st_loss = Start[0] < max(Start[1:3]) - 0.02
            weak_inside = InsideSurvival[0] < 0.55
            strong_enemy = max(CPI[1:3]) > CPI[0] + 0.03
        
            if st_loss and weak_inside and strong_enemy:
                SecondAdj[0] *= 0.65
            
            elif st_loss and (weak_inside or strong_enemy):
                SecondAdj[0] *= 0.75
            
            elif st_loss:
                SecondAdj[0] *= 0.85
            
                    
        # ===============================
        # ★ 攻め成功時の内側構造（統合版）
        # ===============================
        if AttackSuccess == 1 and DAS > WEAK and NoAttackFlag == 0:
        
            # --- 2コース復活 ---
            st_good = Start[1] >= max(Start[0], Start[2]) - 0.01
            perf_ok = CPI[1] >= (sum(CPI)/6) - 0.05
        
            if st_good and perf_ok:
                SecondAdj[1] *= 1.10   # ←少しだけ弱めた
        
            # --- イン2着制御 ---
            st_loss = Start[0] < Start[2]
            weak_inside = InsideSurvival[0] < 0.55
        
            if DAS > STRONG:
                if st_loss:
                    SecondAdj[0] *= 0.80
                else:
                    SecondAdj[0] *= 0.88
        
            elif AttackLevel == 2:
                if st_loss and weak_inside:
                    SecondAdj[0] *= 0.84
                elif st_loss:
                    SecondAdj[0] *= 0.90
                else:
                    SecondAdj[0] *= 0.94
        
            else:  # WEAK帯
                if st_loss:
                    SecondAdj[0] *= 0.94
                    
        # ===============================
        # ★ 攻め成功時のイン残り（3着）
        # ===============================
        if AttackSuccess == 1 and DAS > WEAK and NoAttackFlag == 0:
        
            st_loss = Start[0] < Start[2]
            weak_inside = InsideSurvival[0] < 0.55
        
            if DAS > STRONG:
                if st_loss:
                    ThirdAdj[0] *= 0.88
                else:
                    ThirdAdj[0] *= 0.92
        
            elif AttackLevel == 2:
                if st_loss and weak_inside:
                    ThirdAdj[0] *= 0.90
                elif st_loss:
                    ThirdAdj[0] *= 0.94
                else:
                    ThirdAdj[0] *= 0.96
        
            else:
                if st_loss:
                    ThirdAdj[0] *= 0.96
                    
        # ===============================
        # ★ 外の流入＋制御（統合版）
        # ===============================
        if AttackSuccess == 1 and NoAttackFlag == 0:
        
            for i in range(4,6):
        
                # ----------------------
                # ① 弱展開は強制カット
                # ----------------------
                if DAS < 0.06:
                    SecondAdj[i] *= 0.60
                    continue
        
                elif DAS < 0.09:
                    SecondAdj[i] *= 0.70
                    continue
        
                # ----------------------
                # ② 流入判定
                # ----------------------
                
                if outer_ok[i]:

                    if DAS > STRONG:
                    
                        if i == 4:
                            SecondAdj[i] *= 1.05
                        else:  # 6
                            SecondAdj[i] *= 1.07
                    
                    elif AttackLevel == 2:
                    
                        if i == 4:
                            SecondAdj[i] *= 1.03
                        else:
                            SecondAdj[i] *= 1.04
                    
                    else:
                        SecondAdj[i] *= 1.00
                
                else:
                
                    if i == 4:
                        SecondAdj[i] *= 0.92
                    else:
                        SecondAdj[i] *= 0.85
                # ----------------------
                # ③ 壁チェック（最重要）
                # ----------------------
                if i == 4:
                    if (
                        max(CPI[2:4]) > CPI[4] - 0.02
                        and max(Turn[2:4]) >= Turn[4] - 0.02
                    ):
                        SecondAdj[4] *= 0.85
                        ThirdAdj[4]  *= 0.88
        
                if i == 5:
                    if (
                        max(CPI[2:5]) > CPI[5] - 0.03
                        and max(Turn[2:5]) >= Turn[5] - 0.02
                    ):
                        SecondAdj[5] *= 0.75
                        ThirdAdj[5]  *= 0.80
        
        # ===============================
        # ★ 攻め成立時の前削り（整理版）
        # ===============================
        if AttackSuccess == 1 and DAS > WEAK and NoAttackFlag == 0:
        
            for i in range(0,2):  # 1・2コース
        
                # 3に対して明確に遅れてる
                if Start[i] < Start[2] - 0.03:
                    SecondAdj[i] *= 0.85
        
                elif Start[i] < Start[2] - 0.02:
                    SecondAdj[i] *= 0.90
        
        
        # ===============================
        # ★ 内の処理（整理版）
        # ===============================
        
        # 弱攻め：イン残るが控えめ
        if weak_attack:
            if InsideSurvival[0] >= 0.50 and Start[0] >= Start[2] - 0.03:
                SecondAdj[0] *= 1.10
                ThirdAdj[0] *= 1.05
        
        # 中攻め：条件付きで少しだけ
        elif mid_attack:
            if InsideSurvival[0] >= 0.45 and P1[0] < 0.25:
                SecondAdj[0] *= 1.08
                ThirdAdj[0] *= 1.04
        
        # 強攻め：イン削る（しっかり）
        elif strong_attack:
            SecondAdj[0] *= 0.85
            ThirdAdj[0] *= 0.92
        
        
        # ===============================
        # ★ イン残り（統合版）
        # ===============================
        if NoAttackFlag == 0:
        
            st_ok = Start[0] >= Start[2] - 0.03
            survive_ok = InsideSurvival[0] >= 0.48
        
            # --- 中攻め：イン普通に残る ---
            if mid_attack and st_ok and survive_ok and P1[0] < 0.25:
                SecondAdj[0] *= 1.12
                ThirdAdj[0] *= 1.05
        
            # --- 強攻め：2着は厳しいが3着は残る ---
            elif strong_attack and Skill[0] >= 0.45:
                SecondAdj[0] *= 0.95
                ThirdAdj[0] *= 1.08
                
        # ===============================
        # ★ 2の差し残り強化（整理版）
        # ===============================
        if (
            NoAttackFlag == 0
            and DAS > WEAK
            and Fcount[1] == 0
            and CPI[1] >= CPI[0] - 0.04
            and Start[1] >= Start[0] - 0.03
        ):
            SecondAdj[1] *= 1.12
                
        # ===============================
        # ★ 展開拾い（複数攻め・整理版）
        # ===============================
        if DAS > MID and NoAttackFlag == 0 and len(attackers) > 0:
        
            # 一番強い攻めを選ぶ
            main_atk = max(attackers, key=lambda x: AttackIndex[x])
        
            target = main_atk + 1
        
            if target < 6:
        
                # 前より遅くない（詰まってない）
                if Start[target] >= Start[main_atk] - 0.01:
        
                    SecondAdj[target] *= 1.08
                    ThirdAdj[target] *= 1.10
                    
        # ===============================
        # ★ 階級補正（整理版）
        # ===============================
        for i in range(6):
        
            if CLS[i] == "A1":
                SecondAdj[i] *= 1.06
                ThirdAdj[i]  *= 1.04
        
            elif CLS[i] == "A2":
                SecondAdj[i] *= 1.03
                ThirdAdj[i]  *= 1.02
        
            elif CLS[i] == "B1":
                pass  # 基準
        
            elif CLS[i] == "B2":
                SecondAdj[i] *= 0.95
                ThirdAdj[i]  *= 0.95
        
        # ===============================
        # ★ 会場補正（2着・整理版）
        # ===============================
        if venue == "多摩川":
            SecondAdj[0] *= 1.04
            SecondAdj[4] *= 1.06
        
        elif venue == "びわこ":
            SecondAdj[0] *= 1.05
            SecondAdj[1] *= 1.04
        
        elif venue == "常滑":
            SecondAdj[2] *= 1.06
            SecondAdj[3] *= 1.08
        
        elif venue == "桐生":
            SecondAdj[0] *= 1.05
            SecondAdj[1] *= 1.04
        
        elif venue == "住之江":
            if AttackLevel == 2:
                SecondAdj[3] *= 1.08
                SecondAdj[4] *= 1.06
                

        ThirdScore=[
        0.28*Velocity[i]+
        0.28*Foot[i]+
        0.20*Engine[i]+
        0.14*LaneBonus[i]+
        0.10*InsideSurvival[i]
        for i in range(6)
        ]
        
        
        # ===============================
        # ★ ST遅れでも3着残り（ここ）
        # ===============================
        for i in range(6):
            
        
            if (
                NoAttackFlag == 0
                and Start[i] < min(Start) + 0.01
                and CPI[i] >= 0.42
            ):
                ThirdAdj[i] *= 1.15
        
        for i in range(4,6):
            if NoAttackFlag == 1:
                continue
        
            if Foot[i] >= 0.48:
                ThirdAdj[i] *= 1.05
        
        for i in range(6):

            if i == 2 and NoAttackFlag == 0:
                if CPI[i] >= 0.45:
                    ThirdAdj[i] *= 1.18
        
        # ★ 攻め役の失敗残り（修正版）
        if AttackWeak == 1 and AttackSuccess == 0:
        
            for i in [2,3]:
                ThirdAdj[i] *= 1.08
        
    
        # ===============================
        # ★ インの2着・3着粘り復活（修正版）
        # ===============================
        if (
            CLS[0] in ["A1","A2"]
            and Start[0] >= 0.13
            and DAS < 0.10
        ):
        
            SecondAdj[0] *= 1.08
            ThirdAdj[0]  *= 1.05
        
        # ===============================
        # ★ 展開艇の3着流入（修正版）
        # ===============================
        if NoAttackFlag == 0 and DAS > WEAK:
        
            for i in range(6):
        
                # 攻めライン or その外
                if i >= 2:
        
                    if (
                        ExST[i] <= 0.08
                        and Start[i] >= Start[2] - 0.02
                    ):
                        ThirdAdj[i] *= 1.10
        
        # ===============================
        # ★ 3と4が競合 → 両方少し削る
        # ===============================
        if (
            DAS > WEAK
            and DAS < MID
            and abs(CPI[2] - CPI[3]) < 0.03
            and abs(Start[2] - Start[3]) < 0.02
        ):
        
            ThirdAdj[2] *= 0.95
            ThirdAdj[3] *= 0.95
        
        # ===============================
        # ★ 1の過剰残り抑制（ここ）
        # ===============================
        if (
            DAS > MID
            and Start[0] < Start[2] - 0.02
        ):
            ThirdAdj[0] *= 0.90
        
        # ===============================
        # ★ 2の残り復活（修正版）
        # ===============================
        if (
            NoAttackFlag == 0
            and DAS > WEAK
            and Start[1] >= Start[0] - 0.02
            and CPI[1] >= CPI[0] - 0.05
        ):
            SecondAdj[1] *= 1.10
            ThirdAdj[1] *= 1.06
    
        # ===== 3号艇の自然流入 =====

        if (
            0.43 <= CPI[2] <= 0.62
            and NoAttackFlag == 0
        ):
            ThirdAdj[2] *= 1.08
            
        # ===============================
        # ★ F持ち最終補正（修正版・位置変更）
        # ===============================
        for i in range(6):
        
            if Fcount[i] >= 1:
        
                if Fcount[i] == 1:
        
                    if CLS[i] == "A1":
                        factor = 0.98
                    elif CLS[i] == "A2":
                        factor = 0.96
                    elif CLS[i] == "B1":
                        factor = 0.94
                    else:
                        factor = 0.92
        
                elif Fcount[i] >= 2:
        
                    if CLS[i] == "A1":
                        factor = 0.93
                    elif CLS[i] == "A2":
                        factor = 0.90
                    elif CLS[i] == "B1":
                        factor = 0.87
                    else:
                        factor = 0.85
        
                # 差し役は少しだけ追加ペナ
                if i in [1,2]:
                    factor *= 0.97
        
                SecondAdj[i] *= factor
                ThirdAdj[i]  *= factor
                
        # ===============================
        # ★ イン中間残り（移動版）
        # ===============================
        if (
            FinalFirst[0] < max(FinalFirst) * 0.95
            and FirstScore[0] > max(FirstScore) * 0.75
            and InsideSurvival[0] >= 0.50
        ):
            SecondAdj[0] *= 1.10
            ThirdAdj[0]  *= 1.06
        
        
        SecondAdj_final = SecondAdj.copy()
        ThirdAdj_final = ThirdAdj.copy()
            
        # ===============================
        # ★ 非頭艇の残り補正（最重要）
        # ===============================
        
        for a in range(6):
            
            if a not in force_heads:
                continue
        
            if Active[a] == 0:
                continue
        
            if P1[a] < max(P1) * (0.65 + 0.15*(1-ChaosScore)):
                continue
        
        
            # ===============================
            # ★ local生成
            # ===============================
            SecondAdj_local = SecondAdj_final.copy()
            ThirdAdj_local  = ThirdAdj_final.copy()
            
            debug_log.append(("Second_local_pre", [round(x,4) for x in SecondAdj_local]))
            #セカンド補正再開
            
            for i in range(6):
                bonus = 0.0
            
                if i in attackers:
                    if AttackSuccess == 1:
                        bonus += 0.08
                    elif DAS > 0.10:
                        bonus += 0.04
            
                if i >= 4:
                    bonus -= 0.10
            
                if StartCollapse == 1 and i >= 3:
                    bonus += 0.03
            
                SecondAdj_local[i] *= (1 + bonus)
            
            # ===============================
            # ★ ① 攻め結果補正（←先に入れる）
            # ===============================
            if len(attackers) > 0:
            
                atk = attackers[0]
            
                if atk > 0:
            
                    if AttackSuccess == 1:
                        SecondAdj_local[atk-1] *= 0.90
                        SecondAdj_local[atk]   *= 1.10
            
                    elif AttackWeak == 1:
                        SecondAdj_local[atk]   *= 1.15
                        SecondAdj_local[atk-1] *= 0.95
            
                    elif AttackFail == 1:
                        SecondAdj_local[atk]   *= 0.85
                        SecondAdj_local[atk-1] *= 1.05
            
            
            # ===============================
            # ★ ② 既存SecondCore（後に回す）
            # ===============================
            if SecondCore is not None and NoAttackFlag == 0:
            
                SecondAdj_local[0] *= 0.88
                ThirdAdj_local[0]  *= 0.90
            
                SecondAdj_local[SecondCore] *= 1.10
                ThirdAdj_local[SecondCore]  *= 1.08
        
            # ===============================
            # ★ 攻め成立判定
            # ===============================
            attack_success = False
        
            for atk in attackers:
        
                if atk == 0:
                    continue
        
                if atk == a:
        
                    st_ok = Start[atk] >= Start[atk-1] - 0.02
                    turn_ok = Turn[atk] >= Turn[atk-1]
                    power_ok = CPI[atk] >= CPI[atk-1] - 0.03
        
                    if st_ok and (turn_ok or power_ok):
                        attack_success = True
        
        
            # ===============================
            # ★ 1着確率
            # ===============================
            P_first = P1[a]
            
            if SecondCore is not None and a == 0 and NoAttackFlag == 0:

                if P1[SecondCore] > 0.25:
                    P_first *= 0.90            
        
            # ===============================
            # ★ 弱頭でも残り計算させる
            # ===============================
            if (
                P1[a] < 0.12
                and DAS > STRONG
                and attack_success
            ):
                P_first *= 1.06
        
        
            # ===============================
            # ★ 展開拾い強化（最終版）
            # ===============================
            if attack_success and NoAttackFlag == 0:
        
                for i in range(a+1,6):
        
                    dist = i - a
        
                    # ■ 外は条件付き
                    if i >= 4:
                        can_pass = (
                            Start[i] >= Start[i-1] - 0.01
                            and Turn[i] >= Turn[i-1] - 0.02
                            and CPI[i] >= CPI[i-1] - 0.03
                        )
                        if not can_pass:
                            continue
        
                    # ■ 距離別補正
                    if dist == 1:
                        SecondAdj_local[i] *= 1.12
                        ThirdAdj_local[i]  *= 1.08
        
                    elif dist == 2:
                        SecondAdj_local[i] *= 1.08
                        ThirdAdj_local[i]  *= 1.05
        
                    else:
                        SecondAdj_local[i] *= 1.03
                        
            # ===============================
            # ★ 攻め連動（最終版）
            # ===============================
            if attack_success and NoAttackFlag == 0:
            
                # ===============================
                # ■ 内は潰れる（軽めに修正）
                # ===============================
                for i in range(a):
            
                    if i == 0 and (
                        0.06 < DAS < 0.16
                        and InsideSurvival[0] >= 0.45
                    ):
                        continue
            
                    SecondAdj_local[i] *= 0.88
                    ThirdAdj_local[i]  *= 0.92
            
                # ===============================
                # ■ 攻め艇はしっかり残す
                # ===============================
                
                SecondAdj_local[a] *= 1.08
            
                # ===============================
                # ■ 外は“軽く”だけ浮上（被り防止）
                # ===============================
                for i in range(a+1, 6):
                
                    if i >= 4:
                
                        if not outer_ok[i]:
                            continue
                
                        SecondAdj_local[i] *= 1.05
                        ThirdAdj_local[i]  *= 1.03
                   
                    
            # ===============================
            # ★ 3着バランス補正（最終微調整）
            # ===============================
            for i in range(6):
            
                # ===============================
                # ■ センター優遇（軽め）
                # ===============================
                if i == 2:   # 3号艇
                    ThirdAdj[i] *= 1.05
            
                elif i == 3: # 4号艇
                    ThirdAdj[i] *= 1.04
            
            
                # ===============================
                # ■ 5コース（条件型）
                # ===============================
                elif i == 4:
            
                    if DAS > WEAK and NoAttackFlag == 0:
                        ThirdAdj[i] *= 1.03
                    else:
                        ThirdAdj[i] *= 0.98
            
            
                # ===============================
                # ■ 6コース（整理版）
                # ===============================
                elif i == 5:
            
                    alive = (
                        DAS > MID
                        and Start[i] >= Start[3] - 0.02
                        and Foot[i] >= 0.50
                    )
            
                    if alive:
                        ThirdAdj[i] *= 1.05
                    else:
                        ThirdAdj[i] *= 0.88
            
            
                # ===============================
                # ■ 弱すぎる艇カット
                # ===============================
                if Skill[i] < 0.30:
                    ThirdAdj[i] *= 0.90
                    
            # ===============================
            # ★ 共倒れ時の着順補正
            # ===============================
            if (
                NoAttackFlag == 0
                and DAS > MID
                and Turn[2] > 0.55
                and Turn[3] > 0.55
                and abs(Turn[2] - Turn[3]) < 0.04
            ):
            
                SecondAdj_local[2] *= 0.90
                SecondAdj_local[3] *= 0.90
            
                ThirdAdj_local[2] *= 0.90
                ThirdAdj_local[3] *= 0.90
            
                SecondAdj_local[5] *= 1.02
                ThirdAdj_local[5]  *= 1.05
            
                SecondAdj_local[0] *= 1.05
                ThirdAdj_local[0] *= 1.05
                        
            # ===============================
            # ★ 展開3着強化（修正版）
            # ===============================
            if attack_success and DAS > WEAK and NoAttackFlag == 0:
            
                for i in range(6):
            
                    if i == a:
                        continue
            
                    dist = abs(i - a)
            
                    # 近い艇だけ対象（重要）
                    if dist > 2:
                        continue
            
                    if i >= 4:
                        ThirdAdj_local[i] *= 1.06
            # ===============================
            # ★ 攻め弱い時の残り補正
            # ===============================
            
            if AttackWeak == 1 and AttackSuccess == 0:
            
                for i in attackers:
            
                    if i == 2:
            
                        SecondAdj_local[i] *= 1.10
            
                        ThirdAdj_local[i]  *= 1.15
            
                    elif i == 3:
            
                        SecondAdj_local[i] *= 1.07
            
                        ThirdAdj_local[i]  *= 1.10
            
                    else:
            
                        SecondAdj_local[i] *= 1.03
            
                        ThirdAdj_local[i]  *= 1.05
                        
            # ===============================
            # ★ 内の3着残り（内全体）
            # ===============================
            for i in range(3):  # 1〜3コース
            
                if InsideSurvival[i] > 0.55:
                    ThirdAdj[i] *= 1.05
            
            
            # ===============================
            # ★ インの粘り（1専用）
            # ===============================
            if InsideSurvival[0] > 0.55:
                ThirdAdj[0] *= 1.03
                        

                    
            # ===============================
            # ★ 1だけ飛ぶパターン（修正版）
            # ===============================
            if attack_success and NoAttackFlag == 0:
            
                if (
                    Start[0] < Start[a] - 0.02   # ←逆にする（重要）
                    and Turn[0] < Turn[a]
                ):
                    SecondAdj_local[0] *= 0.70
                    ThirdAdj_local[0]  *= 0.65
            
                    SecondAdj_local[1] *= 1.12
                    ThirdAdj_local[1]  *= 1.06
                    
            # ===============================
            # ★ 攻め共倒れ検知（最終版）
            # ===============================
            if len(attackers) >= 2:
            
                main = attackers[0]
                sub  = attackers[1]
            
                if (
                    DAS > MID
                    and AttackIndex[main] > 0.45
                    and AttackIndex[sub] > 0.45
                ):
            
                    # ===============================
                    # ■ 攻め役はしっかり削る
                    # ===============================
                    SecondAdj_local[main] *= 0.88
                    SecondAdj_local[sub]  *= 0.88
            
                    ThirdAdj_local[main] *= 0.92
                    ThirdAdj_local[sub]  *= 0.92
            
                    # ===============================
                    # ■ 近い艇だけ恩恵（重要）
                    # ===============================
                    for i in range(6):
            
                        if i in [main, sub]:
                            continue
            
                        # 攻めの近くのみ対象
                        if min(abs(i-main), abs(i-sub)) <= 2:
                            ThirdAdj_local[i] *= 1.08
            
                    # ===============================
                    # ■ さらに近い場合だけ追加
                    # ===============================
                    if abs(main - sub) <= 2:
            
                        for i in range(6):
            
                            if i in [main, sub]:
                                continue
            
                            if min(abs(i-main), abs(i-sub)) == 1:
                                ThirdAdj_local[i] *= 1.04
            
            # ===============================
            # ★ 外の詰まり・抜け判定（3着用）
            # ===============================
            for i in range(3,6):

                if Start[i] > Start[i-1] + 0.02:
                    ThirdAdj_local[i] *= 1.10
            
                elif Start[i] < Start[i-1] - 0.02:
                    ThirdAdj_local[i] *= 0.80
            
                else:
                    ThirdAdj_local[i] *= 0.95
                    
                if outer_ok[i]:
                    ThirdAdj_local[i] *= 1.08
                else:
                    ThirdAdj_local[i] *= 0.85
            
            # ===============================
            # ★ 3着：位置ボーナス
            # ===============================
            for i in range(6):

                dist = real_lane[i] - real_lane[a]
            
                if dist == -1:
                    ThirdAdj_local[i] *= 1.08
                elif dist == -2:
                    ThirdAdj_local[i] *= 1.04
        
            # ===== 6の2着残り強化 =====

            SixSecondFlag = 0
            
            if (
                CPI[5] >= 0.55
                and Foot[5] >= 0.55
                and DAS > 0.15
                and NoAttackFlag == 0
                and (
                    DAS > WEAK
                    or OuterClusterFlag == 1
                )
            ):
            
                SixSecondFlag = 1
            
                # 前削り
                SecondAdj_local[0] *= 0.92
                SecondAdj_local[1] *= 0.95
                SecondAdj_local[2] *= 0.97
            
                # 6強化（修正）
                SecondAdj_local[5] *= 1.08
            
            else:
                if Foot[5] < 0.45:
                    SecondAdj_local[5] *= 0.90
            
            # ===============================
            # ★ 3着強化（修正版）
            # ===============================
            
            if (
                FiveFlowFlag
                and DAS > WEAK
                and AttackSuccess == 1
            ):
                ThirdAdj_local[4] *= 1.10
            
            if (
                SixFlowFlag
                and DAS > WEAK
                and AttackSuccess == 1
                and NoAttackFlag == 0
            ):
                ThirdAdj_local[5] *= 1.12
                
                
                
            # ===============================
            # ★ 6の特例（強展開のみ）
            # ===============================
            if (
                DAS > STRONG
                and Start[5] >= max(Start) - 0.005
                and CPI[5] > 0.45
                and Foot[5] > 0.48
            ):
                SecondAdj_local[5] *= 1.10
                
            # ===============================
            # ★ 展開6（性能じゃない6）
            # ===============================
            if (
                NoAttackFlag == 0
                and DAS > MID
                and AttackSuccess == 1
                and Start[5] >= Start[3] - 0.02
                and CLS[5] in ["A1","A2"]
            ):
                ThirdAdj_local[5] *= 1.12
                
            # ===============================
            # ★ 5・6の壁（条件分岐版）
            # ===============================
            for i in range(4,6):
            
                if i == a:
                    continue
            
                # ■ 5コース
                if i == 4:
            
                    if (
                        max(CPI[2:4]) > CPI[4] - 0.02
                        and max(Turn[2:4]) >= Turn[4] - 0.02
                    ):
                        SecondAdj_local[4] *= 0.80
                        ThirdAdj_local[4]  *= 0.85
            
        
            # ===============================
            # ★ 頭別ロジック
            # ===============================
        
            if a == 0:
                SecondAdj_local[1] *= 1.10
                SecondAdj_local[2] *= 1.05
                for i in range(3,6):
                    SecondAdj_local[i] *= 0.88
                    ThirdAdj_local[i]  *= 0.92
        
            elif a == 1:
                SecondAdj_local[0] *= 1.10
                ThirdAdj_local[0]  *= 1.15
                SecondAdj_local[2] *= 1.05
        
            elif a == 2:
                SecondAdj_local[0] *= 0.85
                SecondAdj_local[1] *= 0.90
                for i in range(3,6):
                    SecondAdj_local[i] *= 1.03
                    ThirdAdj_local[i]  *= 1.05
        
            elif a == 3:
                for i in range(0,2):
                    SecondAdj_local[i] *= 0.80
                for i in range(4,6):
                    SecondAdj_local[i] *= 1.06
                    ThirdAdj_local[i]  *= 1.08
        
            elif a == 4:  # 5頭

                for i in range(0,3):
                    SecondAdj_local[i] *= 0.78
            
                ThirdAdj_local[4] *= 1.08
            
            
            elif a == 5:  # 6頭
            
                for i in range(0,3):
                    SecondAdj_local[i] *= 0.70
            
                ThirdAdj_local[5] *= 1.10
                
            # ===============================
            # ★ 3頭時の2過剰抑制
            # ===============================
            if a == 2:  # 3号艇が1着
                if Turn[2] > Turn[1] and NoAttackFlag == 0:
                    SecondAdj_local[1] *= 0.92
            
            
            # 残り艇
            remain1 = [i for i in range(6) if i != a and Active[i] == 1]
            
            for i in range(6):
                if i == a:
                    continue
            
                # ★ 2号艇の遅れ残り（最小補正）
                if (
                    i == 1
                    and Start[1] <= min(Start) + 0.002
                    and CPI[1] >= 0.42
                    and NoAttackFlag == 0
                ):
                    ThirdAdj_local[1] *= 1.08
            
                dist = i - a
            
                if dist < 0:
                    SecondAdj_local[i] *= (1 - 0.04 * DAS)
                    ThirdAdj_local[i]  *= (1 - 0.06 * DAS)
            
                elif dist == 1:
                    SecondAdj_local[i] *= 1.12
                    ThirdAdj_local[i]  *= 1.08
            
                elif dist >= 2:
                    if NoAttackFlag == 0:
            
                        if i >= 4 and not outer_ok[i]:
                            continue
            
                        SecondAdj_local[i] *= 1.03
                        ThirdAdj_local[i]  *= 1.00
     
                            
            # ===============================
            # ★ 外の進路制限（修正版）
            # ===============================
            for i in range(4,6):
            
                if i == a:
                    continue
            
                blockers = 0
            
                for j in range(i):
            
                    if j == a:
                        continue
            
                    if (
                        CPI[j] >= CPI[i] - 0.03
                        and Turn[j] >= Turn[i] - 0.02
                    ):
                        blockers += 1
            
                if blockers >= 2:
                    SecondAdj_local[i] *= 0.80
                    
            # ===============================
            # ★ 4頭時の6流入（修正版）
            # ===============================
            if a == 3 and Strong6:
            
                # 2着寄りに流入
                SecondAdj_local[5] *= 1.12
            
                # 3着も少し拾う
                ThirdAdj_local[5] *= 1.08
                
            # ===============================
            # ★ 2着の構造（軽量版）
            # ===============================
            if DAS < 0.15:
            
                for i in range(6):
            
                    if i == a:
                        continue
            
                    dist = abs(i - a)
            
                    # ===============================
                    # ■ 隣（最重要）
                    # ===============================
                    if dist == 1:
                        SecondAdj_local[i] *= 1.15
            
                    # ===============================
                    # ■ 内（軽め）
                    # ===============================
                    elif i < a:
                        SecondAdj_local[i] *= 1.05
            
                    # ===============================
                    # ■ 外（削りすぎない）
                    # ===============================
                    elif i > a:
                        SecondAdj_local[i] *= 0.85
                    
               
            
            # ===============================
            # ★ 距離で最終決定（整理版）
            # ===============================
            for i in range(6):
            
                if i == a:
                    continue
            
                # ★ 実際の並びで距離判定（重要）
                dist = abs(real_lane[i] - real_lane[a])
            
                # ===============================
                # ■ 直後（最重要）
                # ===============================
                if dist == 1:
                    if i >= 4:
                        SecondAdj_local[i] *= 1.12
                # ===============================
                # ■ 1艇挟み
                # ===============================
                elif dist == 2:
                    SecondAdj_local[i] *= 1.04
            
                # ===============================
                # ■ 遠い（軽く不利）
                # ===============================
                elif dist >= 3:
                    SecondAdj_local[i] *= 0.80
                    
            # ===============================
            # ★ 差し込み勝ち
            # ===============================
            for i in range(1,4):

                st_gap = Start[i] - Start[i-1]
            
                if attack_success and NoAttackFlag == 0:
                
                    attacker = i
                
                    candidates = []
                
                    for j in range(attacker):
                
                        if (
                            Start[j] >= Start[attacker] - 0.02
                            and Turn[j] >= 0.50
                        ):
                            candidates.append(j)
                
                    if len(candidates) > 0:
                
                        best = max(
                            candidates,
                            key=lambda x: (
                                0.40 * Turn[x]
                                + 0.30 * Start[x]
                                + 0.20 * max(0, Start[x] - Start[attacker])
                                + 0.10 * Foot[x]
                            )
                        )
                
                        SecondAdj_local[best] *= 1.15
                        ThirdAdj_local[best]  *= 1.10
                        
            # ===============================
            # ★ 壁崩壊（調整版）
            # ===============================
            for i in range(1,4):
            
                st_gap = Start[i] - Start[i-1]
            
                # ===============================
                # ■ 強崩壊
                # ===============================
                if (
                    abs(st_gap) >= 0.01
                    and st_gap < -0.04
                    and DAS > MID
                    and NoAttackFlag == 0
                ):
            
                    # 崩れた艇
                    SecondAdj_local[i] *= 0.60
                    ThirdAdj_local[i]  *= 0.65
            
                    # 外に流す（段階）
                    for j in range(i+1,6):
            
                        if j == i+1:
                            SecondAdj_local[j] *= 1.15
                            ThirdAdj_local[j]  *= 1.10
                        else:
                            SecondAdj_local[j] *= 1.10
                            ThirdAdj_local[j]  *= 1.05
            
                    # 内は軽く崩す
                    for j in range(0,i):
                        SecondAdj_local[j] *= 0.97
                        ThirdAdj_local[j]  *= 0.98
                # ===============================
                # ■ 弱崩壊
                # ===============================
                elif st_gap < -0.02:
                
                    # 崩れた艇（軽め）
                    SecondAdj_local[i] *= 0.85
                    ThirdAdj_local[i]  *= 0.90
                
                    # 外に流れる
                    for j in range(i+1,6):
                        SecondAdj_local[j] *= 1.08
                        ThirdAdj_local[j]  *= 1.05
                
                    # 内も少し影響
                    for j in range(0,i):
                        SecondAdj_local[j] *= 0.98
                        ThirdAdj_local[j]  *= 0.99
                        
            # ===============================
            # ★ 外（5・6）最終制御（整理版）
            # ===============================
            for i in range(4,6):
            
                # ===============================
                # ■ 生存条件（先に判定）
                # ===============================
                alive = False
            
                # 展開で生きる
                if (
                    DAS > MID
                    and Start[i] >= Start[i-1] - 0.02
                ):
                    alive = True
            
                # 性能で生きる
                if (
                    Foot[i] >= 0.50
                    and CPI[i] >= 0.48
                ):
                    alive = True
            
            
                # ===============================
                # ■ 5コース
                # ===============================
                if i == 4:
            
                    if alive:
                        SecondAdj_local[i] *= 1.08
                        ThirdAdj_local[i]  *= 1.04
                    else:
                        SecondAdj_local[i] *= 0.90
            
            
                # ===============================
                # ■ 6コース
                # ===============================
                if i == 5:
            
                    if alive:
                        SecondAdj_local[i] *= 1.05
                        ThirdAdj_local[i]  *= 1.08
                    else:
                        SecondAdj_local[i] *= 0.85
                        ThirdAdj_local[i]  *= 0.85
                        
            # ===============================
            # ★ 6の最終制御（整理版）
            # ===============================
            # 無風は無条件で殺す
            if NoAttackFlag == 1:
            
                SecondAdj_local[5] *= 0.70
                ThirdAdj_local[5]  *= 0.75
            
            else:
            
                # ===============================
                # ■ 生存条件
                # ===============================
                alive = False
            
                if SixFlowFlag:
                    alive = True
            
                if (
                    DAS > MID
                    and Start[5] >= Start[3] - 0.02
                    and Foot[5] >= 0.50
                ):
                    alive = True
            
            
                # ===============================
                # ■ 分岐
                # ===============================
                if alive:
            
                    SecondAdj_local[5] *= 1.08
                    ThirdAdj_local[5]  *= 1.10
            
                else:
            
                    # 性能不足なら強く削る
                    if CPI[5] < 0.50:
                        SecondAdj_local[5] *= 0.60
                        ThirdAdj_local[5]  *= 0.65
                    else:
                        SecondAdj_local[5] *= 0.80
                        ThirdAdj_local[5]  *= 0.85
                        
            # ===============================
            # ★ 1の残り補正（頭負け時のみ）
            # ===============================
            if a != 0:
            
                weak_head = FirstScore[0] < max(FirstScore) * 0.92
                has_resist = InsideSurvival[0] >= 0.48
            
                weak_sashi = (
                    Start[1] < Start[0] - 0.02
                    or Turn[1] < Turn[2]
                )
            
                if weak_head and has_resist:
            
                    if weak_sashi:
                        SecondAdj_local[0] *= 1.12
                        ThirdAdj_local[0] *= 1.08
            
                    else:
                        SecondAdj_local[0] *= 1.06
                        ThirdAdj_local[0] *= 1.04
            
                # 軽い保険（弱める）
                ratio = FirstScore[0] / max(FirstScore)
            
                if (
                    0.88 <= ratio <= 0.96
                    and InsideSurvival[0] >= 0.45
                ):
                    SecondAdj_local[0] *= 1.05
                    ThirdAdj_local[0] *= 1.03
                    
                    
            remain1 = [i for i in range(6) if i != a and Active[i]==1]
                 
            # ★ 最後に1回だけ入れる（ここ超重要）
            avg = sum(SecondAdj_local) / 6
            
            SecondAdj_local = [
                0.7 * x + 0.3 * avg
                for x in SecondAdj_local
            ]

            second_scores = [SecondAdj_local[i] for i in remain1]
            
            # ===== 内繰り上がり補正（SECOND）=====
            if inner_mode:
                for idx, i in enumerate(remain1):
                    if i == 1:   # 2号艇
                        second_scores[idx] *= 1.2
                    elif i == 2: # 3号艇
                        second_scores[idx] *= 1.15
                    elif i == 5: # 6号艇
                        second_scores[idx] *= 0.7
            
            total2 = sum(second_scores)
            if total2 <= 0:
                total2 = 1e-6
            
            second_probs = [s/total2 for s in second_scores]
            
            for b, P_second in zip(remain1, second_probs):
            
                remain2 = [i for i in remain1 if i != b]
            
                third_scores = [ThirdAdj_local[i] for i in remain2]
                total3 = sum(third_scores)
                if total3 <= 0:
                    total3 = 1e-6
            
                third_probs = [s/total3 for s in third_scores]
            
                for c, P_third in zip(remain2, third_probs):
            
                    p = P_first * P_second * P_third
            
                    results.append((boats[a], boats[b], boats[c], p))
                    
            # ===============================
            # ★ 最終return（絶対必要）
            # ===============================
            
            if len(results) == 0:
                return [], 0, [1/6]*6, 0, [0.5]*6, debug_log, [0]*6
                
            DoubleAttackScore = DAS
            
        return results, ChaosScore, P1, DAS, InsideSurvival, debug_log, Start
                
    def run_zure_ai(order, NoAttackProb):

        results, ChaosScore, P1, DAS, IS, debug, Start = run_attack(order)
    
        if NoAttackProb > 0.95 and IS[0] > 0.60:
            return []
    
        AttackWeak, AttackSuccess, NoAttackProb_new = detect_state(debug, DAS)
    
        zure_results = []
    
        for r in results:

            a = r[0]
            b = r[1]
            c = r[2]
            p = r[3]
    
            head = a - 1
    
            if head >= 0:
    
                if (
                    AttackSuccess == 0
                    and NoAttackProb_new > 0.75
    
                    and 0.30 < P1[0] < 0.48
                    and 0.45 < IS[0] < 0.65
    
                    and abs(P1[1] - P1[0]) < 0.15
    
                    and P1[head] > 0.15
                ):
                    boost = 1.6
    
                    zure_results.append((a,b,c,p * boost))
    
        return zure_results
            
    # =====================================
    # 進入パターン
    # =====================================
    
    order_waku = [0,1,2,3,4,5]
    
    order_ex = [x-1 for x in ExEntry]
    
    if len(order_ex) != 6 or any(x < 0 or x > 5 for x in order_ex):
        order_ex = [0,1,2,3,4,5]
    
    try:
        res_base, chaos1, P1_base, DAS_base, IS_base, debug_log_base, Start_base = run_no_attack(order_waku)
        
        res_no, chaos_no, P1_no, DAS_no, IS_no, debug_no, _ = run_no_attack(order_ex)
    
        res_weak, chaos_w, P1_w, DAS_w, IS_w, debug_w, _ = run_weak(order_ex)
    
        res_attack, chaos_a, P1_a, DAS_a, IS_a, debug_a, Start_a = run_attack(order_ex)
    
    except Exception as e:
        import traceback
        st.write("ERROR:", e)
        st.code(traceback.format_exc())
        st.stop()

    

    # ベースは attack を採用（←一番安定）
    ChaosScore = chaos_a
    P1 = P1_a
    DoubleAttackScore = DAS_a
    InsideSurvival = IS_a
    debug_log_ex = debug_a
    Start = Start_a
    
    
    def detect_state(debug_log, DAS):
    
        MID = 0.09 
    
        AttackWeak = 0
        AttackSuccess = 0
    
        for item in debug_log:
    
            # ★ これ追加
            if not isinstance(item, tuple) or len(item) != 2:
                continue
    
            name, val = item
    
            if name == "AttackWeak":
                AttackWeak = val
            if name == "AttackSuccess":
                AttackSuccess = val
    
        NoAttackProb = max(0, min(1, 1 - (DAS / MID)))
    
        return AttackWeak, AttackSuccess, NoAttackProb
    
    
    AttackWeak, AttackSuccess, NoAttackProb = detect_state(debug_log_ex, DoubleAttackScore)
    # =====================================
    # 合成
    # =====================================
    final = {}
    
    # 重み
    if NoAttackProb > 0.75:
        w_no = 0.70
        w_weak = 0.20
        w_at = 0.10
    
    elif DoubleAttackScore < MID:
        w_no = 0.30
        w_weak = 0.30
        w_at = 0.40
    
    else:
        w_no = 0.25
        w_weak = 0.30
        w_at = 0.45
    
    results = []

    # 各世界からそのまま入れる（重みだけかける）
    for a,b,c,p in res_no:
        results.append((a,b,c,p * w_no))
    
    for a,b,c,p in res_weak:
        results.append((a,b,c,p * w_weak))
    
    for a,b,c,p in res_attack:
        results.append((a,b,c,p * w_at))

    results = sorted(results, key=lambda x: x[3], reverse=True)

    # ===============================
    # ★ セカンド軸生成（最終版）
    # ===============================
    
    SecondHead = None
    
    candidates = sorted(
        range(6),
        key=lambda i: P1[i],
        reverse=True
    )
    
    for i in candidates:
        if i != 0:
            SecondHead = i
            break
    
    # ===============================
    # ★ 判定ロジック
    # ===============================
    top = sorted(P1, reverse=True)
    
    is_close = (top[0] - top[1] < 0.05)
    
    can_break = (
        AttackSuccess == 1
        or DoubleAttackScore > 0.13
    )
    
    allow_outer = (
        SecondHead < 4
        or can_break
    )
    
    SecondAxisResults = []
    
    if (
        SecondHead is not None
        and P1[SecondHead] >= P1[0] * 0.75
        and (AttackWeak == 1 or is_close)
        and allow_outer
    ):
    
        for (a,b,c,p) in results:
    
            # 1頭を崩す
            if a == 1:
                new_head = SecondHead + 1
    
                new = (new_head, b, c, p * 0.95,)
                SecondAxisResults.append(new)
    
            # セカンド頭強化
            elif a == SecondHead + 1:
                SecondAxisResults.append((a,b,c,p * 1.10,))
    
    # 合成
    results += SecondAxisResults
    # ===============================
    # ★ シャープ化 & 正規化 & カット（完成版）
    # ===============================
    
    # ① シャープ化
    power = 1.05 + 0.15 * ChaosScore
    
    new_results = []
    
    for r in results:
    
        if len(r) == 5:
            a,b,c,p,_ = r
            new_results.append((a,b,c,p,))
    
        else:
            a,b,c,p = r
            new_results.append((a,b,c,p**power))
    
    results = new_results
    
    
    # ② 正規化（secも維持）
    total = sum(r[3] for r in results)
    
    clean_results = []

    for r in results:
        if isinstance(r, (list, tuple)) and len(r) >= 4:
            a, b, c, p = r[:4]
            clean_results.append((a,b,c,p))
    
    results = clean_results
    
    if not results:
        st.write("結果なし")
        st.stop()
        
    
    
    
    # ④ ソート
    # ←ここに追加
    fixed = []

    for r in results:
    
        try:
    
            a, b, c, p = r[:4]
    
            fixed.append((int(a), int(b), int(c), float(p)))
    
        except:
    
            continue
            
    if not results:
        st.write("results空")
        st.stop()
    
    results = fixed
    
    # ←そのまま既存
    results.sort(key=lambda x: x[3], reverse=True)
    # ===============================
    # ★ 外頭制限（先にやる）
    # ===============================
    tmp = []
    
    for r in results:

        a = r[0]
        b = r[1]
        c = r[2]
        p = r[3]
    
        if a >= 4 and DoubleAttackScore < MID:
            p *= 0.5
    
        tmp.append((a,b,c,p))
    
    results = tmp
    
    # ===============================
    # ★ 再正規化（超重要）
    # ===============================
    total = sum(p for _,_,_,p in results)
    
    if total > 0:
        results = [(a,b,c,p/total) for a,b,c,p in results]
    
    # ===============================
    # ★ 無風：外頭禁止
    # ===============================
    tmp = []
    
    for r in results:

        a = r[0]
        b = r[1]
        c = r[2]
        p = r[3]
    
        if NoAttackProb > 0.90 and a >= 4:
            continue
    
        tmp.append((a,b,c,p))
    
    results = tmp
    
    # ===============================
    # ★ 同一展開カット
    # ===============================
    seen = set()
    tmp = []
    
    for r in results:

        a = r[0]
        b = r[1]
        c = r[2]
        p = r[3]
    
        key = (a,b,c)
    
        if key in seen:
            continue
    
        seen.add(key)
        tmp.append((a,b,c,p))
    
    results = tmp
    
    # ===============================
    # ★ ソート（先にやる）
    # ===============================
    # ←ここに追加
    fixed = []

    for r in results:
        try:
            a, b, c, p = r[:4]
            fixed.append((int(a), int(b), int(c), float(p)))
        except:
            continue
    
    results = fixed
    
    if not results:
        st.write("results空")
        st.stop()
    # ←そのまま既存
    results.sort(key=lambda x: x[3], reverse=True)
    
    # ===============================
    # ★ 上位指標（←ここ追加）
    # ===============================
    Top1 = results[0][3] if len(results) > 0 else 0
    Top3 = sum(r[3] for r in results[:3])
    Top5 = sum(r[3] for r in results[:5])
    
    # ===============================
    # ★ 購入ランク分類（修正版）
    # ===============================
    BuyRank = "strong"
    
    # 見送り
    if (
        AttackSuccess == 0
        and NoAttackProb > 0.75
        and results[0][0] >= 4
    ):
        BuyRank = "skip"
    
    # 弱
    elif (
        NoAttackProb > 0.90
        and Top1 < 0.28
    ):
        BuyRank = "weak"
    
    elif Top1 < 0.22 and Top3 < 0.55:
        BuyRank = "weak"
    
    # ===============================
    # ★ レースタイプ判定（そのままでOK）
    # ===============================
    if Top1 >= 0.30 and Top3 >= 0.60:
        OddsType = "堅い"
    
    elif ChaosScore > 0.55:
        OddsType = "荒れ（強）"
    
    elif Top1 >= 0.22:
        OddsType = "中穴"
    
    elif P1[0] >= 0.30:
        OddsType = "ヒモ荒れ"
    
    else:
        OddsType = "万舟"
    
    # ===============================
    # ★ 点数制御（順番修正だけ）
    # ===============================
    max_bets = 0
    
    if BuyRank == "skip":
        max_bets = 0
    
    else:
    
        if Top3 > 0.55:
            max_bets = 3
    
        elif Top5 > 0.65:
            max_bets = 5
    
        elif Top5 > 0.55:
            max_bets = 7
    
        elif Top1 < 0.20:
            max_bets = 10
    
        else:
            max_bets = 8
    
        # Chaos連動
        max_bets = int(max_bets * (0.8 + 0.8 * ChaosScore))
    
        # 最低保証
        max_bets = max(5, max_bets)
    
    # ===============================
    # ★ weakだけ軽く制御（最小）
    # ===============================
    if BuyRank == "weak":
        max_bets = min(max_bets, 6)
    
    # ===============================
    # ★ 最後にカット（ここに移動）
    # ===============================
    results = results[:max_bets]

    # ===============================
    # ★ 最後の最後にカット（確定版）
    # ===============================
    cut = 0.002
    
    filtered = []
    
    for r in results:
    
        if len(r) < 4:
            continue
    
        a = r[0]
        b = r[1]
        c = r[2]
        p = r[3]
    
        if p >= cut:
            filtered.append((a,b,c,p))
    
    # ★ filteredが空でも絶対エラーにしない
    if len(filtered) > 0:
        results = filtered
        

    # =====================================
    # OUTPUT
    # =====================================

    Coverage = 0
    Final = []
    
    target = 0.80 + 0.10 * ChaosScore
    
    for r in results:
    
        Coverage += r[3]
        Final.append(r)
    
        # 点数制限
        if len(Final) >= max_bets:
            break
    
        # ★ カバレッジ条件
        if Coverage >= target:
            break

    unique = {}

    for a,b,c,p in Final:
        key = (a,b,c)
        unique[key] = unique.get(key, 0) + p   # ←これに変更
    
    Final = [(k[0],k[1],k[2],v) for k,v in unique.items()]
    
    Final.sort(key=lambda x: x[3], reverse=True)
                    
    # ===============================
    # ★ マーク付け（修正版）
    # ===============================
    
    if len(Final) > 0:
        top_p = Final[0][3]
    else:
        top_p = 0
    
    marked = []
    
    for i, (a,b,c,p) in enumerate(Final):
    
        head = a - 1
    
        if i == 0:
            mark = "◎"
    
        elif p >= top_p * 0.75:
            mark = "○"
    
        elif (
            head >= 2
            and (AttackWeak == 1 or DoubleAttackScore > 0.05)
        ):
            mark = "▲"
    
        elif p >= 0.05:
            mark = "△"
    
        else:
            mark = ""
    
        marked.append((mark,a,b,c,p))
        
    # ===============================
    # ★ 買い方分類（これに変更）
    # ===============================

    main = []
    sub = []
    hole = []
    insurance = []
    
    for (mark,a,b,c,p) in marked:
    
        # ===============================
        # ★ 保険（ここだけにする）
        # ===============================
        head = a - 1
        
        if (
            head == 0
            and mark in ["▲","△"]
            and 0.25 < P1[0] < 0.38
            and InsideSurvival[0] > 0.52
            and Start[0] >= max(Start[1:3]) - 0.02
            and p < top_p * 0.50
        ):
            insurance.append((a,b,c))
            continue
    
        # ===============================
        # 通常分類
        # ===============================
        if mark == "◎":
            main.append((a,b,c))
    
        elif mark == "○":
            sub.append((a,b,c))
    
        elif mark in ["▲","△"]:
            hole.append((a,b,c))
    
    insurance = insurance[:2]
    
    # ===============================
    # ★ 出目＋デバッグ（完全コピペ）
    # ===============================
    
    # ===============================
    # ★ 入力データまとめ（追加）
    # ===============================
    
    input_text = []
    input_text.append("===== INPUT =====")
    
    input_text.append(f"WinRate={WinRate}")
    input_text.append(f"PlaceRate={PlaceRate}")
    input_text.append(f"AvgST={AvgST}")
    input_text.append(f"Motor2={Motor2}")
    input_text.append(f"Boat2={Boat2}")
    
    input_text.append(f"ExTime={ExTime}")
    input_text.append(f"ExST={ExST}")
    
    input_text.append(f"TurnTime={TurnTime}")
    input_text.append(f"LapTime={LapTime}")
    input_text.append(f"StraightTime={StraightTime}")
    
    input_text.append(f"Class={Class}")
    input_text.append(f"Fcount={Fcount}")
    input_text.append(f"ExEntry={ExEntry}")
    
    input_text_output = "\n".join(input_text)
        

        
    # デバッグテキスト
    debug_text = []
    
    debug_text.append("===== DEBUG =====")
    
    # ===============================
    # 状態（最重要）
    # ===============================
    debug_log_ex.append(("RaceState", ""))

    debug_log_ex.append(("NoAttackProb", round(NoAttackProb,4)))
    debug_log_ex.append(("DAS", round(DoubleAttackScore,4)))
    debug_log_ex.append(("ChaosScore", round(ChaosScore,4)))
    # ===============================
    # 重み（今回の核心）
    # ===============================
    debug_log_ex.append(("Weights", ""))
    debug_log_ex.append(("w_no", round(w_no,3)))
    debug_log_ex.append(("w_weak", round(w_weak,3)))
    debug_log_ex.append(("w_at", round(w_at,3)))
    
    # ===============================
    # モード比較
    # ===============================
    debug_log_ex.append(("ModeScores", ""))
    debug_log_ex.append(("P1_no_top", round(max(P1_no),3)))
    debug_log_ex.append(("P1_weak_top", round(max(P1_w),3)))
    debug_log_ex.append(("P1_attack_top", round(max(P1_a),3)))
    
    # ===============================
    # 最終P1
    # ===============================
    debug_log_ex.append(("P1", ""))
    for i,p in enumerate(P1):
        debug_log_ex.append((f"{i+1}", round(p,4)))
    
    # ===============================
    # 内部ログ（必要最低限）
    # ===============================
    debug_log_ex.append(("CoreDebug", ""))
    
    for name, val in list(debug_log_ex):
        if name in [
            "AttackWeak",
            "AttackSuccess",
            "Start",
            "P1_pre",
            "SecondAdj_pre",
            "ThirdAdj_pre"
        ]:
            debug_log_ex.append((name, val))
        
    
    debug_output = "\n".join(
        f"{k}: {v}" for (k,v) in debug_log_ex
    )
            
    
    
        # 出目テキスト
    result_text = "\n".join([
        f"{a}-{b}-{c} ({round(p,4)}) {mark}" if mark != "" else f"{a}-{b}-{c} ({round(p,4)})"
        for (mark,a,b,c,p) in marked
    ])
    
    if BuyRank == "skip":
        st.markdown("## ⚠ 見送りレース")
        
    st.markdown("## 🧠 判定")

    if BuyRank == "skip":
        st.error(f"見送り｜{OddsType}")
    
    elif BuyRank == "weak":
        st.warning(f"購入（微妙）｜{OddsType}")
    
    else:
        st.success(f"購入（推奨）｜{OddsType}")
    
    st.write(f"推奨点数：{max_bets}点")
    
    st.markdown("### ◎ 本線")
    for a,b,c in main:
        st.write(f"{a}-{b}-{c}")
    
    st.markdown("### ○ 押さえ")
    for a,b,c in sub:
        st.write(f"{a}-{b}-{c}")
    
    st.markdown("### ▲ ヒモ荒れ")
    for a,b,c in hole:
        st.write(f"{a}-{b}-{c}")
    
    st.markdown("### 保険（イン）")
    for a,b,c in insurance:
        st.write(f"{a}-{b}-{c}")
        
    st.caption(f"NoAttackProb：{round(NoAttackProb,3)} / DAS：{round(DoubleAttackScore,3)}")
    
    
    st.markdown("## 🎯 買い目")
    

    for line in result_text.split("\n"):
        st.write(line)
        
    # ===============================
    # ★ 進入チェック（コピー専用）
    # ===============================
    real_lane_map = {i: order_ex.index(i) for i in order_ex}
    
    check_text = []
    check_text.append("===== CHECK =====")
    check_text.append(f"order: {order_ex}")
    check_text.append(f"real_lane: {real_lane_map}")
    
    check_output = "\n".join(check_text)
    
    # ===============================
    # ★ 最終出力（ここ重要）
    # ===============================
    full_output = (
        input_text_output
        + "\n\n"
        + result_text
        + "\n\n"
        + check_output
        + "\n\n"
        + debug_output
    )
    
    st.code(full_output, language="text")
    