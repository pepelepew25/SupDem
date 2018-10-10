import math
from plot import *
import talib
#from technical_indicators import ATR
#from pandas_talib import ATR

UP_POINT=1
DN_POINT=-1
period=1
ZONE_Sup=1
ZONE_RESIST=2
ZONE_WEAK=0
ZONE_TURNCOAT=1
ZONE_UNTESTED=2
ZONE_VERIFIED=3
ZONE_PROVEN=4
zone_color = {'Sup_weak' : 'DarkSlateGray', 'Sup_untested': 'SeaGreen', 'Sup_verified': 'Green',
             'Sup_proven': 'LimeGreen', 'Sup_turncoat': 'OliveDrab', 'Res_weak': 'Indigo',
             'Res_untested': 'Orchid', 'Res_verified': 'Crimson', 'Res_proven': 'Red',
             'Res_turncoat': 'DarkOrange'}
zone_show = {'weak': True, 'untested': True, 'turncoat': False}

def SupDem(df, ax):
    High = df['High'].values
    Low = df['Low'].values
    Close = df['Close'].values
    Bars = len(df.index)
    BackLimit = 1000
    fractal_fast_factor = 3.0
    fractal_slow_factor = 6.0
    fractals_show = True

    FastUpPts,FastDnPts = Fractals(fractal_fast_factor, High, Low, Bars, BackLimit)
    #print("FastUpPts: {}".format(FastUpPts))
    #print("FastDnPts: {}".format(FastDnPts))
    SlowUpPts, SlowDnPts = Fractals(fractal_slow_factor, High, Low, Bars, BackLimit)
    #print("SlowUpPts: {}".format(SlowUpPts))
    #print("SlowDnPts: {}".format(SlowDnPts))

    df = df.reset_index()
    #df = ATR(df, 8)
    print(df)

    # plot fractal pts to debug
    if fractals_show:
        for pts in (FastUpPts, FastDnPts, SlowUpPts, SlowDnPts):
            plot_fractals(pts, df, ax)

    zones = findzones(df, FastUpPts, FastDnPts, SlowUpPts, SlowDnPts, High, Low, Close, Bars, BackLimit)
    print("drawing zones")
    print(zones)
    for z in zones:
        drawzone(df, ax, z)


def drawzone(df, ax, z):

        if z['strength'] == ZONE_WEAK and not zone_show['weak']:
            continue
        if z['strength'] == ZONE_UNTESTED and not zone_show['untested']:
            continue
        if z['strength'] == ZONE_TURNCOAT and not zone_show['turncoat']:
            continue
        s = z['type'] + '_' + z['str']


        if z['strength'] == ZONE_PROVEN or z['strength'] == ZONE_VERIFIED:
            s += ", Test Count=" + str(z['hits'])

        color = zone_color[z['type'] + '_' + z['str']]
        starttime = df.loc[z['start'], 'Date']
        endtime = df.Date.iat[-1]
        print("plot rectangle")
        plot_rectangle(ax, starttime, endtime, z['lo'], z['hi'], color)


def findzones_is_touch(iszonesupply,turned,zonebottom,zonetop,UpPt,DnPt):
    # if the zone is resistance and the new high point has entered the zone
    # or if the zone has become Sup and the new low point has entered the zone
    if iszonesupply:
        if (not turned and zonebottom <= UpPt <= zonetop) or (turned and zonebottom <= DnPt <= zonetop):
            return True
    else:
        if (turned and zonebottom <= UpPt <= zonetop) or (not turned and zonebottom <= DnPt <= zonetop):
            return True
    return False


def findzones_is_bust(iszonesupply,turned,zonebottom,zonetop,High,Low):
    print("findzones_is_bust: iszonesupply: {} turned: {} zonebottom: {} zonetop: {} High: {} Low: {}".format(iszonesupply,
                                                                                                         turned, zonebottom, zonetop,
                                                                                                              High, Low))
    if iszonesupply:
        if (not turned and High > zonetop) or (turned and Low < zonebottom):
            return True
    else:
        if (turned and High > zonetop) or (not turned and Low < zonebottom):
            return True
    return False


def findzones_isvalid(iszonesupply,shift, zonetop, zonebottom, isWeak, FastUpPts, FastDnPts, High, Low, ):
    turned = False
    hasturned = False
    isBust = False

    bustcount = 0
    testcount = 0

    print("findzones_isnotbust: iszonesupply: {} shift: {} zonetop: {} zonebottom: {} isWeak: {}".format(iszonesupply, shift, zonetop, zonebottom, isWeak))

    #now that we have the left boundary of the zone, look at candles to the right to find how the price reacted to the zone
    for i in range(shift - 1, 0, -1):
        #we have a touch:
        print("look for touch at index {} FastUpPts[i]: {} FastDnPts[i]: {}".format(i, FastUpPts[i], FastDnPts[i]))
        if findzones_is_touch(True, turned, zonebottom, zonetop, FastUpPts[i], FastDnPts[i]):
            # Potential touch, just make sure its been 10+candles since the prev one
            print("potential Touch")
            touchOk = True
            for j in range(i + 1, i + 11):
                if findzones_is_touch(iszonesupply, turned, zonebottom, zonetop, FastUpPts[j], FastDnPts[j]):
                    print("it has been less than 10 candles since the previous one")
                    touchOk = False
                    break

            if touchOk:
                # we have a touch_  If its been busted once, remove bustcount
                # as we know this level is still valid & has just switched sides
                bustcount = 0
                testcount = testcount + 1

        if findzones_is_bust(iszonesupply, turned, zonebottom, zonetop, High[i], Low[i]):
            # this level has been busted at least once

            bustcount = bustcount + 1
            print("this level has been busted at least once, bustcount {}".format(bustcount))
            if bustcount > 1 or isWeak:
                print("level is Busted because bustcount > 1 or isWeak: bustcount {} isWeak {}".format(bustcount,isWeak))
                # busted twice or more

                isBust = True
                break

            if turned:
                turned = False
            elif not turned:
                turned = True

            hasturned = True

            # forget previous hits
            testcount = 0

    if not isBust:
        zone = {'hi': zonetop, 'lo': zonebottom, 'turn': hasturned, 'hits': testcount, 'start':  shift, 'merge': False}

        if testcount > 3:
            zone['strength'] = ZONE_PROVEN
            zone['str'] = "proven"
        elif testcount > 0:
            zone['strength'] = ZONE_VERIFIED
            zone['str'] = "verified"
        elif hasturned:
            zone['strength'] = ZONE_TURNCOAT
            zone['str'] = "turncoat"
        elif not isWeak:
            zone['strength'] = ZONE_UNTESTED
            zone['str'] = "untested"
        else:
            zone['strength'] = ZONE_WEAK
            zone['str'] = "weak"
        return zone
    return None


def findzones(df, FastUpPts,FastDnPts,SlowUpPts,SlowDnPts, High, Low, Close, Bars, BackLimit):
    # iterate through zones from oldest to youngest(ignore recent 5 bars),
    # finding those that have survived through to the present

    zone_fuzzfactor = 0.75
    zone_extend = True
    zone_merge = True
    #temp_count = 0
    temp_zones = []
    limit = min(Bars-1, BackLimit)
    #print(High)
    #print(Low)
    #print(df['Close'].values)
    iatr = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, 7)
    #print(atr)

    for shift in range(limit, 5, -1):
        atr = iatr[shift]
        fu = atr / 2 * zone_fuzzfactor
        isWeak = True
        touchOk = False
        isBust = False

        if FastUpPts[shift] > 0.001:
            # a zigzag high point
            isWeak = True
            if SlowUpPts[shift] > 0.001:
                isWeak=False

            #store the top of the resistance zone into hival
            zonetop = High[shift]

            if zone_extend:
                zonetop = zonetop + fu

            zonebottom = max(min(Close[shift], High[shift] - fu), High[shift] - fu * 2)
            print("found zigzag high point at {} , hival: {} loval: {}".format(shift, zonetop, zonebottom))
            zone = findzones_isvalid(True, shift, zonetop, zonebottom, isWeak, FastUpPts, FastDnPts, High, Low)
            if zone:
                #level is still valid, add to our list
                temp_zones.append(zone)


        if FastDnPts[shift] > 0.001:
            # a zigzag high point
            isWeak = True
            if SlowDnPts[shift] > 0.001:
                isWeak = False
            zonebottom = Low[shift]
            if zone_extend:
                zonebottom = zonebottom - fu

            zonetop = min(max(Close[shift], Low[shift] + fu), Low[shift] + fu * 2)
            print("found zigzag low point at {} , hival: {} loval: {}".format(shift, zonetop, zonebottom))
            zone = findzones_isvalid(False, shift, zonetop, zonebottom, isWeak, FastUpPts, FastDnPts, High, Low)
            if zone:
                # level is still valid, add to our list
                temp_zones.append(zone)

    print(temp_zones)


    #merge zones
    #if zone_merge:


    # copy the remaining list into our official zones arrays
    zones = []

    for z in temp_zones:
        print(z)
        if z['hits'] >= 0:
            print("zone hits >=0")
            if z['hi'] < Close[4]:
                z['type'] = "Sup"
            elif z['hi'] > Close[4]:
                z['type'] = "Res"
            else:
                j=0
                for j in range(5,1000):
                    if j < len(Close) and Close[j] < z['lo']:
                        z['type'] = "Res"
                        break
                    elif j < len(Close) and Close[j] < z['lo']:
                        z['type'] = "Sup"
                        break
                if j == 1000:
                    z['type'] = "Sup"
            print("adding zone to final list")
            zones.append(z)

    return zones



def plot_fractals(pts, df, ax):

    # plot fractal pts as circles to debug
    for idx, value in pts.items():
        if value > 0:
            #time = df.loc[df.rownum == idx].index.to_pydatetime()
            time = df.loc[idx, 'Date']
            #time = df['Date'].iloc[idx]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    n bvindex.to_pydatetime()
            # print("time: {} value: {}".format(time, value))
            plot_circle(ax, time, value)

def fractal(M,P,shift, High,Low,Bars):
    if period > P:
        P = period

    P = P / period * 2 + math.ceil(P / period / 2)
    #print("fractal - Bars: {} P: {} M: {} shift: {}".format(Bars,P,M,shift))
    if shift < P:
        # print("   shift lower than P")
        return False

    if shift > Bars - P:
        # print("   shift > Bars - P")
        return False

    for i in range(1, int(P)):
        # print("i: {}".format(i))
        if M == UP_POINT:
            # print("   Up point? - i: {} PrevHigh: {} High: {}".format(i, High[shift + i], High[shift]))
            if High[shift + i] > High[shift]:
                return False
            if High[shift - i] >= High[shift]:
                return False
        if M == DN_POINT:
            # print("   Dn point? - PrevLow: {} Low: {}".format(Low[shift + i], Low[shift]))
            if Low[shift + i] < Low[shift]:
                return False
            if Low[shift - i] <= Low[shift]:
                return False
    #print("return true")
    return True


def Fractals(fractal_factor, High, Low, Bars, BackLimit):


    limit = min(Bars-1, BackLimit)
    #print("Fractals - Bars: {} Limit: {}".format(Bars, limit))
    P = period*fractal_factor

    DnPts = {}
    UpPts = {}
    UpPts[0] = 0
    UpPts[1] = 0
    DnPts[0] = 0
    DnPts[1] = 0

    for shift in range(limit, 1, -1):
    #for(shift=limit; shift>1; shift--)
        if fractal(UP_POINT, P, shift, High, Low, Bars):
            UpPts[shift] = High[shift]
        else:
            UpPts[shift] = 0

        if fractal(DN_POINT, P, shift, High, Low, Bars):
            DnPts[shift] = Low[shift]
        else:
            DnPts[shift] = 0

    return UpPts, DnPts

