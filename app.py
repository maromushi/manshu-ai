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
    ExST=clamp(to_float_list(fix_length(ExST)),0,0.40)

    TurnTime=to_float_list(fix_length(TurnTime))
    LapTime=to_float_list(fix_length(LapTime))
    StraightTime=to_float_list(fix_length(StraightTime))

    Class=fix_class(Class)

    Fcount=to_int_list(fix_length(Fcount))

    ExEntry=fix_exentry(ExEntry)
    
    # ★ 欠場艇を進入から除外（修正版）
    new_entry = []
    
    for e in ExEntry:
        idx = e - 1
        if idx >= 0 and idx < 6 and Active[idx] == 1:
            new_entry.append(e)
    
    # ←ここから外（超重要）
    if len(new_entry) >= 3:
        ExEntry = new_entry
    else:
        ExEntry = [i+1 for i in range(6) if Active[i] == 1]
    
    # 足りなければ埋める
    while len(ExEntry) < 6:
        ExEntry.append(ExEntry[-1])

    ExhibitionF=[0,0,0,0,0,0]

    # =====================================
    # AI CORE
    # =====================================

    def run_ai(order):
        
        results = []

        FC=[Fcount[i] for i in order]
        
        CLS=[Class[i] for i in order]
        
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

        # ===============================
        # SKILL
        # ===============================

        WinScore=normalize(WR)
        PlaceScore=normalize(PR)

        SkillRaw=[WinScore[i] for i in range(6)]
        Skill=SkillRaw 
        
        # ===============================
        # ENGINE
        # ===============================

        EngineRaw=[M[i]/100 for i in range(6)]

        Engine = []

        for i in range(6):

            if Active[i]==0:
                Engine.append(0)
                continue

            motor_ratio = M[i] / max(avg_motor,1e-6)

            factor = 0.90+ 0.10*motor_ratio

            Engine.append(EngineRaw[i] * factor)

        # ===============================
        # EXHIBIT
        # ===============================

        AvgEx=sum(ET)/6

        TimeScore=normalize([AvgEx-x for x in ET])
        ExSTScore=normalize([0.30-x for x in EST])

        ExhibitRaw=[0.80*TimeScore[i]+0.20*ExSTScore[i] for i in range(6)]

        Exhibit=[]

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

        RawFoot=[
        0.42*TurnScore[i]+
        0.28*LapScore[i]+
        0.25*StraightScore[i]+
        0.08*Exhibit[i]
        for i in range(6)
        ]

        Foot=RawFoot

        for i in range(6):

            if Active[i]==0:
                continue

            motor_ratio = M[i] / max(avg_motor,1e-6)

            Foot[i] *= (0.90 + 0.10*motor_ratio)

        # 外は展示過信を少し下げる
        for i in range(6):
            if i >= 4:
                Foot[i] *= 0.95

        # ===============================
        # START
        # ===============================

        BaseStart = ([0.30 - x for x in ST])
        ExhibitStart = ([0.30 - x for x in EST])
        
        StartRaw=[0.75*BaseStart[i]+0.25*ExhibitStart[i] for i in range(6)]

        Start=StartRaw
        # F補正（階級 + 展示ST）

        F_TABLE = {
        "A1":{"F1":0.96,"F2":0.92},
        "A2":{"F1":0.94,"F2":0.88},
        "B1":{"F1":0.92,"F2":0.84},
        "B2":{"F1":0.88,"F2":0.78}
        }

        for i in range(6):

            cls = CLS[i]

            factor = 1

            if FC[i] == 1:
                factor = F_TABLE[cls]["F1"]

            elif FC[i] >= 2:
                factor = F_TABLE[cls]["F2"]

            # 展示ST補正
            if EST[i] <= 0.10:
                factor *= 1.10

            elif EST[i] <= 0.13:
                factor *= 1.05

            elif EST[i] >= 0.20:
                factor *= 0.90

            Start[i] *= factor
            
            # 遅いSTペナルティ（基本）

            penalty = 1.0
            
            if ST[i] > 0.20:
                Start[i] *= 0.90

            if ST[i] > 0.25:
                Start[i] *= 0.80

            # A1は軽減だけ（打ち消さない）
            if CLS[i] == "A1":
                penalty = max(penalty, 0.85)
            
            Start[i] *= penalty
    
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
            if i >= 4 and Engine[i] > 0.60:
                Velocity[i] *= 1.05

        # ===============================
        # INSIDE SURVIVAL
        # ===============================

        InsideSurvival=[
        0.40*Skill[i]+
        0.30*Engine[i]+
        0.20*Start[i]+
        0.10*Foot[i]
        for i in range(6)
        ]

        # ===============================
        # CPI
        # ===============================

        CPI=[
        0.20*Skill[i]+
        0.20*Engine[i]+
        0.22*Foot[i]+
        0.18*Turn[i]+
        0.20*Velocity[i]
        for i in range(6)
        ]

        AttackCPI=[
        0.35*Foot[i]+
        0.25*Turn[i]+
        0.20*Start[i]+
        0.20*Engine[i]
        for i in range(6)
        ]

        AttackIndex=[
        0.40*Start[i]+
        0.30*Foot[i]+
        0.20*Turn[i]+
        0.10*Engine[i]
        for i in range(6)
        ]
        
        # ===============================
        # ★ 攻め候補（複数化）
        # ===============================
        attackers = []
        
        for i in range(2,6):
            if (
                Start[i] >= Start[i-1] - 0.06
                and (
                    AttackIndex[i] >= max(AttackIndex[2:6]) - 0.05
                    or Turn[i] >= max(Turn[2:6]) - 0.03
                )
            ):
                attackers.append(i)
                
        attackers = sorted(
            attackers,
            key=lambda x: (
                0.35 * AttackIndex[x]
                + 0.25 * Start[x]      # ←追加（超重要）
                + 0.20 * Turn[x]
                + 0.15 * Foot[x]
                + 0.05 * Engine[x] 
                + 0.05 * max(0, Start[x] - Start[x-1])
            ),
            reverse=True
        )
        
        main_attackers = attackers[:2]

        OuterCluster = max(CPI[3:6]) - min(CPI[3:6])
        OuterClusterFlag = 1 if OuterCluster <= 0.06 else 0

        # ===== 6頭検知フラグ =====

        SixHeadFlag = 0

        if (
            CPI[5] >= max(CPI[3:6]) - 0.02
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

        MidCluster=max(CPI[1:4])-min(CPI[1:4])
        MidClusterFlag=1 if MidCluster<=0.05 else 0

        PerformanceSpread=max(CPI)-min(CPI)

        StartSpread=max(Start)-min(Start)

        InsideCollapse = 1 if (StartSpread > 0.10 and OuterClusterFlag == 1) else 0

        # ===============================
        # EXHIBIT LEADER
        # ===============================

        min_exst = min(EST)

        ExhibitLeader = [0]*6

        for i in range(6):
            if EST[i] == min_exst:
                ExhibitLeader[i] = 1

        # ===============================
        # SASHI CHANCE
        # ===============================

        SashiGap=[0]*6

        for i in range(1,6):
            SashiGap[i]=max(0,Start[i]-Start[i-1])
    
        # ===============================
        # ATTACK FLAG
        # ===============================

        TwoLaneAttackFlag = 1 if (
        Start[1] <= Start[0] + 0.05
        ) else 0

        ThreeLaneAttackFlag = 1 if (
        Start[2] <= Start[1] + 0.04
        ) else 0

        FourLaneAttackFlag = 1 if (
        Start[3] <= min(Start[1],Start[2]) + 0.02
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
        0.22 * max(0, AttackCPI[2] - AttackCPI[0]) +
        0.15 * max(0, Engine[2] - Engine[0]) +
        0.13 * max(0, Turn[2] - Turn[0])
        )

        FourLaneAttackScore = (
        0.22 * FourLaneAttackFlag +
        0.28 * max(0, Start[3] - Start[2]) +
        0.22 * max(0, AttackCPI[3] - AttackCPI[0]) +
        0.15 * max(0, Engine[3] - Engine[0]) +
        0.13 * max(0, Turn[3] - Turn[0])
        )

        OutsideFlow = (
        0.6*ThreeLaneAttackScore +
        0.8*FourLaneAttackScore
        )

        DoubleAttackScore = (
        (ThreeLaneAttackScore * FourLaneAttackScore)
        +
        0.5 * (TwoLaneAttackScore * ThreeLaneAttackScore)
        )
        
        # ===============================
        # ★ 攻め強度フラグ（統一）
        # ===============================
        StrongAttack = DoubleAttackScore > 0.13
        MidAttack    = 0.09 < DoubleAttackScore <= 0.13
        WeakAttack   = 0.06 < DoubleAttackScore <= 0.09
        NoAttackLine = DoubleAttackScore <= 0.06
        
        # ===============================
        # ★ 無風判定（絶対必要）
        # ===============================
        LowStartSpread = (max(Start) - min(Start)) < 0.08
        NoStrongAttacker = max(AttackIndex[2:6]) < 0.55
        
        if LowStartSpread and NoStrongAttacker:
            DoubleAttackScore *= 0.65
        
        
        # ===============================
        # ★ 攻め不発（最重要）
        # ===============================
        NoAttackFlag = 0

        WeakAttack_env = (
            DoubleAttackScore < 0.12
        )
        
        if (
            StartSpread < 0.08
            and WeakAttack_env
            and max(AttackIndex[2:6]) < 0.60   # ←ここ緩和
        ):
            NoAttackFlag = 1
            
        # ★ 疑似無風もNoAttack扱いにする
        if (
            0.06 <= DoubleAttackScore <= 0.12
            and (max(Start) - min(Start)) < 0.08
        ):
            NoAttackFlag = 1
            
        # ===============================
        # ★ 疑似攻め判定（ここに入れる）
        # ===============================
        PseudoAttack = max([
            max(0, Start[2] - Start[1]),
            max(0, Start[3] - Start[2]),
            max(0, Start[4] - Start[3])
        ])
              
        if (WeakAttack or MidAttack or StrongAttack) and NoAttackFlag == 0:
            DoubleAttackScore = max(DoubleAttackScore, PseudoAttack * 0.45)
        
        # ===============================
        # ★ 攻めタイプ判定（追加）
        # ===============================
        
        main_atk = None
        if len(main_attackers) > 0:
            main_atk = main_attackers[0]
        
        AttackType = "sashi"
        
        if main_atk is not None:
        
            # 基本は3基準（2コース起点）
            if main_atk >= 2:
        
                st_diff = Start[main_atk] - Start[main_atk-1]
        
                if st_diff > 0.04:
                    AttackType = "makuri"
        
                elif st_diff > 0.01:
                    AttackType = "makuri_sashi"
        
                else:
                    AttackType = "sashi"
        
            else:
                AttackType = "sashi"
                
        # ===============================
        # ★ 攻め失敗（A/B分離）
        # ===============================
        
        AttackFailA = 0
        AttackFailB = 0
        
        # ■A（メイン攻め）
        if len(main_attackers) >= 1:
        
            a = main_attackers[0]
        
            if a >= 1 and Start[a] < Start[a-1] - 0.025:
                AttackFailA = 1
        
        
        # ■B（サブ攻め）
        if len(main_attackers) >= 2:
        
            b = main_attackers[1]
        
            if b >= 1 and Start[b] < Start[b-1] - 0.03:
                AttackFailB = 1
        
                
        

        # ===============================
        # 攻め主体判定（改良版）
        # ===============================

        Attack2 = 1 if (
            Start[1] > Start[0] + 0.02
            and AttackIndex[1] > AttackIndex[0]
            and (Foot[1] >= Foot[0] or Engine[1] >= Engine[0])
        ) else 0


        Attack3 = 1 if (
            Start[2] > Start[1] + 0.02
            and AttackIndex[2] > AttackIndex[1]
            and (Foot[2] >= Foot[1] or Engine[2] >= Engine[1])
            and (
                CLS[2] in ["A1","A2"]
                or (
                    ExST[2] <= 0.05
                    and Start[2] >= Start[1]   # ★これ追加（ブレーキ）
                )
            )
        ) else 0

        Attack3Power = (
            max(0, Start[2] - Start[1]) +
            max(0, AttackIndex[2] - AttackIndex[1])
        )

        InsideBreak = 1 if (
            Start[0] < Start[1] - 0.03
            and Attack3 == 1
        ) else 0
        
        # ===============================
        # CHAOS CORE
        # ===============================

        OuterPower=(
        0.5*max(CPI[3:6])+
        0.3*sorted(CPI[3:6])[-2]+
        0.2*(sum(CPI[3:6])/3)
        )

        InsideWeak=1-InsideSurvival[0]

        ChaosScore=(
        0.20*OuterPower+
        0.25*InsideWeak+
        0.25*StartSpread+
        0.16*PerformanceSpread+
        0.05*TwoLaneAttackFlag+
        0.08*ThreeLaneAttackFlag+
        0.05*FourLaneAttackFlag+
        0.06*MidClusterFlag
        )

        ChaosScore=max(0,min(1,ChaosScore))

        if ChaosScore < 0.45:
            chaos_weight = 0.7   # 安定レース
        elif ChaosScore < 0.65:
            chaos_weight = 1.0   # 通常
        else:
            chaos_weight = 1.3   # 荒れ
            
        # ===============================
        # AUTO MODE 判定
        # ===============================
        
        race_score = 0
        
        # イン弱い
        if Skill[0] < 0.45:
            race_score += 1
        
        # スタートばらつき
        if max(Start) - min(Start) > 0.08:
            race_score += 1
        
        # 外強い
        if max(CPI[3:6]) > CPI[0]:
            race_score += 1
        
        # 展開あり
        if DoubleAttackScore > 0.13:
            race_score += 1
        
        # 判定
        use_mode = "ana" if race_score >= 2 else "safe"

        
        # ===============================
        # STAGE17
        # ===============================

        AvgStart=sum(Start)/6

        StartBoost=[]

        for i in range(6):

            value=1+(0.25+0.35*ChaosScore)*(Start[i]-AvgStart)

            value=max(0.75,value)

            StartBoost.append(value)

        DynamicInsideFactor=1

        if StartSpread>=0.12:
            DynamicInsideFactor=0.70
        elif StartSpread>=0.08:
            DynamicInsideFactor=0.82

        DynamicInsideFactor=max(0.60,DynamicInsideFactor)

        # ===== イン過信抑制 =====

        if CPI[1] >= CPI[0] - 0.05 and Start[1] <= Start[0] + 0.04:
            DynamicInsideFactor *= 0.88

        LaneWin=[

        0.58*DynamicInsideFactor*(1-0.25*ChaosScore),
        0.19+(0.45*(1-DynamicInsideFactor)*0.40)*(1+0.20*ChaosScore),
        0.16+(0.45*(1-DynamicInsideFactor)*0.30)*(1+0.25*ChaosScore),
        0.14+(0.45*(1-DynamicInsideFactor)*0.20)*(1+0.30*ChaosScore),
        0.07+(0.45*(1-DynamicInsideFactor)*0.07)*(1+0.35*ChaosScore),
        0.04+(0.45*(1-DynamicInsideFactor)*0.03)*(1+0.40*ChaosScore)

        ]

        # ===== 2差し強化補正 =====

        if CPI[1] >= CPI[0] - 0.03 and Start[1] <= Start[0] + 0.03:

            LaneWin[1] += 0.07
            LaneWin[0] -= 0.07

        elif CPI[1] >= CPI[0] - 0.06 and Start[1] <= Start[0] + 0.05:

            LaneWin[1] += 0.04
            LaneWin[0] -= 0.04
            
        # ===============================
        # ★ FirstScoreフラグ箱
        # ===============================

        FirstScore=[
        0.35*Start[i]+
        0.25*Skill[i]+
        0.15*Engine[i]+
        0.15*Foot[i]+
        0.20*Turn[i]+
        0.15*LaneWin[i]
        for i in range(6)
        ]
        
        FS_mult = [1.0]*6

        for i in range(6):
            if Fcount[i] == 1:
                FS_mult[i] *= 0.95
            elif Fcount[i] >= 2:
                FS_mult[i] *= 0.90
                
        # ===============================
        # ★ FS_mult統一ブロック（完成形）
        # ===============================
        # ===============================
        # ★ 共倒れ（A/B分離版）
        # ===============================
        
        if len(main_attackers) >= 1:
        
            # ===============================
            # ■① 1 vs 攻めA
            # ===============================
            if len(main_attackers) >= 1:

                a = main_attackers[0]
            
                if a >= 2:
            
                    st_gap = Start[a] - Start[0]
            
                    if (
                        -0.01 <= st_gap <= 0.03
                        and Turn[a] > Turn[0]
                    ):
                        FS_mult[0] *= 0.88
                        FS_mult[a] *= 0.94
        
        
        # ===============================
        # ■② 1 vs 攻めB（2番手）
        # ===============================
        if len(main_attackers) >= 2:

            b = main_attackers[1]
        
            if b >= 2:
        
                st_gap = Start[b] - Start[0]
        
                if (
                    -0.01 <= st_gap <= 0.03
                    and Turn[b] > Turn[0]
                ):
                    FS_mult[0] *= 0.92
                    FS_mult[b] *= 0.96
        
        
        # ===============================
        # ■③ 攻めA vs 攻めB
        # ===============================
        if len(main_attackers) >= 2:

            a = main_attackers[0]
            b = main_attackers[1]
        
            if (
                abs(Turn[a] - Turn[b]) < 0.04
                and abs(AttackIndex[a] - AttackIndex[b]) < 0.05
            ):
                das = DoubleAttackScore
        
                tomo_boost = 1.02 + 0.06 * min(1.0, das / 0.12)
        
                FS_mult[a] *= tomo_boost
                FS_mult[b] *= tomo_boost
                
        # ===============================
        # ★ イン流れ（複数攻め版）
        # ===============================
        if (WeakAttack or MidAttack or StrongAttack) and NoAttackFlag == 0:
        
            for atk in main_attackers:
        
                st_gap = Start[atk] - Start[0]
        
                if (
                    -0.01 <= st_gap <= 0.03
                    and Turn[0] < Turn[atk]
                ):
                    FS_mult[0] *= 0.86
                    break
        
        
        
        # ===============================
        # ① レースタイプ分岐（最重要）
        # ===============================
        
        if NoAttackFlag == 1:
            race_type = "no_attack"
        
        elif DoubleAttackScore > 0.13:
            race_type = "StrongAttack"
        
        elif DoubleAttackScore > 0.09:
            race_type = "MidAttack"
        
        elif (WeakAttack or MidAttack or StrongAttack):
            race_type = "WeakAttack"
        
        else:
            race_type = "normal"
            
        if NoAttackFlag == 1:
            FS_mult[2] *= 0.95
            FS_mult[3] *= 0.93
            FS_mult[4] *= 0.90
            FS_mult[5] *= 0.75
        
        
        # ===============================
        # ② レースタイプごとの処理
        # ===============================
        
        if race_type == "StrongAttack":
        
            FS_mult[0] *= 0.85
            FS_mult[1] *= 0.90
            FS_mult[2] *= 1.10
            FS_mult[3] *= 1.12
        
        elif race_type == "MidAttack":
        
            FS_mult[0] *= 0.88
            FS_mult[1] *= 0.93
            FS_mult[2] *= 1.05
            FS_mult[3] *= 1.06
        
        elif race_type == "WeakAttack":
        
            FS_mult[0] *= 0.92
            FS_mult[1] *= 0.97
        
        elif race_type == "no_attack":
        
            FS_mult[0] *= 1.08
            FS_mult[1] *= 0.95
            FS_mult[2] *= 0.95
            FS_mult[3] *= 0.95
        
        else:  # normal
        
            FS_mult[0] *= 1.10
            
        # ===============================
        # ★ 疑似無風（SemiNoEvent）
        # ===============================
        SemiNoEvent = (
            0.06 <= DoubleAttackScore <= 0.12
            and (max(Start) - min(Start)) < 0.08
        )
        
        if SemiNoEvent:
            FS_mult[0] *= 1.08   # イン残る
            FS_mult[1] *= 1.05   # 2差し残る
            FS_mult[2] *= 0.98   # 3は頭弱め
            FS_mult[3] *= 0.95   # 外抑制
            
        # ★ 攻め成功でもイン残る（修正版）

        if (
            (MidAttack or StrongAttack)
            and len(main_attackers) > 0
            and AttackFailA == 0   # ←追加
        ):
        
            best_atk = max(main_attackers, key=lambda x: AttackIndex[x])
        
            if (
                Start[0] >= Start[best_atk] - 0.02
                and InsideSurvival[0] >= 0.50
            ):
                FS_mult[0] *= 1.06
            
        # ===============================
        # ★ 攻め失敗イン復活（A/B分離）
        # ===============================
        
        if AttackFailA == 1:
            FS_mult[0] *= 1.10
        
        if AttackFailB == 1:
            FS_mult[0] *= 1.05
        
        # 攻め側の失敗反映
        if len(main_attackers) >= 1:
            a = main_attackers[0]
            if AttackFailA == 1:
                FS_mult[a] *= 0.90
        
        if len(main_attackers) >= 2:
            b = main_attackers[1]
            if AttackFailB == 1:
                FS_mult[b] *= 0.93
                
        # ===============================
        # ③ 個別性能補正（ここだけ許可）
        # ===============================
        
        # イン強いなら少し上げる（そのまま）
        if (
            Skill[0] >= 0.55
            and Engine[0] >= 0.50
        ):
            FS_mult[0] *= 1.05
        
        
        # 3が攻め役なら強化
        if (
            AttackIndex[2] >= AttackIndex[1]
            and (MidAttack or StrongAttack)   # ←ここ変更
            and NoAttackFlag == 0
        ):
            FS_mult[2] *= 1.08
        
        
        # 4が明確に強いなら
        if (
            Turn[3] >= Turn[1]
            and Foot[3] >= Foot[1]
            and (MidAttack or StrongAttack)   # ←ここ変更
            and NoAttackFlag == 0
        ):
            FS_mult[3] *= 1.08
            
        # 4・5コースの“強い時だけ”頭許可
        for i in range(6):
            if i >= 4 and CPI[i] >= 0.50:
                FS_mult[i] *= 1.10
        
        # ===============================
        # ★ 主役取りこぼし（最重要）
        # ===============================
        if (
            CLS[3] == "A1"
            and (WeakAttack or MidAttack or StrongAttack)
            and Start[3] <= Start[2] + 0.01
        ):
            FS_mult[3] *= 0.90
            
        # ===============================
        # ★ イン事故復活（これ）
        # ===============================
        if (
            CLS[0] in ["B1","B2"]
            and DoubleAttackScore < 0.08
        ):
            FS_mult[0] *= 1.08
        
        # ===============================
        # ★ 6の強さ分類（追加）
        # ===============================
        Strong6 = (
            CLS[5] == "A1"
            and CPI[5] >= 0.52
            and Start[5] >= Start[3] - 0.02
        )
        
        Normal6 = (
            CPI[5] >= 0.45
            and Foot[5] >= 0.48
        )
        
        SemiStrong6 = (
            CLS[5] == "A2"
            and CPI[5] >= 0.55
            and Start[5] >= Start[3] - 0.01
            and (MidAttack or StrongAttack)
        )
        
        # ===============================
        # ★ 低性能カット（ここ）
        # ===============================
        for i in range(6):
        
            if Foot[i] < 0.45 and Engine[i] < 0.50:
                FS_mult[i] *= 0.80
        
            if Foot[i] < 0.40:
                FS_mult[i] *= 0.75

            # ★ ここに追加
            if i == 5:
                if Start[5] < Start[3] - 0.02:
                    FS_mult[5] *= 0.55
        
                if AvgST[5] > 0.20:
                    FS_mult[5] *= 0.75
                    




        # ===============================
        # ★ 弱イン分散（最重要）
        # ===============================
        if NoAttackFlag == 1 and Skill[0] < 0.55:
        
            # 1の支配を崩す
            FS_mult[0] *= 0.88
        
            # 3・4を主役に引き上げる
            FS_mult[2] *= 1.08
            FS_mult[3] *= 1.10

        # ★ 1の過集中防止
        if NoAttackFlag == 1 and Start[0] < max(Start[1:4]):
            FS_mult[0] *= 0.90

        
        # ===============================
        # ★ イン安定補正（これが本命）
        # ===============================
        
        if (
            Skill[0] >= 0.50
            and Start[0] >= 0.13
            and InsideSurvival[0] >= 0.55
        ):
            FS_mult[0] *= 1.12
            
            
        # ===============================
        # ★ 攻め条件（←ここ！！！）
        # ===============================
        if (
            Turn[2] == max(Turn)
            and Foot[2] >= Foot[1]
            and (MidAttack or StrongAttack)   # ←ここだけ変更
        ):
            FS_mult[2] *= 1.25
            
        # ★ 3の展示攻め補強（追加）
        if (
            Start[2] >= Start[1] + 0.02
            and ExST[2] <= 0.05
        ):
            FS_mult[2] *= 1.15
            
        # ===============================
        # ★ 3のまくり差し強化（超重要）
        # ===============================
        if (
            Skill[2] >= 0.50
            and Foot[2] >= max(Foot[0], Foot[1])
            and Turn[2] >= max(Turn[0], Turn[1])
            and (MidAttack or StrongAttack)   # ←ここだけ変更
        ):
            FS_mult[2] *= 1.20
            
        
        # ===============================
        # ★ 外A1複数 → 軸分散モード
        # ===============================
        
        outer_a1 = 0

        for i in range(4,6):  # 5・6コース
            if CLS[i] == "A1" and Engine[i] >= 0.55:
                outer_a1 += 1
        
        if outer_a1 >= 2:
        
            for i in range(4,6):
                if CLS[i] == "A1":
                    FS_mult[i] *= 1.15   # 外の頭を引き上げ
        

        # ===== イン最低保証 =====
        # イン最低保証（独立させる）
        if Skill[0] >= 0.55 and Engine[0] >= 0.50:
            FS_mult[0] *= 1.08
        
        # ②（メイン差し）
        if (
            CPI[1] >= CPI[0] - 0.06
            and Start[1] <= Start[0] + 0.05
            and DoubleAttackScore < 0.07
        ):
            FS_mult[1] *= 1.02
            FS_mult[0] *= 0.97
        
        # ③（弱い差し）
        elif (
            CPI[1] >= CPI[0] - 0.10
            and Start[1] <= Start[0] + 0.07
            and DoubleAttackScore < 0.06
        ):
            FS_mult[1] *= 1.01
            FS_mult[0] *= 0.99
            
        # ===============================
        # ★ FS_tmp作成（←ここ追加）
        # ===============================
    
            
        # ★ 2の頭制限（これが本命）
        # ★ 2の頭制限（分岐版）
        if DoubleAttackScore > 0.13 and NoAttackFlag == 0:

            FS_mult[1] *= 0.88
        
            # ★ここに入れる
            if Turn[3] >= Turn[1] and Foot[3] >= Foot[1]:
                FS_mult[1] *= 0.90
            else:
                FS_mult[1] *= 0.95
        
        
        elif (MidAttack or StrongAttack) and NoAttackFlag == 0:
        
            FS_mult[1] *= 0.93
        
            if Turn[3] >= Turn[1] and Foot[3] >= Foot[1]:
                FS_mult[1] *= 0.90
            else:
                FS_mult[1] *= 0.95
        
        
        elif (WeakAttack or MidAttack or StrongAttack) and NoAttackFlag == 0:
        
            FS_mult[1] *= 0.97
            
            
        # ===============================
        # ★ イン残り補正（A1＋A2）
        # ===============================
        if CLS[0] == "A1":
            if Start[0] >= 0.13:
                FS_mult[0] *= 1.12
        
        elif CLS[0] == "A2":
            if Start[0] >= 0.14 and InsideSurvival[0] >= 0.52:
                FS_mult[0] *= 1.08
        
        elif CLS[0] == "B1":
            if (
                Start[0] >= 0.15
                and InsideSurvival[0] >= 0.55
                and DoubleAttackScore < 0.08
            ):
                FS_mult[0] *= 1.05
                
        # ===============================
        # ★ 会場補正（ここに入れる）
        # ===============================
        
        if venue == "多摩川":
            DynamicInsideFactor *= 1.08
            FS_mult[0] *= 1.10
            
            # 外の暴走だけ軽く抑える
            if DoubleAttackScore < 0.05:
                FS_mult[4] *= 0.95
                FS_mult[5] *= 0.92
        
        if venue == "びわこ":
            if StartSpread > 0.10:
                chaos_weight *= 0.9
                
            # でも完全イン信頼ではない
            if (MidAttack or StrongAttack) and NoAttackFlag == 0:
                FS_mult[2] *= 1.04
                FS_mult[3] *= 1.05
                
        if venue == "三国":
            for i in range(6):
                Turn[i] *= 0.95
                AttackIndex[i] *= 0.93
            
                    
        # ===============================
        # ★ 会場差分補正（最終）
        # ===============================
        
        # ■ 桐生（軽水面・まくり強）
        if venue == "桐生":
        
            # イン弱め
            if InsideSurvival[0] < 0.65:
                FS_mult[0] *= 0.93
        
            # 3・4攻め強化
            if (WeakAttack or MidAttack or StrongAttack) and NoAttackFlag == 0:
                FS_mult[2] *= 1.08
                FS_mult[3] *= 1.10
        
        
        # ■ 住之江（センター主役）
        elif venue == "住之江":
        
            # インさらに弱い
            if InsideSurvival[0] < 0.70:
                FS_mult[0] *= 0.90
        
            # 2を削る（最重要）
            FS_mult[1] *= 0.90
        
            # 3・4主役化
            if DoubleAttackScore > 0.04:
                FS_mult[2] *= 1.10
                FS_mult[3] *= 1.12
  
        
        
        # ■ 丸亀（ヒモ荒れ）
        elif venue == "丸亀":
        
            # 頭はそのまま（触らない）
        
            # 中間展開を広げる
            if 0.04 < DoubleAttackScore < 0.10:
                FS_mult[2] *= 1.05
                FS_mult[3] *= 1.06
        
        
        # ■ 蒲郡（浜名湖ほぼ互換）
        elif venue == "蒲郡":
        
            # ほぼそのまま＋微調整だけ
            if (MidAttack or StrongAttack) and NoAttackFlag == 0:
                FS_mult[2] *= 1.03
                FS_mult[3] *= 1.04
                
        #常滑
        elif venue == "常滑":

            # 2を弱める（最重要）
            FS_mult[1] *= 0.92
        
            # 3を少し上げる
            if DoubleAttackScore > 0.04:
                FS_mult[2] *= 1.05
        
            # 外は抑制
            if DoubleAttackScore < 0.06:
                FS_mult[4] *= 0.90
                FS_mult[5] *= 0.85
        
        
        # ===============================
        # ★ 攻め役の勝ち切り制限（5）
        # ===============================
        if (
            ExST[4] <= 0.05
            and Start[4] >= Start[2] - 0.02
        ):
            if not (
                Foot[4] >= max(Foot[1:4])
                or Turn[4] >= max(Turn[1:4])
            ):
                FS_mult[4] *= 0.85

        # ===============================
        # ST遅い艇の頭抑制（追加）
        # ===============================
        AvgStart = sum(Start)/6

        for i in range(6):
            if Start[i] < AvgStart - 0.04:
                FS_mult[i] *= 0.82
                        
            
        # ===============================
        # ★ 6の展開連動ブースト（ここ）
        # ===============================
        if (
            DoubleAttackScore > 0.13 and NoAttackFlag == 0
            and Start[5] >= Start[3] - 0.005
            and CLS[5] == "A1"
        ):
            FS_mult[5] *= 1.08
        
        if use_mode == "safe":
            FS_mult[0] *= 1.08
                
            for i in range(6):

                # 弱いイン削る
                if i == 0 and Skill[i] < 0.45:
                    FS_mult[i] *= 0.75
                        
                # ===============================
                #  外の頭条件化（修正）
                # ===============================
                if i >= 4:
                    if AttackIndex[i] < max(AttackIndex):
                        FS_mult[i] *= 0.85
                        

        # ===== 6頭処理 =====

        # ★ 条件を強化（ここが本質）
        StrongSixHead = (
            CPI[5] >= 0.60
            and Start[5] >= Start[3]
            and DoubleAttackScore > 0.13
            and NoAttackFlag == 0
        )
        
        if SixHeadFlag == 1 and StrongSixHead:
        
            boost = 1.15 + 0.25 * (CPI[5] - 0.50)
        
            if Engine[5] >= 0.60:
                boost += 0.03
        
            FS_mult[5] *= boost
            FS_mult[0] *= 0.85
            FS_mult[1] *= 0.90
        
        else:
        
            # ===== 6抑制（強弱分岐） =====
            
            if Normal6:
                FS_mult[5] *= 0.95
        
            if CPI[5] < 0.50:
                FS_mult[5] *= 0.60
        
            elif Start[5] < Start[3]:
                FS_mult[5] *= 0.70
        
            else:
                FS_mult[5] *= 0.80

        # ★ 6の最終制御（絶対必要）  
        if len(FirstScore) != 6 or len(FS_mult) != 6:
            st.write("長さエラー", len(FirstScore), len(FS_mult))
            st.stop()
            
        # ===============================
        # ★ 弱インなら強制攻め
        # =============================
            
        # 弱イン補正
            
        if AvgST[0] > 0.20:
            FS_mult[0] *= 0.92
            
        # ===============================
        # ★ 攻め展開時の外強化
        # ===============================
        
        if NoAttackFlag == 0:
        
            if DoubleAttackScore > 0.12 and NoAttackFlag == 0:
                FS_mult[2] *= 1.10
                FS_mult[3] *= 1.12
                FS_mult[0] *= 0.92
        
            elif DoubleAttackScore > 0.09 and NoAttackFlag == 0:
                FS_mult[2] *= 1.05
                FS_mult[3] *= 1.06
                FS_mult[0] *= 0.98
        
            else:
                FS_mult[0] *= 1.05
            

        # ===============================
        # ★ 中間展開のイン復活（最重要）
        # ===============================
        if (
            DoubleAttackScore > 0.04
            and DoubleAttackScore < 0.09
            and NoAttackFlag == 0
        ):
            FS_mult[0] *= 1.12
        
        
        # ===============================
        # ★ 攻め成立時の主役スライド（3を押す）
        # ===============================
        if DoubleAttackScore > 0.04 and NoAttackFlag == 0:
        
            # 3が攻め役 or 差し役として成立してる時だけ
            if (
                AttackIndex[2] >= AttackIndex[1] - 0.02
                and Foot[2] >= 0.48
            ):
                FS_mult[2] *= 1.06
                
        # ★ FS_mult暴走防止（必須）
        for i in range(6):
            FS_mult[i] = max(0.65, min(1.35, FS_mult[i]))              
        
        # ===============================
        # ★ 6の頭ブレーキ（ここに単独で置く）
        # ===============================
        if not (
            CLS[5] in ["A1","A2"]
            or (CPI[5] >= 0.50 and Foot[5] >= 0.52)
        ):
            FS_mult[5] *= 0.40
                
            # ===============================
            # ★ 2コース頭制御（汎用版）
            # ===============================
            if i == 1:
            
                sashi_ok = (
                    Start[1] >= Start[0] - 0.02
                    and Turn[1] >= Turn[0] - 0.02
                )
            
                inside_strong = (
                    InsideSurvival[0] >= 0.55
                )
            
                # 差し成立してない → 頭削る
                if not sashi_ok:
                    FS_mult[1] *= 0.85
            
                # インが強い → さらに削る
                if inside_strong:
                    FS_mult[1] *= 0.90
            
                # 攻め中途半端 → 頭じゃなくなる
                if DoubleAttackScore < 0.08:
                    FS_mult[1] *= 0.92
                    
                
        
        # ===============================
        # ★ FS_mult① 確定（ここで一旦固定）
        # ===============================
        FS_mult_base = FS_mult.copy()
        
        FinalFirst = [FirstScore[i]*FS_mult_base[i] for i in range(6)]

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
        AttackBoost5 = 1 + 0.35 * DoubleAttackScore
        AttackBoost6 = 1 + 0.25 * DoubleAttackScore

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
        # 展開モデル
        # ===============================

        CrashFactor=[1.0]*6
        SashiBoost=[1.0]*6

        if main_attacker is not None:

            attack_power = DoubleAttackScore

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
                * (0.70 + 0.50 * (FinalFirst[i] / max(FinalFirst)))
            )


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
            if ExhibitLeader[i] == 1 and i >= 3:
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
                    value = value*(1+0.20*DoubleAttackScore)

                elif i > main_attacker:
                    value = value*(1+0.08*DoubleAttackScore)

                elif i == main_attacker - 1:
                    value *= (1+0.06*DoubleAttackScore)

            LaneCPI.append(value)
        
        
        #デバック

        debug_log = []
        debug_log.append(("FirstScore", [round(x,3) for x in FinalFirst]))
        debug_log.append(("順位", sorted(range(6), key=lambda i: FinalFirst[i], reverse=True)))
        debug_log.append(("CPI", [round(x,3) for x in CPI]))
        debug_log.append(("Start", [round(x,3) for x in Start]))
        debug_log.append(("AttackFailA", AttackFailA))
        debug_log.append(("AttackFailB", AttackFailB))
        debug_log.append(("FinalFirst", [round(x,3) for x in FinalFirst]))
        
        
        TotalFirst = sum([FinalFirst[i] for i in range(6) if Active[i]==1])
        
        P1 = [
            (FinalFirst[i]/TotalFirst) if Active[i]==1 else 0
            for i in range(6)
        ]

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

        LaneBonus=[0.10,0.09,0.08,0.07,0.06,0.05]

        SecondScore=[
        0.33*Turn[i]+
        0.27*Foot[i]+
        0.20*Engine[i]+
        0.10*Velocity[i]+
        0.10*LaneBonus[i]
        + 0.05*Start[i]
        for i in range(6)
        ]
        
        
        SecondAdj = SecondScore.copy()
        ThirdAdj = [1.0]*6
        
        # ===============================
        # ★ 会場補正2
        # ===============================
        if venue == "三国":
        
            for i in range(6):
        
                if Start[i] >= max(Start) - 0.02:
                    SecondAdj[i] *= 1.10
                    ThirdAdj[i]  *= 1.12
        
                if 2 <= i <= 4 and CPI[i] >= 0.45:
                    ThirdAdj[i] *= 1.08
        
                if i == 0 and (WeakAttack or MidAttack or StrongAttack):
                    SecondAdj[0] *= 0.92
                    
        # ===============================
        # ★ 疑似無風（2・3着安定）
        # ===============================
        if (
            0.06 <= DoubleAttackScore <= 0.12
            and (max(Start) - min(Start)) < 0.08
        ):
            SecondAdj[1] *= 1.12
            ThirdAdj[2]  *= 1.15
        
        # ===============================
        # ★ 攻め失敗補正（調整版）
        # ===============================
        
        if AttackFailA == 1:
        
            fail_strength = min(1.0, DoubleAttackScore / 0.10)
        
            # ■イン復活（強すぎ防止）
            SecondAdj[0] *= (1.08 + 0.04 * (1 - fail_strength))
            ThirdAdj[0] *= (1.05 + 0.03 * (1 - fail_strength))
        
            # ■2の復活（軽め）
            SecondAdj[1] *= (1.04 + 0.03 * (1 - fail_strength))
        
            # ■攻め役は軽く削るだけ
            for atk in main_attackers:
                SecondAdj[atk] *= 0.93
        
        # ★ 攻め時の2残り復活（汎用版）

        if (MidAttack or StrongAttack) and NoAttackFlag == 0:
        
            st_good = Start[1] >= max(Start[0], Start[2]) - 0.01
            perf_ok = CPI[1] >= (sum(CPI)/6) - 0.05
        
            if st_good and perf_ok:
                SecondAdj[1] *= 1.12
        
        # ★ 攻め時のイン2着分岐（完成版）

        st_loss = Start[0] < Start[2]
        weak_inside = InsideSurvival[0] < 0.55
        
        # ===============================
        # ★ 攻めタイプ別イン残り（修正版）
        # ===============================
        
        if (WeakAttack or MidAttack or StrongAttack) and NoAttackFlag == 0:
        
            # --- Second（2着）---
            if AttackType == "makuri":
                SecondAdj[0] *= 0.80
            elif AttackType == "makuri_sashi":
                SecondAdj[0] *= 0.95
            elif AttackType == "sashi":
                SecondAdj[0] *= 1.12
        
            # --- Third（3着）---
            if AttackType == "makuri":
                ThirdAdj[0] *= 0.90
            elif AttackType == "makuri_sashi":
                ThirdAdj[0] *= 1.00
            elif AttackType == "sashi":
                ThirdAdj[0] *= 1.10
                    
                    
         # ★ 展開6の2着（修正版）さ
        
        if (MidAttack or StrongAttack) and NoAttackFlag == 0:
            if Start[5] == max(Start):
                ThirdAdj[5] *= 1.10 
        
        # ===============================
        # ★ スタート主導の外流入（追加）
        # ===============================
        for i in range(4,6):
        
            if (
                Start[i] >= max(Start[1:4]) - 0.01
                and (MidAttack or StrongAttack)
            ):
                # ★ 上げるんじゃなくて下げを無効化
                SecondAdj[i] = max(SecondAdj[i], 1.05)
                ThirdAdj[i]  = max(ThirdAdj[i], 1.05)
        
        
        # ===============================
        # ★ 外の暴走防止（最重要）
        # ===============================
        for i in range(4,6):

            valid = (
                (Foot[i] >= 0.50 or CPI[i] >= 0.48)
                and Start[i] >= Start[3] - 0.02
            )
            
            if StrongAttack:
                if valid:
                    SecondAdj[i] *= 1.08
                else:
                    SecondAdj[i] *= 0.85
            
            elif MidAttack:
                if valid:
                    SecondAdj[i] *= 1.00
                else:
                    SecondAdj[i] *= 0.88
            
            else:
                SecondAdj[i] *= 0.90
                
        # ===============================
        # ★ 5コースの入口制御（重要）
        # ===============================
        if (MidAttack or StrongAttack) and NoAttackFlag == 0:
        
            if (
                Start[4] >= Start[2] - 0.02   # ←位置条件（5は3基準）
            ):
                SecondAdj[4] *= 1.08
        
            else:
                SecondAdj[4] *= 0.85
                
                
                
        if (
            DoubleAttackScore > 0.13
            and NoAttackFlag == 0
            and Start[5] == max(Start)
            and CPI[5] > 0.45
            and Foot[5] > 0.48
        ):
            SecondAdj[5] *= 1.15
            
        
                
                
        
        # ===============================
        # ★ 攻め成功 前削り（A/B分離）
        # ===============================
        
        # ■A（メイン攻め）
        if len(main_attackers) >= 1:
        
            a = main_attackers[0]
        
            if AttackFailA == 0:  # 成功時のみ
        
                for i in range(a):
                    if i == 0 and InsideSurvival[0] >= 0.50:
                        continue  # インは例外（重要）
        
                    SecondAdj[i] *= 0.85
        
        
        # ■B（サブ攻め）
        if len(main_attackers) >= 2:
        
            b = main_attackers[1]
        
            if AttackFailB == 0:
        
                for i in range(b):
                    if i == 0 and InsideSurvival[0] >= 0.50:
                        continue
        
                    SecondAdj[i] *= 0.90
                    
        # ===============================
        # ★ 攻め後ろ流入（A/B分離）
        # ===============================
        
        # Aの後ろ
        if len(main_attackers) >= 1:
        
            a = main_attackers[0]
        
            if AttackFailA == 0:
        
                for i in range(a+1, 6):
                    if CPI[i] >= 0.50:
                        SecondAdj[i] *= 1.10
        
        
        # Bの後ろ
        if len(main_attackers) >= 2:
        
            b = main_attackers[1]
        
            if AttackFailB == 0:
        
                for i in range(b+1, 6):
                    SecondAdj[i] *= 1.05
                    
        # ===============================
        # 👇ここに追加（ThirdAdj）
        # ===============================
        
        # ===============================
        # ★ 攻め後ろ流入（3着 A/B分離）
        # ===============================
        
        # A
        if len(main_attackers) >= 1:
        
            a = main_attackers[0]
        
            if AttackFailA == 0:
        
                for i in range(a+1, 6):
                    ThirdAdj[i] *= 1.12
        
        
        # B
        if len(main_attackers) >= 2:
        
            b = main_attackers[1]
        
            if AttackFailB == 0:
        
                for i in range(b+1, 6):
                    ThirdAdj[i] *= 1.08
                    
        # ===============================
        # ★ 前崩れ（3着 A/B分離）
        # ===============================
        
        # A
        if len(main_attackers) >= 1:

            a = main_attackers[0]
        
            if AttackFailA == 0:
        
                for i in range(a):
                    ThirdAdj[i] *= 0.85
        
        
        # B
        if len(main_attackers) >= 2:
        
            b = main_attackers[1]
        
            if AttackFailB == 0:
        
                for i in range(b):
                    ThirdAdj[i] *= 0.90
        
        
        # ===============================
        # ★ 内の処理
        # ===============================
        
        if WeakAttack:
            if InsideSurvival[0] >= 0.45 and Start[0] >= Start[2] - 0.04:
                SecondAdj[0] *= 1.20
                ThirdAdj[0] *= 1.10
        
        elif MidAttack:
            if InsideSurvival[0] >= 0.45 and P1[0] < 0.25:
                SecondAdj[0] *= 1.12
                ThirdAdj[0] *= 1.05
        
        elif StrongAttack:
            SecondAdj[0] *= 0.90
        
        
        # ===============================
        # ★ イン残り
        # ===============================
        if (
            0.07 < DoubleAttackScore <= 0.13
            and InsideSurvival[0] >= 0.48
            and Start[0] >= Start[2] - 0.04
            and P1[0] < 0.25
        ):
            SecondAdj[0] *= 1.18
            ThirdAdj[0] *= 1.05
            
            
        # ===============================
        # ★ イン3着保険
        # ===============================
        if (
            DoubleAttackScore > 0.13 and NoAttackFlag == 0
            and Skill[0] >= 0.45
        ):
            ThirdAdj[0] *= 1.10
        
        # ===============================
        # ★ 会場補正（2着）
        # ===============================
        if venue == "多摩川":
            SecondAdj[0] *= 1.05   # イン少し残る
            SecondAdj[4] *= 1.10   # 5コース流れ
        
        if venue == "びわこ":
            SecondAdj[0] *= 1.08
            SecondAdj[1] *= 1.05
        
        if venue == "常滑":
            SecondAdj[2] *= 1.08
            SecondAdj[3] *= 1.10
        
        if venue == "桐生":
            SecondAdj[0] *= 1.06
            SecondAdj[1] *= 1.05
        
        if venue == "住之江":
            if (MidAttack or StrongAttack) and NoAttackFlag == 0:
                SecondAdj[3] *= 1.10
                SecondAdj[4] *= 1.08
                
        # ===============================
        # ★ 展開拾い（複数攻め）
        # ===============================
        if (MidAttack or StrongAttack) and NoAttackFlag == 0:   # ←これ追加
            if len(main_attackers) > 0:
                main_atk = main_attackers[0]
            else:
                main_atk = None
        
            if main_atk is not None:
                target = main_atk + 1
                if target < 6:
                    SecondAdj[target] *= 1.10
                    ThirdAdj[target] *= 1.15
        
        
        # ===============================
        # ★ 階級補正（最重要）
        # ===============================
        for i in range(6):
        
            if CLS[i] == "A1":
                SecondAdj[i] *= 1.05
        
            elif CLS[i] == "A2":
                SecondAdj[i] *= 1.03
        
            elif CLS[i] == "B2":
                SecondAdj[i] *= 0.95
        
        # ===============================
        # ★ 外残りフラグ（5・6用）
        # ===============================
        
        FlowOuter = (
            (MidAttack or StrongAttack)
            or OuterClusterFlag == 1
        )
        
        FiveFlowFlag = (
            FlowOuter
            and (MidAttack or StrongAttack)   # ←追加（これが本質）
            and Foot[4] >= 0.50            # ←少し上げる
            and CPI[4] >= 0.48             # ←ANDにする
            and Start[4] >= Start[2] - 0.02
        )
        
        SixFlowFlag = (
            FlowOuter
            and (MidAttack or StrongAttack)
            and Foot[5] >= 0.52
            and CPI[5] >= 0.50
            and Start[5] >= Start[3] - 0.02
        )    
        

        # ===============================
        # ★ 6の過剰2着抑制（追加）
        # ===============================
        
        if NoAttackFlag == 1:
            SecondAdj[5] *= 0.85

        # ===============================
        # ★ 2コース展開分岐（最重要）
        # ===============================
        
        if (WeakAttack or MidAttack or StrongAttack) and NoAttackFlag == 0:
        
            # ■まくり → 2は巻き込まれる
            if AttackType == "makuri":
                SecondAdj[1] *= 0.85
        
            # ■まくり差し → 2は残るか微妙
            elif AttackType == "makuri_sashi":
                SecondAdj[1] *= 0.98
        
            # ■差し → 2は主役
            elif AttackType == "sashi":
                SecondAdj[1] *= 1.15
                
        if (WeakAttack or MidAttack or StrongAttack) and NoAttackFlag == 0:

            if AttackType == "makuri":
                ThirdAdj[1] *= 0.90
            
            elif AttackType == "makuri_sashi":
                ThirdAdj[1] *= 1.00
            
            elif AttackType == "sashi":
                ThirdAdj[1] *= 1.10
            
        # ===============================
        # ★ F持ち最終補正（完全版）
        # ===============================
        for i in range(6):
        
            if Fcount[i] >= 1:

                if Fcount[i] == 1:
            
                    if CLS[i] == "A1":
                        factor = 0.97
                    elif CLS[i] == "A2":
                        factor = 0.95
                    elif CLS[i] == "B1":
                        factor = 0.93
                    else:
                        factor = 0.90
            
                elif Fcount[i] >= 2:
            
                    if CLS[i] == "A1":
                        factor = 0.92
                    elif CLS[i] == "A2":
                        factor = 0.88
                    elif CLS[i] == "B1":
                        factor = 0.85
                    else:
                        factor = 0.80
            
                # 差し役は少しだけ追加ペナ
                if i in [1,2]:
                    factor *= 0.97
            
                SecondAdj[i] *= factor


        # ===== 6の2着残り強化 =====

        SixSecondFlag = 0

        if (
            CPI[5] >= 0.50
            and Foot[5] >= 0.55
            and (
                (MidAttack or StrongAttack)
                or OuterClusterFlag == 1
            )
        ):
            SixSecondFlag = 1

            # 1〜3を少し削る（前残り崩れ）
            SecondAdj[0] *= 0.92
            SecondAdj[1] *= 0.95
            SecondAdj[2] *= 0.97

        else:

            # 弱い6はしっかり消す
            if Foot[5] < 0.45:
                SecondAdj[5] *= 0.90
            else:
                SecondAdj[5] *= 1.00
                
      
                
        # ===============================
        # ★ 外の選別ロジック（完成版）
        # ===============================
        for i in range(4,6):
        
            strong_outer = (
                CPI[i] >= 0.50
                or (Foot[i] >= 0.52 and Turn[i] >= 0.50)
            )
        
            good_start = (
                Start[i] >= Start[3] - 0.02
            )
        
            flow_race = (
                (MidAttack or StrongAttack)
            )
        
            # ■来る理由がない外は消す
            if not strong_outer and not good_start:
                SecondAdj[i] *= 0.75
                ThirdAdj[i]  *= 0.80
        
            # ■スタートだけの外（よくある事故原因）
            elif good_start and not strong_outer:
                SecondAdj[i] *= 0.85
        
            # ■展開あるけど弱い外（軽く削る）
            elif flow_race and not strong_outer:
                SecondAdj[i] *= 0.90
        
            # ■ちゃんと強い外（ここは残す）
            elif strong_outer and flow_race:
                SecondAdj[i] *= 1.05
                ThirdAdj[i]  *= 1.08
                

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
                Start[i] < min(Start) + 0.01
                and CPI[i] >= 0.42
            ):
                ThirdAdj[i] *= 1.15
        
        for i in range(4,6):
        
            if Foot[i] >= 0.48:
                ThirdAdj[i] *= 1.05
        
        for i in range(6):

            # ===============================
            # ★ 3の自然残り（完成版）
            # ===============================
            if (
                i == 2
                and (
                    # ■ 強い3（従来）
                    CPI[i] >= 0.45
            
                    # ■ 弱いけど残る3（今回の本質）
                    or (
                        0.06 <= DoubleAttackScore <= 0.12
                        and (max(Start) - min(Start)) < 0.08
                        and CPI[i] >= 0.25
                        and Start[i] >= Start[3] - 0.10
                    )
                )
            ):
                ThirdAdj[i] *= 1.18
      
        
    
        # ===============================
        # ★ インの2着・3着粘り復活
        # ===============================
        
        if (
            CLS[0] in ["A1","A2"]
            and Start[0] >= 0.13
        ):
            SecondAdj[0] *= 1.12
            ThirdAdj[0] *= 1.08
        
        
        # ===============================
        # ★ 3と4が完全に競ってる時だけ
        # ===============================
        if (
            DoubleAttackScore > 0.04
            and DoubleAttackScore < 0.09
            and abs(CPI[2] - CPI[3]) < 0.03
        ):
            ThirdAdj[2] *= 0.95
        
        # ===============================
        # ★ 1の過剰残り抑制（ここ）
        # ===============================
        if (
            (MidAttack or StrongAttack)
            and Start[0] < Start[2] - 0.02
        ):
            ThirdAdj[0] *= 0.90
        
        # ===============================
        # ★ 2の残り復活（ここに入れる）
        # ===============================
        if (
            Start[1] >= Start[0] - 0.02
            and CPI[1] >= 0.45
        ):
            SecondAdj[1] *= 1.12
            ThirdAdj[1] *= 1.08
        
                
        # ===============================
        # ★ 展開6（性能じゃない6）
        # ===============================
        # スタート主導外流入
        if (
            DoubleAttackScore > 0.13
            and NoAttackFlag == 0
            and Start[5] >= Start[3] - 0.02
            and (
                (CLS[5] in ["A1","A2"])   # ←従来
                or (Foot[5] >= 0.52 and CPI[5] >= 0.50)  # ←代替
            )
        ):
            ThirdAdj[5] *= 1.25
        
        # ===============================
        # ★ 3着強化
        # ===============================
        
        if (MidAttack or StrongAttack) and NoAttackFlag == 0:
            ThirdAdj[4] *= 1.15
        
        if SixFlowFlag:
            ThirdAdj[5] *= 1.20

        # ===== 3号艇の自然流入 =====

        if 0.43 <= CPI[2] <= 0.62:
            ThirdAdj[2] *= 1.12
            
        # ===============================
        # ★ 非頭艇の残り補正（最重要）
        # ===============================
        
        BaseSecond = SecondAdj.copy()
        BaseThird  = ThirdAdj.copy()
            
        for a in range(6):
            
            SecondAdj = BaseSecond.copy()
            ThirdAdj  = BaseThird.copy()

            if Active[a] == 0:
                continue
        
            P_first = P1[a]
            
            attack_center = max(range(1,6), key=lambda x: AttackIndex[x])

            InsideResist = (
                InsideSurvival[0]
                - 0.6 * DoubleAttackScore
                - 0.6 * max(0, Start[attack_center] - Start[0])
            )
        
            ThirdScoreBase = ThirdScore.copy()
            
            # ===============================
            # ★ 攻め成立判定
            # ===============================
            attack_success = False
            
            for atk in main_attackers:
                if atk == a:
                    if (
                        Start[atk] >= Start[atk-1] - 0.03
                        or Turn[atk] >= Turn[atk-1]
                    ):
                        attack_success = True
                        
           # ===============================
            # ★ 展開拾い強化（汎用版）
            # ===============================
            if attack_success:
            
                for i in range(a+1,6):
            
                    if (
                        (Turn[i] >= Turn[a] - 0.04 and Foot[i] >= 0.48)
                        or (Foot[i] >= Foot[a] - 0.04 and Turn[i] >= 0.48)
                    ):
                        SecondAdj[i] *= 1.10
                        ThirdAdj[i] *= 1.18
                        
            # ===============================
            # ★ 展開3着強化（汎用版）
            # ===============================
            if attack_success and (WeakAttack or MidAttack or StrongAttack):
            
                for i in range(2,5):
            
                    if (
                        Turn[i] >= 0.48
                        and Start[i] >= Start[a] - 0.04
                    ):
                        ThirdAdj[i] *= 1.08
            
            # ===============================
            # ★ 攻め連動
            # ===============================
            if attack_success:

                for i in range(a):
            
                    # ★ インだけは例外（これが本質）
                    if i == 0 and (
                        0.06 < DoubleAttackScore < 0.16
                        and InsideSurvival[0] >= 0.45
                    ):
                        continue
            
                    SecondAdj[i] *= 0.80
            
                # 攻め艇は少し残る
                SecondAdj[a] *= 1.05
            
                # 後ろが展開拾う
                for i in range(a+1,6):
                    SecondAdj[i] *= 1.12
                    ThirdAdj[i] *= 1.15
            
            # ===============================
            # ★ 1だけ飛ぶパターン
            # ===============================
            if attack_success:
                if (
                    Start[0] >= Start[a] - 0.01
                    and Turn[0] < Turn[a]
                ):
                    SecondAdj[0] *= 0.65
                    ThirdAdj[0] *= 0.60
            
                    SecondAdj[1] *= 1.15
                    ThirdAdj[1] *= 1.08
            
            
            
                    
            # ===============================
            # ★ イン中間残り（精度用）
            # ===============================
            if (
                FinalFirst[0] < max(FinalFirst) * 0.95   # 頭は弱い
                and FirstScore[0] > max(FirstScore) * 0.75  # でも弱すぎない
                and InsideSurvival[0] >= 0.50
            ):
                SecondAdj[0] *= 1.12
                ThirdAdj[0] *= 1.08
                    
            
        
                        
                        
            # ===============================
            # ★ 攻め共倒れ検知（汎用・最終版）
            # ===============================
            
            if len(main_attackers) >= 2:
                main = main_attackers[0]
                sub  = main_attackers[1]
            
                if (
                    (MidAttack or StrongAttack)
                    and AttackIndex[main] > 0.45
                    and AttackIndex[sub] > 0.45
                ):
            
                    # 攻め役を少し削る
                    SecondAdj[main] *= 0.96
                    SecondAdj[sub]  *= 0.96
                
                    ThirdAdj[main] *= 0.95
                    ThirdAdj[sub]  *= 0.95
                
                    # その他を底上げ（差し・待ち）
                    for i in range(6):
                        if i not in [main, sub]:
                            ThirdAdj[i] *= 1.10
                
                    # 攻めが近いときはさらに崩れやすい
                    if abs(main - sub) <= 2:
                        for i in range(6):
                            if i not in [main, sub]:
                                ThirdAdj[i] *= 1.05
                        
            # ★ ズレ決着の許容（万舟用）
            if (MidAttack or StrongAttack) and NoAttackFlag == 0:
                for i in range(6):
                    if i >= 2:
                        ThirdAdj[i] *= 1.05
                        
        
            
            # ===============================
            # ★ 弱頭でも残り計算させる（最重要）
            # ===============================
            if (
                P1[a] < 0.15
                and (MidAttack or StrongAttack)
            ):
                P_first *= 1.10
            
            # ===============================
            # ★ 頭弱い艇の残り救済（最重要）
            # ===============================
            if NoAttackFlag == 1:
                
                # イン残り
                SecondAdj[0] *= 1.10
                ThirdAdj[0] *= 1.08
            
                # 3の残り（ちゃんと効かせる）
                SecondAdj[2] *= 1.10
                ThirdAdj[2] *= 1.10
            
                # 攻め役だけ少し削る（軽く）
                SecondAdj[3] *= 0.95        

            
            # ===============================
            # ★ 3頭時の2過剰抑制
            # ===============================
            if a == 2:  # 3号艇が1着
                if Turn[2] > Turn[1]:
                    SecondAdj[1] *= 0.92
            
            # 残り5艇（ここ追加）
            remain1 = [i for i in range(6) if i != a and Active[i] == 1]
    
            for i in range(6):

                # ★ 2号艇の遅れ残り（最小補正）
                if (
                    i == 1
                    and Start[1] == min(Start)
                    and CPI[1] >= 0.42
                ):
                    ThirdAdj[1] *= 1.08

                dist = i - a
            
                if dist < 0:
                    SecondAdj[i] *= (1 - 0.04*DoubleAttackScore)                  
                    ThirdAdj[i] *= (1 - 0.06*DoubleAttackScore)
            
                elif dist == 1:
                    SecondAdj[i] *= 1.12
                    ThirdAdj[i] *= 1.08
            
                elif dist >= 2:
                    SecondAdj[i] *= 1.03
                    ThirdAdj[i] *= 1.00
                    
            # ===============================
            # ★ 壁崩壊（最終完成版）
            # ===============================
            for i in range(1,4):
                collapse = False 
                st_gap = Start[i] - Start[i-1]
            
                # ノイズ除去
                if abs(st_gap) < 0.01:
                    continue
            
                # ===============================
                # ■ 強崩壊（レース壊す）
                # ===============================
                if (
                    (st_gap < -0.04 and (MidAttack or StrongAttack))
                    or (st_gap < -0.03 and Start[i] < Start[i-1] - 0.02)
                ):
                
                    # 頭も崩す → 2着3着へ移動
                    SecondAdj[i] *= 0.75
                    ThirdAdj[i]  *= 0.80
                
                    # 本体削る
                    SecondAdj[i] *= 0.70
                    ThirdAdj[i]  *= 0.75
                
                    # 外に強く流す
                    for j in range(i+1,6):
                        SecondAdj[j] *= 1.25
                        ThirdAdj[j]  *= 1.20
                
                    # 内も少し崩す
                    for j in range(0,i):
                        SecondAdj[j] *= 0.95
                        ThirdAdj[j]  *= 0.97
                
                    continue
            
                # ===============================
                # ■ 弱崩壊（ズレるだけ）
                # ===============================
                elif st_gap < -0.02:
            
                    SecondAdj[i] *= 0.80
                    ThirdAdj[i]  *= 0.85
            
                    for j in range(i+1,6):
                        SecondAdj[j] *= 1.08
                        ThirdAdj[j]  *= 1.05
            
                    for j in range(0,i):
                        SecondAdj[j] *= 0.98
                        ThirdAdj[j]  *= 0.99
            
                is_attacker = (st_gap < -0.02)

                if is_attacker and i >= 2 and (WeakAttack or MidAttack or StrongAttack):
                
                    if Start[0] < Start[i] - 0.02:
                        SecondAdj[0] *= 0.65
                        ThirdAdj[0]  *= 0.60
                    else:
                        SecondAdj[0] *= 0.75
            
                # ===============================
                # ★ 差し込み勝ち（ここに入れる）
                # ===============================
                is_attacker = (st_gap < -0.02)

                candidates = []
                
                if is_attacker:
                
                    for j in range(i):
                
                        if (
                            Start[j] >= Start[i] - 0.03
                            and Turn[j] >= 0.50
                        ):
                            candidates.append(j)
            
                if len(candidates) > 0:
            
                    best = max(
                        candidates,
                        key=lambda x: (
                            0.40 * Turn[x]
                            + 0.30 * Start[x]
                            + 0.20 * max(0, Start[x] - Start[i])
                            + 0.10 * Foot[x]
                        )
                    )
            
                    SecondAdj[best] *= 1.18
                    ThirdAdj[best]  *= 1.12
                        
                        

                if i >= 4:

                    if i == 5:
                        if not (Strong6 or Normal6):

                            # ★ 展開6は殺さない
                            if not (
                                (MidAttack or StrongAttack)
                                and Start[i] >= Start[3] - 0.02
                            ):
                                if not (
                                    i == 5
                                    and (MidAttack or StrongAttack)
                                    and Start[i] >= Start[3] - 0.02
                                ):
                                    if Foot[i] < 0.50:
                                        ThirdAdj[i] *= 0.95
                    else:
                        if Foot[i] < 0.55:
                            SecondAdj[i] *= 0.90
                            
                    # ===== 外の残り再設計 =====
                    if i == 4:
                        if (
                            (MidAttack or StrongAttack)
                            and Start[i] >= Start[2] - 0.02
                            and Foot[i] >= 0.50
                            and CPI[i] >= 0.48
                        ):
                            SecondAdj[i] *= 1.08
                            ThirdAdj[i] *= 1.04

                    # ★ 6だけは条件付きにする
                    if i == 5:
                    
                        if not (
                            (MidAttack or StrongAttack)
                            and Start[5] >= Start[3] - 0.02
                        ):
                            SecondAdj[5] *= 0.85
                            ThirdAdj[5] *= 0.85
            
                # ===============================
                # 内残り（条件付きに変更）
                # ===============================
                if i <= 2 and InsideSurvival[i] > 0.55:
                    ThirdAdj[i] *= 1.03
            
                # インのしぶとさ（少し弱め）
                if i == 0:
                    ThirdAdj[i] *= 1.02
            
                # ===============================
                # 3着バランス補正（シンプル版）
                # ===============================

                # 基本位置
                if i == 2:   # 3号艇
                    ThirdAdj[i] *= 1.10
                
                elif i == 3: # 4号艇
                    ThirdAdj[i] *= 1.08
                
                elif i == 4:
                
                    if (MidAttack or StrongAttack) and NoAttackFlag == 0:
                        ThirdAdj[i] *= 1.05
                    else:
                        ThirdAdj[i] *= 0.98
                        
                elif i == 5: # 6号艇

                    if Foot[i] < 0.50:
                        ThirdAdj[i] *= 0.90   # 弱いときだけ削る
                
                    else:
                        ThirdAdj[i] *= 1.00   # 基本はあまり削らない

                # 展開ある時だけ6を少し戻す
                if i == 5 and (MidAttack or StrongAttack):
                    ThirdAdj[i] *= 1.10

                # 弱すぎる艇だけ削る
                if Skill[i] < 0.30:
                    ThirdAdj[i] *= 0.90  
                    
            # ===============================
            # ★ 4頭時の6流入（ここに入れる）
            # ===============================
            
                
            if (
                a == 3
                and Strong6
            ):
                SecondAdj[5] *= 1.10
                
            # ===============================
            # ★ 1の2着・3着残り補正（改良版）
            # ===============================
            weak_head = FirstScore[0] < max(FirstScore) * 0.92
            
            has_resist = InsideResist >= 0.48
            
            weak_sashi = (
                Start[1] < Start[0] - 0.02
                or Turn[1] < Turn[2]
            )
            
            if weak_head and has_resist:
            
                if weak_sashi:
                    SecondAdj[0] *= 1.15
                    ThirdAdj[0] *= 1.10
            
                else:
                    SecondAdj[0] *= 1.08
                    ThirdAdj[0] *= 1.05
                        
            if (
                0.85 <= FirstScore[0] / max(FirstScore) <= 0.98
                and InsideResist >= 0.45
            ):
                SecondAdj[0] *= 1.10
                ThirdAdj[0] *= 1.05
                
            # ===============================
            # ★ 弱い6は2着に来させない（ここに入れる）
            # ===============================
            if not (
                CLS[5] in ["A1","A2"]
                or (CPI[5] >= 0.50 and Foot[5] >= 0.52)
            ):
                SecondAdj[5] *= 0.80
                
            # ===============================
            # ★ 6の最終制御（統一版）
            # ===============================
            
            six_flow = (
                (MidAttack or StrongAttack)
                and Start[5] >= Start[3] - 0.02
            )
            
            six_power = (
                Foot[5] >= 0.50
                or CPI[5] >= 0.48
            )
            
            if (
                six_flow
                and six_power
                and DoubleAttackScore > 0.13
                and NoAttackFlag == 0
            ):
                SecondAdj[5] *= 1.08
                ThirdAdj[5] *= 1.12
            else:
                SecondAdj[5] *= 0.82
                ThirdAdj[5] *= 0.85
                
            # ===============================
            # ★ 6の2着 最終制御（完全固定）
            # ===============================
            weak6 = not (
                CLS[5] in ["A1","A2"]
                or (CPI[5] >= 0.52 and Foot[5] >= 0.53)
            )
            
            if weak6:
            
                if DoubleAttackScore < 0.10:
                    SecondAdj[5] = 0.40   # ←乗算じゃなく代入
                else:
                    SecondAdj[5] = 0.65
                
            
                
                    

            second_scores = [
                SecondAdj[i] if Active[i]==1 else 0
                for i in remain1
            ]
            total2=sum(second_scores)

            if total2<=0:
                total2=1e-6

            second_probs=[s/total2 for s in second_scores]

            for idx_b,b in enumerate(remain1):
                if Active[b] == 0:
                    continue

                P_second = second_probs[idx_b]

                remain2=[i for i in remain1 if i!=b and Active[i]==1]

                third_scores = [
                ThirdAdj[i] if Active[i]==1 else 0
                for i in remain2
                ]
                total3=sum(third_scores)

                if total3<=0:
                    total3=1e-6

                third_probs=[s/total3 for s in third_scores]

                for idx_c,c in enumerate(remain2):

                    if Active[c] == 0:
                        continue

                    P_third = third_probs[idx_c]

                    p = P_first * P_second * P_third
                    
                    # ★ 最終フィルター（絶対防御）
                    if (
                        Active[a] == 0
                        or Active[b] == 0
                        or Active[c] == 0
                    ):
                        continue
                        
                    if (
                        boats[a] <= 0
                        or boats[b] <= 0
                        or boats[c] <= 0
                    ):
                        continue
                    
                    results.append((boats[a],boats[b],boats[c],p))

        return results, ChaosScore, P1, DoubleAttackScore, InsideSurvival, debug_log, StrongAttack, MidAttack
    # =====================================
    # 進入パターン
    # =====================================

    order_waku=[0,1,2,3,4,5]

    order_ex=[x-1 for x in ExEntry if x>0]

    if len(order_ex)!=6:
        order_ex=[0,1,2,3,4,5]

    try:
        res_waku, chaos1, P1_waku, DAS1, IS1, debug_log, StrongAttack_waku, MidAttack_waku = run_ai(order_waku)

        res_ex, chaos2, P1_ex, DAS2, IS2, debug_log, StrongAttack_ex, MidAttack_ex = run_ai(order_ex)
    
    except Exception as e:
        import traceback
        st.write("ERROR:", e)
        st.code(traceback.format_exc())
        st.stop()

        res_ex, chaos2, P1_ex, DAS2, IS2, debug_log = run_ai(order_ex) 

    ChaosScore = 0.3 * chaos1 + 0.7 * chaos2
    P1 = P1_ex
    DoubleAttackScore = DAS2
    InsideSurvival = IS2
    # =====================================
    # 合成
    # =====================================

    final={}

    for a,b,c,p in res_waku:

        key=(a,b,c)

        final[key]=final.get(key,0)+0.3*p

    for a,b,c,p in res_ex:

        key=(a,b,c)

        final[key]=final.get(key,0)+0.7*p

    results=[(k[0],k[1],k[2],v) for k,v in final.items()]
    
    # ===============================
    # ★ シャープ化 & 正規化 & カット
    # ===============================
    
    # ① シャープ化
    power = 1.45 + 0.35 * ChaosScore
    
    results = [
        (a,b,c, p**power)
        for (a,b,c,p) in results
    ]
    
    # ② 正規化
    total = sum(r[3] for r in results)
    
    if total > 0:
        results = [
            (a,b,c, p/total)
            for (a,b,c,p) in results
        ]
    
    filtered = []

    for r in results:
    
        p = r[3]
    
        # 中穴ゾーン保護
        if 0.01 <= p <= 0.03:
            filtered.append(r)
    
        # 通常カット条件
        elif p >= 0.004:
            filtered.append(r)
    
    results = filtered

    results.sort(key=lambda x:x[3],reverse=True)

    # ===============================
    # 予想信頼度
    # ===============================

    if len(results) >= 2:
        TopGap = results[0][3] - results[1][3]
    else:
        TopGap = 0
        
    # ===============================
    # ★ レース難易度判定
    # ===============================
    
    top_p1 = max(P1)
    top_gap = TopGap
    
    if top_p1 >= 0.38 and top_gap >= 0.08 and ChaosScore < 0.55:
        RaceLevel = "solid"
    
    elif top_p1 >= 0.25 and ChaosScore < 0.70:
        RaceLevel = "middle"
    
    else:
        RaceLevel = "chaos"
    
    # 攻め強すぎは強制的に荒れ
    if DoubleAttackScore > 0.12 and top_p1 < 0.30:
        RaceLevel = "chaos"


    # =====================================
    # OUTPUT
    # =====================================

    Coverage = 0
    Final = []
    
    target = 0.72 + 0.10 * ChaosScore
    max_bets = int(10 + 16 * ChaosScore)
    
    for r in results:
    
        Coverage += r[3]
        Final.append(r)
    
        # カバレッジ条件
        if Coverage >= target:
            break
    
        # ★ 点数制限（最重要）
        if len(Final) >= max_bets:
            break

    unique = {}

    for a,b,c,p in Final:
        key = (a,b,c)
        unique[key] = unique.get(key, 0) + p   # ←これに変更
    
    Final = [(k[0],k[1],k[2],v) for k,v in unique.items()]
    
    Final.sort(key=lambda x: x[3], reverse=True)
                    
    # ===============================
    # ★ マーク付け（完成形）
    # ===============================
    
    sorted_final = sorted(Final, key=lambda x: x[3], reverse=True)

    top_head = P1.index(max(P1))
    
    marked = []
    
    for i, (a,b,c,p) in enumerate(sorted_final):
    
        head = a-1
    
        # ◎は1点固定
        if i == 0:
            mark = "◎"
    
        # ○は上位3点
        elif i <= 2:
            mark = "○"
    
        # ▲は攻め条件＋上位6まで
        elif i <= 5 and (MidAttack_ex or StrongAttack_ex) and head >= 2:
            mark = "▲"
    
        else:
            mark = ""
    
        marked.append((mark,a,b,c,p))
    
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
        
    debug_text.append(f"DAS_waku: {round(DAS1,4)}")
    debug_text.append(f"DAS_ex: {round(DAS2,4)}")
    debug_text.append(f"ChaosScore: {round(ChaosScore,4)}")
        
    debug_text.append("")
    debug_text.append("P1:")
    for i,p in enumerate(P1):
        debug_text.append(f"{i+1}: {round(p,4)}")
        
    debug_text.append("")
    debug_text.append("P1順位:")
    debug_text.append(str(sorted(range(6), key=lambda i: P1[i], reverse=True)))
        
    debug_text.append("")
    debug_text.append("---- run_ai debug ----")
    for name, val in debug_log:
        debug_text.append(f"{name}: {val}")
        
    debug_output = "\n".join(debug_text)
    
        # 出目テキスト
    result_text = "\n".join([
        f"{a}-{b}-{c} ({round(p,4)}) {mark}" if mark != "" else f"{a}-{b}-{c} ({round(p,4)})"
        for (mark,a,b,c,p) in marked
    ])
    
    st.markdown("### ▼ 買い目")
    
    st.write(f"レース判定：{RaceLevel}")

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
    
        
        

  
