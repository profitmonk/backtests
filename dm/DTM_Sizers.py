    ######################################
    #
    # Backtrader Sizers
    # 
    # maxRiskSizer
    #
    ######################################
#
# Module imports
#
import backtrader as bt
import math
#
# Import my code
#

class maxRiskSizer(bt.Sizer):
    '''
    Returns the number of shares rounded down that can be purchased for the
    max rish tolerance
    '''
    params = (('risk', 0.03),)

    def __init__(self):
        if self.p.risk > 1 or self.p.risk < 0:
            raise ValueError('The risk parameter is a percentage which must be'
                'entered as a float. e.g. 0.5')

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy == True:
            size = math.floor((cash * self.p.risk) / data[0])
        else:
            size = math.floor((cash * self.p.risk) / data[0]) * -1
        return size
    
class PercentRiskSizer(bt.Sizer):
    '''Sizer modeling the Percentage Risk sizing model of Van K. Tharp'''
    params = dict(percrisk=0.01)  # 1% percentage risk

    def _getsizing(self, comminfo, cash, data, isbuy):
        # Risk per 1 contract
        risk = comminfo.p.mult * self.strategy.stoptrailer.stop_dist[0]
        # % of account value to risk
        torisk = self.broker.get_value() * self.p.percrisk
        return torisk // risk  # size to risk