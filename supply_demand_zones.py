import math
from plot import *
#import talib
import logging
#from technical_indicators import ATR
import technical_indicators
#import pandas_talib


class SupDem:

    UP_POINT=1
    DN_POINT=-1
    fractal_period = 1
    zone_type = {'ZONE_WEAK': 0,
				'ZONE_TURNCOAT': 1,
				'ZONE_UNTESTED': 2,
				'ZONE_VERIFIED': 3,
				'ZONE_PROVEN': 4}
    zone_color = {'Sup_weak': 'DarkSlateGray', 'Sup_untested': 'SeaGreen', 'Sup_verified': 'Green',
                 'Sup_proven': 'LimeGreen', 'Sup_turncoat': 'OliveDrab', 'Res_weak': 'Indigo',
                 'Res_untested': 'Orchid', 'Res_verified': 'Crimson', 'Res_proven': 'Red',
                 'Res_turncoat': 'DarkOrange'}
    zone_show = {'weak': True, 'untested': True, 'turncoat': True}
    fractal_fast_factor = 3.0
    fractal_slow_factor = 6.0

    def __init__(self, df, zone_merge=False, period=500, zone_extend=True):
        #we need to reverse the dataframe as the original MT4 code is looking backwards
        df.index.name = 'Date'
        self.df = df[::-1]

        self.zone_extend = zone_extend
        logging.debug(self.df)
        High = self.df['High'].values
        logging.debug(High)
        Low = self.df['Low'].values
        Close = self.df['Close'].values
        Bars = len(self.df.index)

        self.FastUpPts,self.FastDnPts = self.Fractals(self.fractal_fast_factor, High, Low, Bars, period)
        logging.debug("FastUpPts: {}".format(self.FastUpPts))
        logging.debug("FastDnPts: {}".format(self.FastDnPts))
        #exit()
        self.SlowUpPts, self.SlowDnPts = self.Fractals(self.fractal_slow_factor, High, Low, Bars, period)
        logging.debug("SlowUpPts: {}".format(self.SlowUpPts))
        logging.debug("SlowDnPts: {}".format(self.SlowDnPts))

        #create a numeric index on the reversed dataframe
        self.df = self.df.reset_index()

        tmp_zones = self.findzones(self.FastUpPts, self.FastDnPts, self.SlowUpPts, self.SlowDnPts, High, Low, Close, Bars, period)
        if zone_merge:
            tmp_zones = self.zones_merge(tmp_zones)
        self.zones = self.__type_zones(tmp_zones, Close)
        logging.debug(self.zones)

    def get_zones(self):
        return self.zones

    def drawzones(self):
        for z in self.zones:
            self.drawzone(z)

    def drawzone(self, z):
            if z['strength'] == self.zone_type['ZONE_WEAK'] and not self.zone_show['weak']:
                return
            if z['strength'] == self.zone_type['ZONE_UNTESTED'] and not self.zone_show['untested']:
                return
            if z['strength'] == self.zone_type['ZONE_TURNCOAT'] and not self.zone_show['turncoat']:
                return

            timeframes = {'1 days 00:00:00': 'daily', '0 days 01:00:00': 'hourly', '0 days 04:00:00': '4H',
                          '0 days 06:00:00': '6H', '7 days 00:00:00': 'Weekly'}
            timeframe = str(self.df.Date.iat[0] - self.df.Date.iat[1])
            if timeframe in timeframes:
                timeframe = timeframes[timeframe]

            s = timeframe + " "
            s += z['type'] + '_' + z['str']


            if z['strength'] == self.zone_type['ZONE_PROVEN'] or z['strength'] == self.zone_type['ZONE_VERIFIED']:
                s += ", Test Count=" + str(z['hits'])

            color = self.zone_color[z['type'] + '_' + z['str']]
            starttime = self.df.loc[z['start'], 'Date']
            #endtime = df.Date.iat[-1]
            endtime = self.df.Date.iat[0]
            #logging.debug("plot rectangle")
            plot_rectangle(starttime, endtime, z['lo'], z['hi'], color, s)


    def findzones(self, FastUpPts,FastDnPts,SlowUpPts,SlowDnPts, High, Low, Close, Bars, BackLimit):
        # iterate through zones from oldest to youngest(ignore recent 5 bars),
        # finding those that have survived through to the present

        def zone_touched(iszonesupply, turned, zonebottom, zonetop, UpPt, DnPt):
            if iszonesupply:
                # if the zone is resistance and the new high point has entered the zone
                # or if the zone has become Sup and the new low point has entered the zone
                if (not turned and zonebottom <= UpPt <= zonetop) or (turned and zonebottom <= DnPt <= zonetop):
                    return True
            else:
                # support zone turned resistance and new high point entered
                # support zone and new low point entered
                if (turned and zonebottom <= UpPt <= zonetop) or (not turned and zonebottom <= DnPt <= zonetop):
                    return True
            return False

        def zone_is_bust(iszonesupply, turned, zonebottom, zonetop, High, Low):

            if iszonesupply:
                if (not turned and High > zonetop) or (turned and Low < zonebottom):
                    #logging.debug("Supply Zone is bust - turned: {} High: {} Low: {}".format(turned,High,Low))
                    return True
            else:
                if (turned and High > zonetop) or (not turned and Low < zonebottom):
                    #logging.debug("Demand Zone is bust - turned: {} High: {} Low: {}".format(turned,High,Low))
                    return True
            return False

        def validate_zone(iszonesupply, shift, zonetop, zonebottom, isWeak, FastUpPts, FastDnPts, High, Low, ):
            turned = False
            hasturned = False
            touchOk = False

            bustcount = 0
            testcount = 0

            #logging.debug("findzones_isvalid: iszonesupply: {} shift: {} zonetop: {} zonebottom: {} isWeak: {}".format(
            #    iszonesupply, shift, zonetop, zonebottom, isWeak))

            # now that we have the left boundary of the zone, look at candles to the right to find how the price reacted to the zone
            for i in range(shift - 1, 0, -1):
                # we have a touch:
                # logging.debug("look for touch at index {} FastUpPts[i]: {} FastDnPts[i]: {}".format(i, FastUpPts[i], FastDnPts[i]))
                #Check if the new high and low points have entered the zone
                if zone_touched(iszonesupply, turned, zonebottom, zonetop, FastUpPts[i], FastDnPts[i]):
                    # Potential touch, just make sure its been 10+candles since the prev one
                    logging.debug("potential Touch at {} index {} FastUpPts[i]: {} FastDnPts[i]: {}".format(self.df.loc[i, 'Date'], i, FastUpPts[i],
                                                                                                 FastDnPts[i]))
                    touchOk = True
                    for j in range(i + 1, i + 11):
                        if zone_touched(iszonesupply, turned, zonebottom, zonetop, FastUpPts[j], FastDnPts[j]):
                            logging.debug("invalid touch -> it has been less than 10 candles since the previous one")
                            touchOk = False
                            break

                    if touchOk:
                        # we have a touch_  If its been busted once, remove bustcount
                        # as we know this level is still valid & has just switched sides
                        bustcount = 0
                        testcount += 1

                #check if the new candle high has pierced the top for resitance or low has pierced the bottom for support
                if zone_is_bust(iszonesupply, turned, zonebottom, zonetop, High[i], Low[i]):
                    # this level has been busted at least once

                    bustcount += 1
                    logging.debug("This level has been busted at {} candle high {}, low {}, "
                                  "bustcount {}".format(self.df.loc[i, 'Date'],High[i], Low[i],bustcount))
                    if bustcount > 1 or isWeak:
                        logging.debug(
                            "Level invalid: busted at least twice or busted once but Weak: bustcount {} isWeak {}".format(bustcount,
                                                                                                             isWeak))
                        # busted twice or more
                        return None

                    if turned:
                        turned = False
                    elif not turned:
                        turned = True

                    hasturned = True

                    # forget previous hits
                    testcount = 0

            zone = {'hi': zonetop, 'lo': zonebottom, 'turn': hasturned, 'hits': testcount, 'start': shift,
                    'merge': False}

            if testcount > 3:
                zone['strength'] = self.zone_type['ZONE_PROVEN']
                zone['str'] = "proven"
            elif testcount > 0:
                zone['strength'] = self.zone_type['ZONE_VERIFIED']
                zone['str'] = "verified"
            elif hasturned:
                zone['strength'] = self.zone_type['ZONE_TURNCOAT']
                zone['str'] = "turncoat"
            elif not isWeak:
                zone['strength'] = self.zone_type['ZONE_UNTESTED']
                zone['str'] = "untested"
            else:
                zone['strength'] = self.zone_type['ZONE_WEAK']
                zone['str'] = "weak"
            logging.debug("valid zone found:{}".format(zone))
            return zone



        zone_fuzzfactor = 0.75

        recent_bars_to_ignore = 3
        #temp_count = 0
        temp_zones = []
        limit = min(Bars-1, BackLimit)
        #logging.debug(High)
        #logging.debug(Low)
        #logging.debug(df['Close'].values)
        #iatr = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, 7)
        #logging.debug(iatr)
        #iatr = technical_indicators.ATR(High, Low, Close, 7)

        #temporary to remove dependancy on talib
        tmpdf = self.df[::-1]
        tmpdf = tmpdf.reset_index()
        iatr = technical_indicators.average_true_range(tmpdf, 7)
        iatr = iatr[::-1]
        #logging.debug(iatr)
        iatr = iatr['ATR_7'].values
        #logging.debug(iatr)

        # iterate through zones from oldest to youngest (ignore recent 5 bars),
        # finding those that have survived through to the present
        for shift in range(limit, recent_bars_to_ignore, -1):
            atr = iatr[shift]
            fu = atr / 2 * zone_fuzzfactor
            isWeak = True

            isBust = False

            if FastUpPts[shift]:
                # a zigzag high point
                isWeak = True
                if SlowUpPts[shift]:
                    isWeak=False

                #store the top of the resistance zone into hival
                zonetop = High[shift]

                if self.zone_extend:
                    zonetop = zonetop + fu

                zonebottom = max(min(Close[shift], High[shift] - fu), High[shift] - fu * 2)
                logging.debug("Checking potential {} supply zone at high point {}, {}, top: {} bottom: {}"
                              .format('weak' if isWeak else 'strong',
                                shift, self.df.loc[shift, 'Date'], zonetop, zonebottom))
                zone = validate_zone(True, shift, zonetop, zonebottom, isWeak, FastUpPts, FastDnPts, High, Low)
                if zone:
                    #level is still valid, add to our list
                    temp_zones.append(zone)


            if FastDnPts[shift]:
                # a zigzag low point
                isWeak = True
                if SlowDnPts[shift]:
                    isWeak = False
                zonebottom = Low[shift]
                if self.zone_extend:
                    zonebottom = zonebottom - fu

                zonetop = min(max(Close[shift], Low[shift] + fu), Low[shift] + fu * 2)
                logging.debug("Checking potential {} demand zone at low point {}, {}, top: {} bottom: {}"
                              .format('weak' if isWeak else 'strong', shift, self.df.loc[shift, 'Date'], zonetop, zonebottom))
                zone = validate_zone(False, shift, zonetop, zonebottom, isWeak, FastUpPts, FastDnPts, High, Low)
                if zone:
                    logging.debug("Level is still valid, add to our list")
                    temp_zones.append(zone)
        logging.debug("\n")
        return temp_zones



    def __type_zones(self, temp_zones, Close):
        # copy the remaining list into our official zones arrays and mark them as support or resistance
        zones = []

        for z in temp_zones:

            #copy only the zones that have not been merged from another (
            if z['hits'] >= 0:
                logging.debug("about to mark this zone as support or resistance:{}".format(z))
                #if the recent high is lower then mark as support
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
                logging.debug("adding {} zone to final list".format(z['type']))
                zones.append(z)
        return zones

    def plot_fractals(self):
        for pts in self.FastUpPts,self.FastDnPts, self.SlowUpPts,self.SlowDnPts:
            # plot fractal pts as circles to debug
            for idx, value in pts.items():
                if value > 0:

                    time = self.df.loc[idx, 'Date']
                    #time = df['Date'].iloc[idx]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    n bvindex.to_pydatetime()
                    # logging.debug("time: {} value: {}".format(time, value))
                    plot_circle(time, value)

    def Fractals(self, fractal_factor, High, Low, Bars, BackLimit):
        def fractal(M, P, shift, High, Low, Bars):
            if self.fractal_period > P:
                P = self.fractal_period

            P = P / self.fractal_period * 2 + math.ceil(P / self.fractal_period / 2)
            # logging.debug("fractal - Bars: {} P: {} M: {} shift: {}".format(Bars,P,M,shift))
            if shift < P:
                # logging.debug("   shift lower than P")
                return False

            if shift > Bars - P:
                # logging.debug("   shift > Bars - P")
                return False

            for i in range(1, int(P)):
                # logging.debug("i: {}".format(i))
                if M == self.UP_POINT:
                    # logging.debug("   Up point? - i: {} PrevHigh: {} High: {}".format(i, High[shift + i], High[shift]))
                    if High[shift + i] > High[shift]:
                        return False
                    if High[shift - i] >= High[shift]:
                        return False
                if M == self.DN_POINT:
                    # logging.debug("   Dn point? - PrevLow: {} Low: {}".format(Low[shift + i], Low[shift]))
                    if Low[shift + i] < Low[shift]:
                        return False
                    if Low[shift - i] <= Low[shift]:
                        return False
            # logging.debug("return true")
            return True

        #logging.debug(High)
        limit = min(Bars-1, BackLimit)
        #logging.debug("Fractals - Bars: {} Limit: {}".format(Bars, limit))
        P = self.fractal_period*fractal_factor

        DnPts = {}
        UpPts = {}
        UpPts[0] = 0
        UpPts[1] = 0
        DnPts[0] = 0
        DnPts[1] = 0

        for shift in range(limit, 1, -1):
        #for(shift=limit; shift>1; shift--)
            if fractal(self.UP_POINT, P, shift, High, Low, Bars):
                UpPts[shift] = High[shift]
            else:
                UpPts[shift] = 0

            if fractal(self.DN_POINT, P, shift, High, Low, Bars):
                DnPts[shift] = Low[shift]
            else:
                DnPts[shift] = 0

        return UpPts, DnPts


    def zones_merge(self, zones):
        merge_count = 1
        iterations = 0
        merge1 = []
        merge2 = []

        #look for overlapping zones ...
        while merge_count > 0 and iterations < 3:
            merge_count = 0
            iterations += 1

            #for each zone set merge flag to false
            for z in zones:
                z['merge'] = False

            #for each zone except the last, ignore zones without hits or already merged
            for i in range(0, len(zones)-1):
                if zones[i]['hits'] == -1 or zones[i]['merge']:
                    continue

                #check the zone after i, ignore zones without hits or already merged
                for j in range(i + 1, len(zones)):
                    if zones[j]['hits'] == -1 or zones[j]['merge']:
                        continue

                    #if the 2 zones are overlapping, put their index in the merge list (merge1 and 2)
                    if (zones[j]['lo'] <= zones[i]['hi'] <= zones[j]['hi'] or
                        zones[j]['lo'] <= zones[i]['lo'] <= zones[j]['hi'] or
                         zones[i]['lo'] <= zones[j]['hi'] <= zones[i]['hi'] or
                        zones[i]['lo'] <= zones[j]['lo'] <= zones[i]['hi']):
                        merge1.append(i)
                        merge2.append(j)
                    # set merge flag to true for both zones
                    zones[i]['merge'] = True
                    zones[j]['merge'] = True
                    merge_count += 1

            #...and merge them
            logging.debug("found zones to merge:")
            logging.debug(merge1)
            logging.debug(merge2)

            #for i in range(0, merge_count):
            for target, source in zip(merge1, merge2):
                #target = merge1[i]
                #source = merge2[i]

                zones[target]['hi'] = max(zones[target]['hi'], zones[source]['hi'])
                zones[target]['lo'] = min(zones[target]['lo'], zones[source]['lo'])
                zones[target]['hits'] += zones[source]['hits']
                zones[target]['start'] = max(zones[target]['start'], zones[source]['start'])
                zones[target]['strength'] = max(zones[target]['strength'], zones[source]['strength'])
                if zones[target]['hits'] > 3:
                    zones[target]['strength'] = ZONE_PROVEN
                    zones[target]['str'] = "proven"

                if zones[target]['hits'] == 0 and not zones[target]['turn']:
                    zones[target]['hits'] = 1
                if zones[target]['strength'] < ZONE_VERIFIED:
                    zones[target]['strength'] = ZONE_VERIFIED
                    zones[target]['str'] = "verified"

                if not zones[target]['turn'] or not zones[source]['turn']:
                    zones[target]['turn'] = False
                if zones[target]['turn']:
                    zones[target]['hits'] = 0

                #set hits to -1 to ignore the zone going forward
                zones[source]['hits'] = -1

        #logging.debug("zones merged:")
        #logging.debug(zones)
        return zones

