import streamlit as st

WEAK = 0.06
MID = 0.09
STRONG = 0.13

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

    # ★ 同値処理（最重要）
    if mx - mn < 1e-6:
        return [0.5] * len(values)

    return [
        ((v - mn) / (mx - mn)) if v is not None else 0
        for v in values
    ]

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
        # SKILL
        # ===============================
        
        WinScore = normalize(WR)
        PlaceScore = normalize(PR)

        Skill = []

        for i in range(6):
        
            base = 0.7*WinScore[i] + 0.3*PlaceScore[i]
        
            # ★ 欠損だけ軽く落とす
            if WR[i] == 0 and PR[i] == 0:
                base *= 0.7
        
            Skill.append(base)
        
        
        # ===============================
        # ENGINE（修正版）
        # ===============================
        
        Engine = []
        
        Active_local = [Active[i] for i in order]
        
        for i in range(6):
        
            if Active_local[i] == 0:
                Engine.append(0)
                continue
        
            val = 0.6 * MotorScore[i] + 0.4 * Skill[i]
        
            # ★ モーター弱すぎは削る（重要）
            if MotorScore[i] < 0.35:
                val *= 0.85
        
            Engine.append(val)
           

        # ===============================
        # EXHIBIT
        # ===============================
        
        AvgEx = sum(ET)/6
        
        TimeScore = normalize([AvgEx-x for x in ET])
        ExSTScore = normalize([
            0.25 - x if x > 0 else 0.0
            for x in EST
        ])
        
        ExhibitRaw = [
            0.80*TimeScore[i] + 0.20*ExSTScore[i]
            for i in range(6)
        ]
        
        Exhibit = []
        
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
        
            Exhibit.append(ExhibitRaw[i]*factor)
    
        # ===============================
        # FOOT
        # ===============================

        AvgTurn=sum(TT)/6
        AvgLap=sum(LT)/6
        AvgStraight=sum(STT)/6

        TurnScore=normalize([AvgTurn-x for x in TT])
        LapScore=normalize([AvgLap-x for x in LT])
        StraightScore=normalize([AvgStraight-x for x in STT])

        RawFoot = [
            0.42*TurnScore[i]+
            0.28*LapScore[i]+
            0.25*StraightScore[i]+
            0.08*Exhibit[i]
            for i in range(6)
        ]

        Foot=RawFoot

        Active_local = [Active[i] for i in order]


        # ===============================
        # START（精度版）
        # ===============================
        
        adj_exst = []

        for i in range(6):
        
            x = EST[i]
        
            # ★ 展示Fはここで処理（最重要）
            if ExhibitionF[i] == 1:
                x = max(0.12, x + 0.06)
        
            adj_exst.append(convert_exst(x))
        
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
        
        
        # ===============================
        # ★ 壁崩れ検知
        # ===============================
        WallBreak = 0
        
        if (
            Start[1] > Start[0] + 0.03
            or Start[1] > Start[2] + 0.01
        ):
            WallBreak = 1
        
        
        # ===============================
        # ★ FrontBreak（最終）
        # ===============================
        FrontBreak = (
            StartCollapse == 1
            or WallBreak == 1
            or (
                max(Start[1:4]) - Start[0] > 0.05
            )
        )
    
        # ===============================
        # TURN
        # ===============================

        TurnRaw=[0.30*Skill[i]+0.55*Foot[i]+0.15*Engine[i] for i in range(6)]
        Turn=TurnRaw

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
        
        MotorScore = normalize(M)
        
        # ===============================
        # ★ AttackIndex補正（統合）
        # ===============================
        for i in range(6):
        
            # モーター（条件付きで強化）
            if MotorScore[i] > 0.60 and Foot[i] > 0.50:
                AttackIndex[i] += 0.02
        
            elif MotorScore[i] > 0.55:
                AttackIndex[i] += 0.03
        
            # 展示F
            if ExF[i] == 1:
        
                if Foot[i] > 0.50 and Turn[i] > 0.50:
                    AttackIndex[i] *= 1.02
                else:
                    AttackIndex[i] *= 0.90
        
            # 良ST
            elif GoodST[i] == 1:
                AttackIndex[i] *= 1.05
        #外壁用
                
        wall_penalty = [1.0]*6

        for i in range(4,6):
        
            if i == 5:
        
                wall_hit = (
                    max(CPI[2:5]) > CPI[5] - 0.03
                    and max(Turn[2:5]) >= Turn[5] - 0.02
                )
        
                if wall_hit:
                    wall_penalty[5] = 0.75
        
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
        
            # ★ ここだけにする（重要）
            if (
                can_attack
                or start_attack
                or (chance_flag and strong)
            ):
                attackers.append(i)
        
        # 重複削除（これも重要）
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
        
        # ===============================
        # ★ 崩れは攻め扱い（主トリガー）
        # ===============================
        if StartCollapse == 1:
            AttackWeak = 1
            DAS = max(DAS, 0.08)
        
        # ===============================
        # ★ 壁崩れ（補助）
        # ===============================
        if WallBreak == 1:
            DAS += 0.02   # ←弱める
        
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
        if DAS > MID:
            race_score += 1.2
        
        elif DAS > WEAK:
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

            value = 1 + (0.18 + 0.25*ChaosScore) * (Start[i] - AvgStart)

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
        
        FirstScore = []

        for i in range(6):
        
            val = (
                0.24*Start[i]
                +0.16*Skill[i]
                +0.14*Foot[i]
                +0.18*Turn[i]
                +0.18*LaneWin[i]
            )
            
            # ===============================
            # ★ 外の事前カット（超重要）
            # ===============================
            if (
                i >= 4
                and AttackSuccess == 0
                and DAS < 0.12
                and Start[i] < Start[i-1] - 0.02
            ):
        
                val *= 0.92
                        
            # ★ 4の突破
            if i == 3:
                if Start[3] >= max(Start[1:3]) + 0.015:
                    val *= 1.07
            
            # ★ 攻め勝ち
            if i in attackers:
                if AttackSuccess == 1:
                    val *= 1.10
                elif DAS > 0.10:
                    val *= 1.06
                        
            # ★ 崩れ展開
            if StartCollapse == 1 and i >= 2:
                val *= 1.05
                
            # ===============================
            # ★ 外の突破判定（1着用）
            # ===============================
            if i >= 3:
                
                front_break = (
                    Start[0] < Start[2] - 0.04
                    or Start[1] < Start[2] - 0.03
                )
                
                outer_fast = (
                    Start[i] > max(Start[1:4]) + 0.02
                )
                
                if front_break and outer_fast:
                    val *= 1.12   # ← 少し弱める（1.15→1.12）
                
                
            # ===============================
            # ★ 外の基本抑制（修正）
            # ===============================
            if i >= 4:

                outer_power = 0.4*CPI[i] + 0.3*Start[i] + 0.3*Foot[i]
            
                if DAS < 0.08:
                    val *= (0.75 + 0.2 * outer_power)
            
                elif DAS < 0.12:
                    val *= (0.85 + 0.15 * outer_power)
            
                else:
                    val *= (0.92 + 0.10 * outer_power)
                
                
                # ===============================
                # ★ 外パワー判定（軽量化）
                # ===============================
                outer_power = (
                    0.4 * CPI[i]
                    + 0.3 * Start[i]
                    + 0.3 * Foot[i]
                )
                
                if DAS < 0.08:
                
                    if outer_power < 0.52:
                        val *= 0.75   # ← 0.55→緩和
                    else:
                        val *= 0.90
                
                elif DAS < 0.12:
                
                    if outer_power < 0.50:
                        val *= 0.85
                    else:
                        val *= 0.95
                
                else:
                    val *= 1.00   # ← 0.95→消さない
                
            # ===============================
            # ★ グレーゾーンだけ外を少し許可
                # ===============================
            if (
                NoAttackFlag == 0
                and DAS < WEAK
                and i >= 3
            ):
                if Start[i] >= max(Start[2:6]) - 0.01:
                    val *= 0.60   # ← 0.70→0.60
                else:
                    val *= 0.30   # ← 0.25→少し緩和
            
            FirstScore.append(val)
            
        # ===============================
        # ★ 2差し強化（修正）
        # ===============================
        if (
            NoAttackFlag == 0
            and CPI[1] >= CPI[0] - 0.03
            and Start[1] <= Start[0] + 0.03
        ):
        
            FirstScore[1] *= 1.12
            FirstScore[0] *= 0.95
        
        elif (
            NoAttackFlag == 0
            and CPI[1] >= CPI[0] - 0.06
            and Start[1] <= Start[0] + 0.05
        ):
        
            FirstScore[1] *= 1.06
            FirstScore[0] *= 0.97
        
        # ===============================
        # ★ 6の強さ分類（最終版）
        # ===============================
        
        Strong6 = (
            CLS[5] == "A1"
            and CPI[5] >= 0.53
            and Foot[5] >= 0.52
            and Start[5] >= Start[3] - 0.015
        )
        
        SemiStrong6 = (
            CLS[5] in ["A1","A2"]
            and CPI[5] >= 0.50
            and Foot[5] >= 0.50
            and Start[5] >= Start[3] - 0.02
            and DAS > MID
        )
        
        Normal6 = (
            CPI[5] >= 0.46
            and Foot[5] >= 0.48
        )
        
        Weak6 = not (Strong6 or SemiStrong6)
        
        FS_mult = [1.0]*6
        
        # ===============================
        # ★ 0 レイヤー1（最重要・修正版）
        # ===============================
        
        # ★ 展開ゾーン分類（追加）
        if DAS < 0.01:

            RaceZone = "no_attack"
        
        elif DAS < 0.06:
        
            RaceZone = "weak"
        
        else:
        
            RaceZone = "attack"
            

        # ===============================
        # ★ 1 インST差（ここ）
        # ===============================
        diff = max(Start[1:4]) - Start[0]
        
        if diff > 0.06:
            FS_mult[0] *= 0.50
        elif diff > 0.04:
            FS_mult[0] *= 0.70
        elif diff > 0.02:
            FS_mult[0] *= 0.80
            
            
        
            
        # ===============================
        # ★ 2 モード別 性格付け（最重要）
        # ===============================
        
        if mode == "no":
            FS_mult[0] *= 1.15
            for i in range(4,6):
                FS_mult[i] *= 0.60
        
        elif mode == "weak":
            FS_mult[0] *= 0.85
            FS_mult[2] *= 1.15
            FS_mult[3] *= 1.10
        
        elif mode == "attack":
            FS_mult[0] *= 0.75
            FS_mult[3] *= 1.10
            FS_mult[4] *= 1.10
            FS_mult[5] *= 1.08
        
            
        # ===============================
        # ★ 壁判定（FS後に入れる）
        # ===============================
        CLASS_WALL = {
            "A1": 1.10,
            "A2": 1.05,
            "B1": 0.95,
            "B2": 0.90
        }
        
        for i in range(1,6):
        
            prev = i - 1
        
            wall = (
                0.5 * Turn[prev] +
                0.3 * Skill[prev] +
                0.2 * Engine[prev]
            ) * CLASS_WALL[CLS[prev]]
        
            attack = (
                0.4 * Start[i] +
                0.3 * Turn[i] +
                0.3 * Foot[i]
            )
        
            if attack > wall + 0.02:
                FS_mult[i] *= 1.08
                FS_mult[prev] *= 0.94
            
        # ===============================
        # ★ 2 壁崩れ → 3優遇（ここに移動）
        # ===============================
        if WallBreak == 1:
            FS_mult[2] *= 1.12
            FS_mult[3] *= 1.05

            
        if WeakLeader is not None and AttackWeak == 1 and AttackSuccess == 0:
            FS_mult[WeakLeader] *= 1.10
            
         # ===============================
        # ★ 2 ゾーン別処理（整理版）
        # ===============================
        
        if RaceZone == "no_attack":
        
            weak_factor = min(1.0, DAS / WEAK)
        
            FS_mult[3] *= 0.60
            FS_mult[4] *= 0.40
            FS_mult[5] *= 0.30
        
            FS_mult[0] *= 1.12
        
            if CPI[1] >= CPI[0] - 0.08:
                FS_mult[1] *= 1.15
        
            if Start[1] < Start[0] - 0.02:
                FS_mult[1] *= 0.90
            elif CPI[1] < CPI[0] - 0.08:
                FS_mult[1] *= 0.92
        
            if CPI[2] < 0.45:
                FS_mult[2] *= 0.92
            elif Start[2] >= max(Start) - 0.005:
                FS_mult[2] *= 0.90
        
            if CPI[3] < 0.40:
                FS_mult[3] *= 0.80
            elif Start[3] < Start[2] - 0.02:
                FS_mult[3] *= 0.85
        
            FS_mult[4] *= 0.65
            FS_mult[5] *= 0.50
        
        
        elif RaceZone == "weak":
        
            FS_mult[0] *= 0.85
            FS_mult[1] *= 0.95
            FS_mult[2] *= 1.10
            FS_mult[3] *= 1.08
                
        
        else:  # attack
        
            if DAS > STRONG:

                FS_mult[0] *= 0.85
                FS_mult[1] *= 0.90
                FS_mult[2] *= 1.10
                FS_mult[3] *= 1.12
        
            elif DAS > MID:
        
                FS_mult[0] *= 0.88
                FS_mult[1] *= 0.93
                FS_mult[2] *= 1.05
                FS_mult[3] *= 1.06
        
            else:
        
                FS_mult[0] *= 0.92
                FS_mult[1] *= 0.97
                    

            
        # ===============================
        # ★ 2 展開補正
        # ===============================
        
        if NoAttackFlag == 1:
            FS_mult[0] *= 1.05
        
        # ===============================
        # ★ 3 個別補正（統一）
        # ===============================
        for i in range(6):
        
            # F
            if Fcount[i] == 1:
                FS_mult[i] *= 0.92
            elif Fcount[i] >= 2:
                FS_mult[i] *= 0.85
        
            # 級別
            if Class[i] == "A1":
                FS_mult[i] *= 1.05
        
            # CPI
            if CPI[i] > 0.28:
                FS_mult[i] *= 1.05
            
        # イン性能
        if Skill[0] >= 0.55 and Engine[0] >= 0.50:
            FS_mult[0] *= 1.05
        
        # 3攻め
        if AttackIndex[2] >= AttackIndex[1] and DAS > WEAK and NoAttackFlag == 0:
            FS_mult[2] *= 1.08
        
        # 4性能
        if NoAttackFlag == 0 and AttackSuccess == 1 and DAS > MID:
            if Turn[3] >= max(Turn[1], Turn[2]) and Foot[3] >= max(Foot[1], Foot[2]):
                FS_mult[3] *= 1.05
        
        # OuterSlip
        if OuterSlip and DAS > MID:
            for i in range(4,6):
                if Start[i] >= max(Start) - 0.005:
                    FS_mult[i] *= 1.10
        
        # 主役取りこぼし
        if CLS[3] == "A1" and DAS > WEAK and NoAttackFlag == 0:
            if Start[3] <= Start[2] + 0.01:
                FS_mult[3] *= 0.90
                
        # ===============================
        # ★ 3 能力逆転（軽量版）
        # ===============================
        
        for i in range(1,6):
        
            gap = CPI[i] - CPI[0]
        
            if (
                gap > 0.06
                and Start[i] >= Start[0] - 0.02
            ):
                # 軽く上げる
                FS_mult[i] *= 1.06
        
                # イン少し削る
                FS_mult[0] *= 0.95
        
                # ターン優位なら少し追加
                if Turn[i] > Turn[0]:
                    FS_mult[i] *= 1.03
        
                # 足優位なら追加
                if Foot[i] > Foot[0]:
                    FS_mult[i] *= 1.02
                        
                
        
                  
        # ===============================
        # ★ 会場補正（完成版）
        # ===============================
        
        if venue == "多摩川":
        
            # ■ 常時（弱）
            FS_mult[0] *= 1.05
        
            # ■ 条件
            if DAS < 0.05:
                FS_mult[4] *= 0.92
                FS_mult[5] *= 0.90
        
        
        elif venue == "びわこ":
        
            # ■ 常時（ほぼ無し）
        
            # ■ 条件
        
            if DAS > WEAK and AttackSuccess == 1:
                FS_mult[2] *= 1.05
                FS_mult[3] *= 1.06
        
        
        elif venue == "桐生":
        
            # ■ 常時（弱）
            FS_mult[0] *= 0.97
        
            # ■ 条件
            if DAS > WEAK and AttackSuccess == 1:
                FS_mult[2] *= 1.07
                FS_mult[3] *= 1.08
        
        
        elif venue == "住之江":
        
            # ■ 常時（弱）
            FS_mult[1] *= 0.95
        
            # ■ 条件（ここが本体）
            if DAS > 0.04:
                FS_mult[2] *= 1.04
                FS_mult[3] *= 1.05
        
            if InsideSurvival[0] < 0.65:
                FS_mult[0] *= 0.95
        
        
        elif venue == "丸亀":
        
            # ■ 常時なし
        
            # ■ 条件（ヒモ荒れ）
            if 0.04 < DAS < 0.10:
                FS_mult[2] *= 1.05
                FS_mult[3] *= 1.05
                FS_mult[4] *= 1.03
        
        
        elif venue == "蒲郡":
        
            # ■ 常時なし
        
            # ■ 条件（軽微）
            if DAS > WEAK and AttackSuccess == 1:
                FS_mult[2] *= 1.04
                FS_mult[3] *= 1.05
        
        
        elif venue == "三国":
        
            # ■ 常時（弱）
            FS_mult[0] *= 1.04
        
            # ■ 条件（差し水面）
            if DAS < 0.06:
                FS_mult[1] *= 1.05
                FS_mult[2] *= 1.05
        
            if DAS > 0.04:
                FS_mult[3] *= 1.03
        
        
        elif venue == "常滑":
        
            # ■ 常時（弱）
            FS_mult[1] *= 0.96
        
            # ■ 条件
            if DAS > 0.04:
                FS_mult[2] *= 1.05
        
            if DAS < 0.06:
                FS_mult[4] *= 0.95
                FS_mult[5] *= 0.94

        FS_tmp = [FirstScore[i]*FS_mult[i] for i in range(6)]
        
        TotalFirst = sum(FS_tmp) if sum(FS_tmp) > 0 else 1e-6

        P1 = [FS_tmp[i]/TotalFirst for i in range(6)]
        
        # ===============================
        # ★ 最終FirstScore
        # ===============================
        FinalFirst = [FirstScore[i]*FS_mult[i] for i in range(6)]
        
        total = sum(FinalFirst)
        if total <= 0:
            total = 1e-6
        
        P1 = [x / total for x in FinalFirst]
        
        # ★ 頭分散（最重要）
        top = sorted(P1, reverse=True)
        
        if top[0] - top[2] < 0.06:
        
            for i in range(6):
                if P1[i] >= top[2]:
                    P1[i] *= 1.05
        
        # ===============================
        # ★ P1圧縮ガード（完成版）
        # ===============================
        P1_pre = P1.copy()
        
        top = sorted(P1_pre, reverse=True)
        
        # 上位拮抗なら上位3艇を少し持ち上げる
        if top[0] - top[2] < 0.07:
        
            for val in top[:3]:
                idx = P1_pre.index(val)
                P1[idx] *= 1.08
        
        # 再正規化（絶対必要）
        total = sum(P1)
        P1 = [p / total for p in P1]
        
        
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
            AttackBoost = [1.0]*6

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
        FinalFirst = [FirstScore[i]*FS_mult[i] for i in range(6)]

        
        debug_log.append(("FirstScore", [round(x,3) for x in FinalFirst]))
        debug_log.append(("順位", sorted(range(6), key=lambda i: FinalFirst[i], reverse=True)))
        debug_log.append(("CPI", [round(x,3) for x in CPI]))
        debug_log.append(("Start", [round(x,3) for x in Start]))
        start_rank = sorted(range(6), key=lambda i: Start[i])
        debug_log.append(("StartRank", start_rank))
        start_rank = sorted(range(6), key=lambda i: Start[i])
        debug_log.append(("StartRank", start_rank))
        # ★ デバッグ追加（ここ！！）
        if len(debug_log) > 50:
            debug_log = debug_log[-50:]
        debug_log.append(("P1_pre", [round(x,4) for x in FinalFirst]))
        
        
        TotalFirst = sum([FinalFirst[i] for i in range(6) if Active[i]==1])
        
        TotalFirst = sum([FinalFirst[i] for i in range(6) if Active[i]==1])
        
        
        # 再正規化（絶対必要）
        total = sum(P1)
        if total > 0:
            P1 = [p / total for p in P1]
            
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
        
                # 再正規化
                total = sum(P1)
                P1 = [p / total for p in P1]
                
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
                or WallBreak == 1
                or Start[1] < Start[0] - 0.02
                or Start[2] < Start[1] - 0.02
                or max(Start[1:4]) - Start[0] > 0.04

            )
        
            if i >= 4:

                if DAS < 0.09:
                    P1[i] *= 0.20   # ←強化
            
                if DAS < 0.08:
                    P1[i] *= 0.10   # ←さらに強化

        # ===============================
        # トップ集中ブースト
        # ===============================
        top = max(P1)

        for i in range(6):
            if P1[i] == top:
                if ChaosScore < 0.45:
                    P1[i] *= 1.07   # 固いときだけ強化
                else:
                    P1[i] *= 1.05   # 荒れはそのまま

        # ===== 正規化 =====

        total_p1 = sum(P1)

        if total_p1 > 0:
            P1 = [p / total_p1 for p in P1]
            
        for i in range(4,6):

            if (
                AttackSuccess == 0
                and DAS < 0.12
                and Start[i] < Start[i-1] - 0.02
            ):
                # 既存ロジックと競合しないように弱〜中で調整
                if DAS < 0.08:
                    P1[i] *= 0.5   # ←ここは0.1じゃなくて緩める
                else:
                    P1[i] *= 0.7
            
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
        # ★ デバッグ（ここが正解）
        debug_log.append(("SecondAdj_pre", [round(x,4) for x in SecondAdj]))
        
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
        if RaceZone == "weak":
        
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
        
            elif DAS > MID:
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
        
            elif DAS > MID:
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
                
                is_fast = Start[i] >= Start[i-1] - 0.01
                has_power = Foot[i] >= 0.50 or CPI[i] >= 0.48
                
                if is_fast and has_power:

                    if DAS > STRONG:
                    
                        if i == 4:
                            SecondAdj[i] *= 1.05
                        else:  # 6
                            SecondAdj[i] *= 1.07
                    
                    elif DAS > MID:
                    
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
            if DAS > MID:
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
        
            if Active[a] == 0:
                continue
        
            if P1[a] < max(P1) * (0.65 + 0.15*(1-ChaosScore)):
                continue
        
        
            # ===============================
            # ★ local生成
            # ===============================
            SecondAdj_local = SecondAdj_final.copy()
            ThirdAdj_local  = ThirdAdj_final.copy()
            
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
            
                    # 外は条件付きにする（重要）
                    if i >= 4:
                        if (
                            Start[i] < Start[i-1] - 0.02
                            or CPI[i] < CPI[i-1] - 0.03
                        ):
                            continue
                                
                    if i >= 4:
                        SecondAdj_local[i] *= (1.05 * wall_penalty[i])
                        ThirdAdj_local[i]  *= (1.03 * wall_penalty[i])  # ←追加
                    else:
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
            
                SecondAdj_local[5] *= (1.02 * wall_penalty[5])
                ThirdAdj_local[5]  *= (1.05 * wall_penalty[5])
            
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
                        ThirdAdj_local[i] *= (1.06 * wall_penalty[i])
                    else:
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
            
                # 前より速い → 抜けてこれる
                if Start[i] > Start[i-1] + 0.02:
                    ThirdAdj_local[i] *= 1.10
            
                # 前より遅い → 詰まる
                elif Start[i] < Start[i-1] - 0.02:
                    ThirdAdj_local[i] *= 0.80
            
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
                SecondAdj_local[5] *= (1.08 * wall_penalty[5])
            
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
                SecondAdj_local[5] *= (1.10 * wall_penalty[5])
                
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
            
                # ■ 6コース
                if i == 5:
            
                    # ←ここ削除（wall_hit & wall_penalty代入）
                    # wall_hit = ...
                    # wall_penalty[5] = ...
            
                    # ★減衰は残す（重要）
                    if wall_penalty[5] < 1.0:
                        SecondAdj_local[5] *= 0.70
                        ThirdAdj_local[5]  *= 0.75
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
            
                        if i >= 4 and Start[i] < Start[i-1] - 0.01:
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
                        SecondAdj_local[i] *= (1.12 * wall_penalty[i])
                    else:
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
            
                    # 強い6は無条件で生かす
                    if Strong6 or Normal6:
                        SecondAdj_local[i] *= wall_penalty[i]
                        ThirdAdj_local[i]  *= wall_penalty[i]
                        continue
            
                    if alive:
                        SecondAdj_local[i] *= (1.05 * wall_penalty[i])
                        ThirdAdj_local[i]  *= (1.08 * wall_penalty[i])
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

            second_scores = [SecondAdj_local[i] for i in remain1]
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
            
        return results, ChaosScore, P1, DoubleAttackScore, InsideSurvival, debug_log, Start
                
    def run_zure_ai(order, NoAttackProb):

        results, ChaosScore, P1, DAS, IS, debug, Start = run_attack(order)
    
        if NoAttackProb > 0.95 and IS[0] > 0.60:
            return []
    
        AttackWeak, AttackSuccess, NoAttackProb_new = detect_state(debug, DAS)
    
        zure_results = []
    
        for a,b,c,p in results:
    
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
    
        for name, val in debug_log:
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
    
    for a,b,c,p in res_no:
        final[(a,b,c)] = final.get((a,b,c),0) + w_no*p
    
    for a,b,c,p in res_weak:
        final[(a,b,c)] = final.get((a,b,c),0) + w_weak*p
    
    for a,b,c,p in res_attack:
        final[(a,b,c)] = final.get((a,b,c),0) + w_at*p
    
    results = [(a,b,c,p) for (a,b,c),p in final.items()]
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
    
                new = (new_head, b, c, p * 0.95, "sec")
                SecondAxisResults.append(new)
    
            # セカンド頭強化
            elif a == SecondHead + 1:
                SecondAxisResults.append((a,b,c,p * 1.10, "sec"))
    
    # 合成
    results += SecondAxisResults
    # ===============================
    # ★ シャープ化 & 正規化 & カット（完成版）
    # ===============================
    
    # ① シャープ化
    power = 1.25 + 0.25 * ChaosScore
    
    new_results = []
    
    for r in results:
    
        if len(r) == 5:
            a,b,c,p,_ = r
            new_results.append((a,b,c,p,"sec"))
    
        else:
            a,b,c,p = r
            new_results.append((a,b,c,p**power))
    
    results = new_results
    
    
    # ② 正規化（secも維持）
    total = sum(r[3] for r in results)
    
    if total > 0:
        new_results = []
    
        for r in results:
    
            if len(r) == 5:
                a,b,c,p,_ = r
                new_results.append((a,b,c,p/total,"sec"))
            else:
                a,b,c,p = r
                new_results.append((a,b,c,p/total))
    
        results = new_results
    
    
    # ③ カット（secは保護）
    cut = 0.004 + 0.004 * (1 - ChaosScore)
    
    filtered = []
    
    for r in results:
    
        if len(r) == 5:
            a,b,c,p,_ = r
            filtered.append((a,b,c,p))
            continue
    
        a,b,c,p = r
    
        if 0.01 <= p <= 0.03:
            filtered.append((a,b,c, p * 1.10))
    
        elif p >= cut:
            filtered.append((a,b,c,p))
    
    results = filtered
    
    
    # ④ ソート
    results.sort(key=lambda x:x[3], reverse=True)
    # ===============================
    # ★ 外頭制限（先にやる）
    # ===============================
    tmp = []
    
    for a,b,c,p in results:
    
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
    
    for a,b,c,p in results:
    
        if NoAttackProb > 0.90 and a >= 4:
            continue
    
        tmp.append((a,b,c,p))
    
    results = tmp
    
    # ===============================
    # ★ 同一展開カット
    # ===============================
    seen = set()
    tmp = []
    
    for a,b,c,p in results:
    
        key = (a,b,c)
    
        if key in seen:
            continue
    
        seen.add(key)
        tmp.append((a,b,c,p))
    
    results = tmp
    
    # ===============================
    # ★ ソート（先にやる）
    # ===============================
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
    debug_text.append("")
    debug_text.append("RaceState:")
    debug_text.append(f"NoAttackProb: {round(NoAttackProb,4)}")
    debug_text.append(f"DAS: {round(DoubleAttackScore,4)}")
    debug_text.append(f"ChaosScore: {round(ChaosScore,4)}")
    
    # ===============================
    # 重み（今回の核心）
    # ===============================
    debug_text.append("")
    debug_text.append("Weights:")
    debug_text.append(f"w_no: {round(w_no,3)}")
    debug_text.append(f"w_weak: {round(w_weak,3)}")
    debug_text.append(f"w_at: {round(w_at,3)}")
    
    # ===============================
    # モード比較
    # ===============================
    debug_text.append("")
    debug_text.append("ModeScores:")
    debug_text.append(f"P1_no_top: {round(max(P1_no),3)}")
    debug_text.append(f"P1_weak_top: {round(max(P1_w),3)}")
    debug_text.append(f"P1_attack_top: {round(max(P1_a),3)}")
    
    # ===============================
    # 最終P1
    # ===============================
    debug_text.append("")
    debug_text.append("P1:")
    for i,p in enumerate(P1):
        debug_text.append(f"{i+1}: {round(p,4)}")
    
    # ===============================
    # 内部ログ（必要最低限）
    # ===============================
    debug_text.append("")
    debug_text.append("CoreDebug:")
    for name, val in debug_log_ex:
        if name in [
            "AttackWeak",
            "AttackSuccess",
            "Start",
            "P1_pre",
            "SecondAdj_pre",
            "ThirdAdj_pre"
        ]:
            debug_text.append(f"{name}: {val}")
            
    if a == 0:
    
        debug_text.append("=== CHECK ===")
        debug_text.append(f"Second: {[round(x,3) for x in SecondAdj_local]}")
        debug_text.append(f"Third : {[round(x,3) for x in ThirdAdj_local]}")
    
        sum2 = sum(SecondAdj_local)
        sum3 = sum(ThirdAdj_local)
        ratio = sum2 / sum3 if sum3 > 0 else 0
    
        debug_text.append(f"sum2: {round(sum2,3)}")
        debug_text.append(f"sum3: {round(sum3,3)}")
        debug_text.append(f"ratio: {round(ratio,3)}")
        debug_text.append("=============")
    
    debug_output = "\n".join(debug_text)
    
    
    
    
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
    