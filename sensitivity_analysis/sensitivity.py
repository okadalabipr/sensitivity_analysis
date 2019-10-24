import sys
import numpy as np
from scipy.integrate import simps

from .model.name2idx import f_parameter as C
from .model.name2idx import f_variable as V
from .model import differential_equation as de
from .model.param_const import f_params
from .model.initial_condition import initial_values
from .ode_solver import solveode

# Calculation of the duration as the time it takes to decline below 10% of its maximum
def get_duration(time_course_vector):
    maximum_value = np.max(time_course_vector)
    t_max = np.argmax(time_course_vector)

    time_course_vector = time_course_vector - 0.1*maximum_value
    time_course_vector[time_course_vector > 0.0] = -np.inf

    duration = np.argmax(time_course_vector[t_max:]) + t_max

    return duration


def analyze_sensitivity():

    x = f_params()
    y0 = initial_values()

    condition = 2 # EGF & HRG
    tspan = range(5401) # -> 90 min.
    len_v = 57 # Num. of Rate equations (See differential_equation.py)

    rate = 1.01 # 1% change

    # Signaling metric
    duration_cFosmRNA = np.empty((condition,len_v))
    integ_PcFos = np.empty((condition,len_v))

    for j in range(len_v):
        de.perturbation = [1]*len_v
        de.perturbation[j] = rate

        for i in range(condition):
            if i==0:
                y0[V.EGF] = 10.0
                y0[V.HRG] = 0.0
            elif i==1:
                y0[V.EGF] = 0.0
                y0[V.HRG] = 10.0

            (T,Y) = solveode(de.diffeq,y0,tspan,tuple(x))

            cFosmRNA = Y[:,V.cfosmRNAc]
            PcFos = Y[:,V.pcFOSn]*(x[C.Vn]/x[C.Vc]) + Y[:,V.pcFOSc]

            duration_cFosmRNA[i,j] = get_duration(cFosmRNA)
            integ_PcFos[i,j] = simps(PcFos)
            
            sys.stdout.write('\r%d/%d'%(1+j,len_v))
            

    # Sensitivity coefficient
    s_cFosmRNA = np.log(duration_cFosmRNA/duration_cFosmRNA[:,0][:,None])/np.log(rate)
    s_PcFos = np.log(integ_PcFos/integ_PcFos[:,0][:,None])/np.log(rate)

    return s_cFosmRNA, s_PcFos