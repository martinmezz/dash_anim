import numpy as np
#from lmfit import Model,Parameters
from scipy.optimize import curve_fit


def cum_hyperbolic_correlation(t, qi, di, b):
    '''
    Function for hyperbolic cumulative, to use on EUR correlation.
    
    Params:
        t (ndarray): times for which to calculate decline
        qi (float): theorical initial rate
        di (float): decline rate
        b (float): model exponent
    
    Returns:
        Q (ndarray):
    '''

    return (qi**b / (di*(1 - b))) * (qi**(1 - b) - (qi/((b*di*t + 1)**(1/b)))**(1 - b))


def cum_hyper_modif_correlation(t, qi, di, b):
    '''
    Function for modified hyperbolic cumulative, to use on EUR correlation.

    Params:
    t (ndarray): times for which to calculate decline
    qi (float): theorical initial rate
    di (float): decline rate
    b (float): model exponent

    Returns:
        Q (ndarray):
    '''

    tiempo_cambio = 2432
    
    # Dividir vector
    tiempo_hip = t[t < tiempo_cambio]
    tiempo_exp = t[t >= tiempo_cambio]
    
    acum_hip = (qi**b / (di*(1 - b))) * (qi**(1 - b) - (qi/((b*di*tiempo_hip + 1)**(1/b)))**(1 - b))
    acum_cambio = acum_hip[-1]
    caudal_cambio = qi * (1+b*di*tiempo_cambio)**(-1/b)
    dn_cambio = di / (1+b*di*(tiempo_cambio-20))
    #dn_cambio = -(caudal_hip[-1] - caudal_hip[-2]) /(caudal_hip[-1] * (tiempo_hip[-1] - tiempo_hip[-2]))
    acum_exp = acum_cambio + caudal_cambio * (1 - np.exp(-dn_cambio * (tiempo_exp - tiempo_cambio)))/dn_cambio
    
    return np.append(acum_hip, acum_exp)


def hyperbolic(t, qi, di, b):
    '''
    Function for hyperbolic decline.
    
    Params:
        t (ndarray): times for which to calculate decline
        qi (float): theorical initial rate
        di (float): decline rate
        b (float): model exponent

    Returns:
        q (ndarray):
    '''

    return qi / ((1 + b * di * t)**(1/b))


def hiperbola_modificada(t, Qi, Dni, b_coeff):
    '''
    Function for modified hyperbolic decline.
    
    Params:
        t (ndarray): times for which to calculate decline
        qi (float): theorical initial rate
        di (float): decline rate
        b (float): model exponent

    Returns:
        q (ndarray):
    '''

    tiempo_cambio = 2432

    # Dividir vector
    tiempo_hip = t[t < tiempo_cambio]
    tiempo_exp = t[t >= tiempo_cambio]

    # Calcular cada uno con su func
    caudal_hip = Qi * (1 + Dni * b_coeff * tiempo_hip) ** (-1/b_coeff)
    dn_cambio = Dni / (1 + b_coeff * Dni * (tiempo_cambio - 20))
    #dn_cambio = -(caudal_hip[-1] - caudal_hip[-2]) /(caudal_hip[-1] * (tiempo_hip[-1] - tiempo_hip[-2]))
    
    caudal_de_cambio = Qi * (1 + Dni * b_coeff * tiempo_cambio) ** (-1/b_coeff)
    caudal_exp = caudal_de_cambio * np.exp(-dn_cambio * (tiempo_exp-tiempo_cambio))

    return np.append(caudal_hip, caudal_exp)


def predecir_qmax(fracs,rama):
    '''TODO: AGREGAR DOCSTRING'''

    if fracs < 43:
        return float(np.exp(0.038631*fracs + 0.000103*rama + 3.682385))
    else:
        return float(np.exp(0.5639*np.log(fracs)+5.4708) / 6.29)


def predecir_EUR(fracs,rama):
    '''TODO: AGREGAR DOCSTRING'''
    
    return float(np.exp(0.025625*fracs + 0.000235*rama + 10.4018))


def predecir_np1a(fracs,rama):
    '''TODO: AGREGAR DOCSTRING'''
    
    return float(np.exp(1.025619*np.log(fracs) + -0.0805*np.log(rama) + 7.533349))


def decline_correlation(fracs, rama, tipo='P50', b_max=1.3, t_qmax=90,
    dni_max=1, to_time=9132):
    '''
    Apply default decline based on correlation.
    
    Params:
        fracs: fracturas (int)
        rama: rama lateral en metros (int)
        tipo: tipo de declinacion ('P50','P90' o 'P10')
        t_qmax: tiempo hasta el caudal maximo en dias (float)
        b_max: limite superior para b (float)
        dni_max: limite superior para dni en 1/dias (float)
        
    Returns:
        well(dict):
    '''

    # Calculate q max (based on correlation)
    qi = predecir_qmax(fracs, rama)
    #qi= 400
    
    if tipo == 'P50':
        pass
    elif tipo == 'P90':
        qi = qi / (1 + 0.169)
    elif tipo == 'P10':
        qi = qi / (1 - 0.155)
    
    # Acumulada al t qmax, qmax (lineal)
    Np_qmax = int(t_qmax * qi / 2)
    
    # Calculate EUR (based on correlation)
    EUR = predecir_EUR(fracs, rama)
    EUR_t = to_time

    if tipo == 'P50':
        pass
    elif tipo == 'P90':
        EUR = EUR / (1 + 0.3064)
    elif tipo == 'P10':
        EUR = EUR / (1 - 0.239)

    # Calculate cumg at 365 days (based on correlation)
    np1a = predecir_np1a(fracs, rama)
    #np1a = 70000
    
    if tipo == 'P50':
        np1a = np1a
    elif tipo == 'P90':
        np1a = np1a / (1 + 0.219)
    elif tipo == 'P10':
        np1a = np1a / (1 - 0.166)

    # Append cumg_365 and EUR to aux arrays
    t_aux = np.array([0, 365, EUR_t])
    cum_aux = np.array([Np_qmax, np1a, EUR])

    # Curve fitting
    MAXFEV = len(cum_aux) * 100
    popt, pcov = curve_fit(cum_hyper_modif_correlation, t_aux,
    cum_aux, maxfev=int(MAXFEV), bounds=((qi*0.97, 0, 0.4),
                    (qi*1.03, dni_max, b_max)))
    curve_fitted = True
            
    qi_calc, di, b = popt

# =============================================================================
#     # LMFIT
#     hm_model = Model(cum_hyper_modif_correlation)
#     fit_params = Parameters()
#     fit_params.add('qi', value=qi, max=1.05*qi, min=0.95*qi)
#     fit_params.add('di', value=0.5, max=1, min=0)
#     fit_params.add('b', value=1.1, max=1.6, min=0.4)
#     
#     result = hm_model.fit(cum_aux, fit_params, t=t_aux, nan_policy='propagate')
#    
#     qi_calc = result.params['qi'].value
#     di = result.params['di'].value
#     b = result.params['b'].value
# =============================================================================
   
    # Create times array
    t_forecast = np.linspace(0, to_time, 200)

    # Decline
    qo_forecast = hiperbola_modificada(t_forecast, qi_calc, di, b)
    
    # Inclination
    t_inclina = np.array([0, t_qmax])
    q_inclina = np.array([0, qi_calc])
    acum_inclina = np.array([0, Np_qmax])
    
    # Complete data arrays
    tiempo = np.append(t_inclina, t_forecast.copy() + t_qmax)
    caudal = np.append(q_inclina, qo_forecast.copy())
    acumulada = np.append(
        acum_inclina,
        cum_hyper_modif_correlation(t_forecast, qi_calc, di, b) + Np_qmax
    )

    pronostico = {
        'tiempo': tiempo,
        'caudal': caudal,
        'acumulada': acumulada,
        'fracturas': fracs,
        'rama': rama
    }
    
    return pronostico, EUR, qi, np1a


def calc_forecast(fracs=56, rama=2800):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    forecast = {}

    pronostico50, EUR50, qi50, np1a50 = decline_correlation(fracs, rama, tipo='P50')
    pronostico90, EUR90, qi90, np1a90 = decline_correlation(fracs, rama, tipo='P90')
    pronostico10, EUR10, qi10, np1a10 = decline_correlation(fracs, rama, tipo='P10')
    
    forecast['times'] = pronostico50['tiempo']
    
    forecast['qo_p50'] = pronostico50['caudal']
    forecast['cumo_p50'] = pronostico50['acumulada']
        
    forecast['qo_p90'] = pronostico90['caudal']
    forecast['cumo_p90'] = pronostico90['acumulada']
    
    forecast['qo_p10'] = pronostico10['caudal']
    forecast['cumo_p10'] = pronostico10['acumulada']

    return forecast