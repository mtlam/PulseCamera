# Stripped down and modified version from PyPulse

import numpy as np
import scipy.optimize as optimize

def funcgaussian(p,x,width=1.0,baseline=False):
    if baseline:
        return p[0] * np.exp(-((x-p[1])/(np.sqrt(2)*width))**2) + p[2]
    return p[0] * np.exp(-((x-p[1])/(np.sqrt(2)*width))**2)
def errgaussian(p,x,y,width=1.0,baseline=False):
    return funcgaussian(p,x,width=width,baseline=baseline) - y
def gaussianfit(x,y,guesswidth,baseline=False):
    x=np.array(x)
    y=np.array(y)
    height=max(y)
    mu=np.sum(x*y)/np.sum(y)
    #sigma=np.sqrt(np.abs(np.sum((x-mu)**2*y)/np.sum(y)))
    if baseline:
        p0=[height,mu,0.0]
    else:
        p0=[height,mu]
    out = optimize.leastsq(errgaussian, p0[:], args=(x,y,guesswidth,baseline), full_output = True)
    return out #p1, errgaussian(p1,x,y,baseline)
