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
        
mode = st.selectbox("モード", ["auto","ana","safe"])


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
        if WinRate[i]==0 and PlaceRate[i]==0:
            Active[i]=0

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

    ExhibitionF=[0,0,0,0,0,0]

    # =====================================
    # AI CORE
    # =====================================

    def run_ai(order, mode):

        FC=[Fcount[i] for i in order]
        
        CLS=[Class[i] for i in order]
        
        boats = [
            Boat[i] if Active[i]==1 else -1
            for i in order
        ]

        WR=[WinRate[i] for i in order]
        PR=[PlaceRate[i] for i in order]

        ST=[AvgST[i] for i in order]

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

        OuterCluster = max(CPI[3:6]) - min(CPI[3:6])
        OuterClusterFlag = 1 if OuterCluster <= 0.06 else 0


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
                or (Start[2] > Start[1] + 0.04)
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
        if DoubleAttackScore > 0.08:
            race_score += 1
        
        # 判定
        if race_score >= 2:
            mode_auto = "ana"
        else:
            mode_auto = "safe"
        
        # 最終モード決定
        if mode == "auto":
            use_mode = mode_auto
        else:
            use_mode = mode

        
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

        LaneWin=[

        0.58*DynamicInsideFactor*(1-0.25*ChaosScore),
        0.19+(0.45*(1-DynamicInsideFactor)*0.40)*(1+0.20*ChaosScore),
        0.16+(0.45*(1-DynamicInsideFactor)*0.30)*(1+0.25*ChaosScore),
        0.14+(0.45*(1-DynamicInsideFactor)*0.20)*(1+0.30*ChaosScore),
        0.07+(0.45*(1-DynamicInsideFactor)*0.07)*(1+0.35*ChaosScore),
        0.04+(0.45*(1-DynamicInsideFactor)*0.03)*(1+0.40*ChaosScore)

        ]

        FirstScore=[
        0.35*Start[i]+
        0.25*Skill[i]+
        0.15*Engine[i]+
        0.10*Foot[i]+
        0.15*LaneWin[i]
        for i in range(6)
        ]

        # ===============================
        # ST遅い艇の頭抑制（追加）
        # ===============================
        AvgStart = sum(Start)/6

        for i in range(6):
            if Start[i] < AvgStart - 0.03:
                FirstScore[i] *= 0.80

        # 外の1着抑制（重要）
        for i in range(6):

            if i >= 4:
        
                # インより遅いなら強く削る
                if Start[i] < Start[0]:
                    FirstScore[i] *= 0.75
        
                # 同等なら軽く削る
                else:
                    FirstScore[i] *= 0.90
        
        if use_mode == "safe":
            FirstScore[0] *= 1.08
                
            for i in range(6):

                # 弱いイン削る
                if i == 0 and Skill[i] < 0.45:
                    FirstScore[i] *= 0.75
                        
                # ===============================
                # 外の頭条件化（修正）
                # ===============================
                if i >= 4:
                    if AttackIndex[i] < max(AttackIndex):
                        FirstScore[i] *= 0.70

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

        TotalFirst = sum([FirstScore[i] for i in range(6) if Active[i]==1])

        if TotalFirst <= 0:
            TotalFirst = 1e-6
        
        P1 = [
        (FirstScore[i]/TotalFirst) if Active[i]==1 else 0
        for i in range(6)
        ]

        # ===============================
        # トップ集中ブースト
        # ===============================
        top = max(P1)

        for i in range(6):
            if P1[i] == top:        
                P1[i] *= 1.15

        LaneBonus=[0.10,0.09,0.08,0.07,0.06,0.05]

        SecondScore=[
        0.33*Turn[i]+
        0.27*Foot[i]+
        0.20*Engine[i]+
        0.10*Velocity[i]+
        0.15*LaneBonus[i]
        
        for i in range(6)
        ]

        ThirdScore=[
        0.28*Velocity[i]+
        0.28*Foot[i]+
        0.20*Engine[i]+
        0.14*LaneBonus[i]+
        0.10*InsideSurvival[i]
        for i in range(6)
        ]

        # 弱い外は3着削る
        for i in range(6):
            if i >= 4 and Engine[i] < 0.50:
                ThirdScore[i] *= 0.80

        results=[]

        for a in range(6):

            if Active[a] == 0:
                continue

            P_first = P1[a]

            SecondAdj = SecondScore.copy()
            ThirdAdj = ThirdScore.copy()

            # 残り5艇（ここ追加）
            remain1 = [i for i in range(6) if i != a and Active[i] == 1]
    
            for i in range(6):

                dist = i - a
            
                if dist < 0:
                    SecondAdj[i] *= (1 - 0.04*DoubleAttackScore)                  
                    ThirdAdj[i] *= (1 - 0.06*DoubleAttackScore)
            
                elif dist == 1:
                    SecondAdj[i] *= 1.12
                    ThirdAdj[i] *= 1.08
            
                elif dist >= 2:
                    SecondAdj[i] *= 1.03
                    ThirdAdj[i] *= 0.95

                # ===============================
                # 弱い外の2着削り（ここ追加）
                # ===============================
                if i >= 4:
                    if Foot[i] < 0.55:
                        SecondAdj[i] *= 0.88

                # 6号艇はさらに厳しく
                if i == 5:
                    if Foot[i] < 0.60:
                        SecondAdj[i] *= 0.80
            
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
                elif i == 4: # 5号艇
                    ThirdAdj[i] *= 0.97
                elif i == 5: # 6号艇
                    if Foot[i] < 0.60:
                        ThirdAdj[i] *= 0.75
                    else:
                        ThirdAdj[i] *= 0.90  # 普通は沈める

                # 展開ある時だけ6を少し戻す
                if i == 5 and DoubleAttackScore > 0.08:
                    ThirdAdj[i] *= 1.05

                # 弱すぎる艇だけ削る
                if Skill[i] < 0.30:
                    ThirdAdj[i] *= 0.90  
                    

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

                    if boats[a] != -1 and boats[b] != -1 and boats[c] != -1:
                        results.append((boats[a],boats[b],boats[c],p))

        return results

    # =====================================
    # 進入パターン
    # =====================================

    order_waku=[0,1,2,3,4,5]

    order_ex=[x-1 for x in ExEntry if x>0]

    if len(order_ex)!=6:
        order_ex=[0,1,2,3,4,5]

    res_waku=run_ai(order_waku, mode)
    res_ex=run_ai(order_ex, mode)

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

    results.sort(key=lambda x:x[3],reverse=True)

    # ===============================
    # 予想信頼度
    # ===============================

    if len(results) >= 2:
        TopGap = results[0][3] - results[1][3]
    else:
        TopGap = 0


    # =====================================
    # OUTPUT
    # =====================================

    Coverage=0
    Final=[]

    for r in results:

        Coverage+=r[3]

        Final.append(r)

        if Coverage>=0.90:
            break

        if len(Final)>=20:
            break

    st.write("Coverage:",Coverage)
    for i,r in enumerate(Final,1):

        st.write(i,r)
