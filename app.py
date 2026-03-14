import itertools
import copy

# =====================================
# NORMALIZE
# =====================================

def normalize(values):

    mn=min(values)
    mx=max(values)

    if mx-mn<1e-6:
        return [0.5]*len(values)

    return [(v-mn)/(mx-mn) for v in values]


# =====================================
# INPUT
# =====================================

Boat=[1,2,3,4,5,6]

WinRate=[0,0,0,0,0,0]
PlaceRate=[0,0,0,0,0,0]

AvgST=[0,0,0,0,0,0]

Motor2=[0,0,0,0,0,0]
Boat2=[0,0,0,0,0,0]

ExTime=[0,0,0,0,0,0]
ExST=[0,0,0,0,0,0]

TurnTime=[0,0,0,0,0,0]
LapTime=[0,0,0,0,0,0]
StraightTime=[0,0,0,0,0,0]

Class=["A1","A2","B1","B1","B2","A1"]
Fcount=[0,0,0,0,0,0]
ExhibitionF=[0,0,0,0,0,0]

# 展示進入
ExEntry=[1,2,3,4,5,6]


# =====================================
# 欠場処理
# =====================================

ExEntry=[x for x in ExEntry if x!=0]+[0]*(6-len([x for x in ExEntry if x!=0]))


# =====================================
# AI計算関数
# =====================================

def run_ai(order):

    # ----------------------------
    # データ並び替え
    # ----------------------------

    B=[Boat[i] for i in order]

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

    CL=[Class[i] for i in order]
    FC=[Fcount[i] for i in order]
    EF=[ExhibitionF[i] for i in order]

    # ----------------------------
    # SKILL
    # ----------------------------

    WinScore=normalize(WR)
    PlaceScore=normalize(PR)

    SkillRaw=[0.55*WinScore[i]+0.45*PlaceScore[i] for i in range(6)]
    Skill=normalize(SkillRaw)

    # ----------------------------
    # ENGINE
    # ----------------------------

    MotorScore=normalize(M)
    BoatScore=normalize(BO)

    EngineRaw=[0.65*MotorScore[i]+0.35*BoatScore[i] for i in range(6)]
    Engine=normalize(EngineRaw)

    # ----------------------------
    # EXHIBITION
    # ----------------------------

    AvgEx=sum(ET)/6
    TimeScore=normalize([AvgEx-x for x in ET])
    ExSTScore=normalize([0.30-x for x in EST])

    Exhibit=[0.80*TimeScore[i]+0.20*ExSTScore[i] for i in range(6)]

    # ----------------------------
    # FOOT
    # ----------------------------

    AvgTurn=sum(TT)/6
    AvgLap=sum(LT)/6
    AvgStraight=sum(STT)/6

    TurnScore=normalize([AvgTurn-x for x in TT])
    LapScore=normalize([AvgLap-x for x in LT])
    StraightScore=normalize([AvgStraight-x for x in STT])

    RawFoot=[
    0.40*TurnScore[i]+
    0.25*LapScore[i]+
    0.25*StraightScore[i]+
    0.10*Exhibit[i]
    for i in range(6)
    ]

    Foot=normalize(RawFoot)

    # ----------------------------
    # START
    # ----------------------------

    BaseStart=[max(0,min(1,(0.20-ST[i])/0.10)) for i in range(6)]
    ExhibitStart=[max(0,min(0.80,(0.20-EST[i])/0.10)) for i in range(6)]

    StartRaw=[0.75*BaseStart[i]+0.25*ExhibitStart[i] for i in range(6)]

    Start=normalize(StartRaw)

    # ----------------------------
    # TURN
    # ----------------------------

    TurnRaw=[
    0.30*Skill[i]+
    0.55*Foot[i]+
    0.15*Engine[i]
    for i in range(6)
    ]

    Turn=normalize(TurnRaw)

    # ----------------------------
    # VELOCITY
    # ----------------------------

    VelocityRaw=[
    0.50*Foot[i]+
    0.35*Engine[i]+
    0.15*Start[i]
    for i in range(6)
    ]

    Velocity=normalize(VelocityRaw)

    # ----------------------------
    # CPI
    # ----------------------------

    CPI=[
    0.33*Skill[i]+
    0.25*Engine[i]+
    0.27*Foot[i]+
    0.10*Turn[i]+
    0.05*Velocity[i]
    for i in range(6)
    ]

    # ----------------------------
    # STAGE17
    # ----------------------------

    StartSpread=max(Start)-min(Start)

    DynamicInsideFactor=1

    if StartSpread>=0.12:
        DynamicInsideFactor=0.70
    elif StartSpread>=0.08:
        DynamicInsideFactor=0.82

    LaneWin=[

    0.50*DynamicInsideFactor,
    0.17+(0.50*(1-DynamicInsideFactor)*0.40),
    0.15+(0.50*(1-DynamicInsideFactor)*0.30),
    0.11+(0.50*(1-DynamicInsideFactor)*0.20),
    0.05+(0.50*(1-DynamicInsideFactor)*0.07),
    0.02+(0.50*(1-DynamicInsideFactor)*0.03)

    ]

    LaneCPI=[CPI[i]*LaneWin[i] for i in range(6)]

    TotalLane=sum(LaneCPI)

    P1=[x/TotalLane for x in LaneCPI]

    SecondScore=[
    0.35*Turn[i]+
    0.35*Foot[i]+
    0.30*Velocity[i]
    for i in range(6)
    ]

    ThirdScore=[
    0.35*Velocity[i]+
    0.30*Foot[i]+
    0.20*Engine[i]+
    0.15*CPI[i]
    for i in range(6)
    ]

    SecondTotal=sum(SecondScore)
    ThirdTotal=sum(ThirdScore)

    SecondProb=[x/SecondTotal for x in SecondScore]
    ThirdProb=[x/ThirdTotal for x in ThirdScore]

    results=[]

    for A,B,C in itertools.permutations(range(6),3):

        den2=1-SecondProb[A]
        den3=1-ThirdProb[A]-ThirdProb[B]

        if den2<=0: den2=1e-6
        if den3<=0: den3=1e-6

        p=P1[A]*(SecondProb[B]/den2)*(ThirdProb[C]/den3)

        results.append((B[A],B[B],B[C],p))

    return results


# =====================================
# 進入パターン
# =====================================

order_waku=[0,1,2,3,4,5]
order_ex=[x-1 for x in ExEntry if x!=0]

res_waku=run_ai(order_waku)
res_ex=run_ai(order_ex)

# =====================================
# 結合
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


print("Coverage:",Coverage)

for i,r in enumerate(Final,1):

    print(i,r)
