import numpy as np
from itertools import permutations

# =========================
# utility
# =========================

def normalize(x):
    x = np.array(x,dtype=float)
    return (x - np.min(x))/(np.max(x)-np.min(x)+0.01)

def clamp(x,a,b):
    return max(a,min(b,x))

def pos(x):
    return max(0,x)


# =========================
# PERFORMANCE ENGINE
# =========================

def performance_engine(data):

    WinRate=np.array(data["WinRate"])
    PlaceRate=np.array(data["PlaceRate"])
    AvgST=np.array(data["AvgST"])

    Motor2=np.array(data["Motor2"])
    Boat2=np.array(data["Boat2"])

    ExTime=np.array(data["ExTime"])
    ExST=np.array(data["ExST"])

    TurnTime=np.array(data["TurnTime"])
    LapTime=np.array(data["LapTime"])
    StraightTime=np.array(data["StraightTime"])

    Class=data["Class"]

    WinRateScore=normalize(WinRate)
    PlaceRateScore=normalize(PlaceRate)

    SkillRaw=0.55*WinRateScore+0.45*PlaceRateScore
    Skill=normalize(SkillRaw)

    MotorScore=normalize(Motor2)
    BoatScore=normalize(Boat2)

    EngineRaw=0.65*MotorScore+0.35*BoatScore
    Engine=normalize(EngineRaw)

    AvgExTime=np.mean(ExTime)

    TimeDiff=AvgExTime-ExTime
    TimeScore=normalize(TimeDiff)

    ExSTScore=normalize(0.30-ExST)

    Exhibit=0.80*TimeScore+0.20*ExSTScore

    AvgTurn=np.mean(TurnTime)
    AvgLap=np.mean(LapTime)
    AvgStraight=np.mean(StraightTime)

    TurnDiff=AvgTurn-TurnTime
    LapDiff=AvgLap-LapTime
    StraightDiff=AvgStraight-StraightTime

    TurnScore=normalize(TurnDiff)
    LapScore=normalize(LapDiff)
    StraightScore=normalize(StraightDiff)

    RawFoot=(
        0.40*TurnScore+
        0.25*LapScore+
        0.25*StraightScore+
        0.10*Exhibit
    )

    Foot=normalize(RawFoot)

    BaseStart=np.array([clamp((0.20-x)/0.10,0,1) for x in AvgST])
    ExhibitStart=np.array([clamp((0.20-x)/0.10,0,1) for x in ExST])

    Start=0.65*BaseStart+0.35*ExhibitStart

    TurnRaw=0.30*Skill+0.55*Foot+0.15*Engine
    Turn=normalize(TurnRaw)

    VelocityRaw=0.50*Foot+0.35*Engine+0.15*Start
    Velocity=normalize(VelocityRaw)

    InsideSurvival_1=(
        0.40*Skill[0]+
        0.30*Engine[0]+
        0.20*Start[0]+
        0.10*Foot[0]
    )

    boats=[]

    for i in range(6):
        boats.append({
            "lane":i+1,
            "Skill":Skill[i],
            "Engine":Engine[i],
            "Foot":Foot[i],
            "Start":Start[i],
            "Turn":Turn[i],
            "Velocity":Velocity[i],
            "Class":Class[i]
        })

    return boats,InsideSurvival_1


# =========================
# MANSHU HUNTER VER23
# =========================

def manshu_hunter(boats,InsideSurvival_1):

    Skill=np.array([b["Skill"] for b in boats])
    Engine=np.array([b["Engine"] for b in boats])
    Foot=np.array([b["Foot"] for b in boats])
    Start=np.array([b["Start"] for b in boats])
    Turn=np.array([b["Turn"] for b in boats])
    Velocity=np.array([b["Velocity"] for b in boats])

    # =================
    # CPI
    # =================

    CPI=[]

    for i in range(6):

        lane=i+1

        if lane==4:
            StartWeight=0.17
        elif lane==5:
            StartWeight=0.10
        elif lane==6:
            StartWeight=0.08
        else:
            StartWeight=0.15

        val=(
            0.30*Skill[i]+
            0.22*Engine[i]+
            0.22*Foot[i]+
            StartWeight*Start[i]+
            0.11*Turn[i]+
            0.07*Velocity[i]
        )

        CPI.append(val)

    CPI=np.array(CPI)

    PerformanceSpread=max(CPI)-min(CPI)

    MidCluster=max(CPI[1],CPI[2],CPI[3])-min(CPI[1],CPI[2],CPI[3])
    MidClusterFlag=1 if MidCluster<=0.05 else 0

    outer=CPI[3:6]
    outer_sorted=np.sort(outer)

    OuterPower=(
        0.5*outer_sorted[-1]+
        0.3*outer_sorted[-2]+
        0.2*np.mean(outer)
    )

    OutsideStackFlag=1 if outer_sorted[-2]>=0.50 else 0

    InsideWeak=1-InsideSurvival_1

    StartSpread=max(Start)-min(Start)

    FastLane=np.argmax(Start)+1
    StartPressureFlag=1 if FastLane in [2,4] else 0

    TopStart=np.argmax(Start)+1
    StartShockFlag=1 if TopStart>=4 else 0

    WallSashiFlag=1 if (
        Turn[2]>=0.80 and
        CPI[2]>=0.52 and
        Engine[1]>=0.70
    ) else 0

    TwoLaneAttackFlag=1 if (
        Start[1]<=Start[0]+0.05 and
        CPI[1]>=0.55
    ) else 0

    ThreeLaneAttackFlag=1 if (
        Start[2]<=0.18 and
        CPI[2]>=0.55 and
        Start[2]<=Start[1]+0.03
    ) else 0

    FourLaneAttackFlag=1 if (
        Start[3]<=Start[1] and
        Start[3]<=Start[2] and
        Start[3]<=0.15 and
        CPI[3]>=0.55
    ) else 0

    TwoLaneAttackScore=(
        0.22*TwoLaneAttackFlag+
        0.28*pos(Start[1]-Start[0])+
        0.22*pos(CPI[1]-CPI[0])+
        0.15*pos(Engine[1]-Engine[0])+
        0.13*pos(Turn[1]-Turn[0])
    )

    ThreeLaneAttackScore=(
        0.22*ThreeLaneAttackFlag+
        0.28*pos(Start[2]-Start[1])+
        0.22*pos(CPI[2]-CPI[0])+
        0.15*pos(Engine[2]-Engine[0])+
        0.13*pos(Turn[2]-Turn[0])
    )

    FourLaneAttackScore=(
        0.22*FourLaneAttackFlag+
        0.28*pos(Start[3]-Start[2])+
        0.22*pos(CPI[3]-CPI[0])+
        0.15*pos(Engine[3]-Engine[0])+
        0.13*pos(Turn[3]-Turn[0])
    )

    DoubleAttackScore=(
        (ThreeLaneAttackScore*FourLaneAttackScore)+
        0.5*(TwoLaneAttackScore*ThreeLaneAttackScore)
    )

    AttackBoost1=1-0.4*max(TwoLaneAttackScore,ThreeLaneAttackScore,FourLaneAttackScore)
    AttackBoost2=1+0.5*TwoLaneAttackScore
    AttackBoost3=1+0.6*ThreeLaneAttackScore
    AttackBoost4=1+0.5*FourLaneAttackScore
    AttackBoost5=1+0.9*DoubleAttackScore
    AttackBoost6=1+0.7*DoubleAttackScore

    LaneBonus=[0.05,0.06,0.05,0.10,0.15,0.18]

    SecondScore=0.40*Turn+0.35*Foot+0.25*Velocity

    ThirdScore=(
        0.35*Velocity+
        0.30*Foot+
        0.20*Engine+
        0.10*np.array(LaneBonus)
    )

    LaneWin=[0.50,0.17,0.15,0.11,0.05,0.02]

    AttackBoost=[AttackBoost1,AttackBoost2,AttackBoost3,AttackBoost4,AttackBoost5,AttackBoost6]

    LaneCPI=CPI*np.array(LaneWin)*np.array(AttackBoost)

    TotalLaneCPI=sum(LaneCPI)
    P1=LaneCPI/TotalLaneCPI

    TotalSecond=sum(SecondScore)
    TotalThird=sum(ThirdScore)

    combos=[]

    for A,B,C in permutations(range(6),3):

        p=(
            P1[A]*
            (SecondScore[B]/(TotalSecond-SecondScore[A]))*
            (ThirdScore[C]/(TotalThird-ThirdScore[A]-ThirdScore[B]))
        )

        combos.append((A+1,B+1,C+1,p))

    combos.sort(key=lambda x:-x[3])

    coverage=0
    bets=[]

    for c in combos:

        coverage+=c[3]
        bets.append(c)

        if coverage>=0.90 or len(bets)>=20:
            break

    return bets
