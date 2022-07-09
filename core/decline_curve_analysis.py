import json
import plotly.express as px
from scipy.optimize import curve_fit, newton
import numpy as np
from math import e
import pandas as pd
import plotly.graph_objects as go
import copy


def extract_wells_data(df, wellnames):
    '''
    Retrieve data from wells specified in 'wellnames' and create wells dict.
    
    Params:
        df (dataFrame): contain production times, rates for several wells
        wellnames (list of str): well names to extract from df

    Returns:
        wells_data:
        wells_data_raw:
        wells:
    '''

    wells_data = [extract_single_well(df, well, filter=True) for well in wellnames]
    wells_data_raw = [extract_single_well(df, well) for well in wellnames]
    wells = dict.fromkeys(wellnames, {})

    return wells_data, wells_data_raw, wells


def extract_single_well(df, well:str, filter=False):
    '''
    Get data for single well and return it sorted.
    
    Params:
        df (dataFrame): contain production times, rates for several wells
        well (str): well to extract from df
        filter (bool): indicates if data with q_ef = 0 must be filtered

    Returns:
        well_data (dataFrame):
    '''

    well_data = df[df['Pozo_Form'] == well].sort_values(['TdP', 'qo_ef', 'qg_ef'])
    if filter: well_data.drop_duplicates(subset='TdP', keep='last', inplace=True)

    return well_data.reset_index(drop=True)


def hyperbolic(t, qi, di, b):
    '''
    Function for hyperbolic decline

    Params:
        t(float): times for which to calculate decline
        qi(float): theorical initial rate
        di(float): decline rate
        b(float): model exponent
    
    Returns:
        q(float): calculated rate
    '''

    return qi / ((1 + b * di * t)**(1/b)) 


def exponential(t, qi, di):
    '''
    Function for exponential decline

    Params:
        t(float): times for which to calculate decline
        qi(float): theorical initial rate
        di(float): decline rate
    
    Returns:
        q(float): calculated rate
    '''

    return qi * (e **(-di * t))


def get_dca_params(data, fluid):
    '''
    Get rate, time and cumulative for a single well data.

    Params:
        data (series): contain production times, rates and cumulatives for a
            single well
        fluid (string): forecasted fluid, used to slice data from max rate index
    
    Returns:
        dca_data (dataFrame): production times, rates and cumulatives for a
            single well, starting from q_max.
        q_max (float): max rate from which to decline.
        cum_at_q_max (float): cumulative from which to decline.
        t_at_q_max (float): time from which to decline.
    '''

    if fluid == 'oil':
        q_max_pos = data['qo_ef'].idxmax()
        dca_data = data.iloc[q_max_pos:]

        return (dca_data.reset_index(drop=True),
            dca_data['TdP'].iloc[0],
            dca_data['qo_ef'].iloc[0],
            dca_data['Acu_Pet'].iloc[0])

    elif fluid == 'gas':
        q_max_pos = data['qg_ef'].idxmax()
        dca_data = data.iloc[q_max_pos:]

        return (dca_data.reset_index(drop=True),
            dca_data['TdP'].iloc[0],
            dca_data['qg_ef'].iloc[0],
            dca_data['Acu_Gas'].iloc[0])
    else:
        return None, None, None, None


def normalize_data(x_data, y_data, x_max, y_max):
    '''Normalizes x and y array data'''
    
    return np.nan_to_num(x_data/x_max), np.nan_to_num(y_data/y_max)


def scale_to_range(value, minv, maxv, target_min, target_max):
    '''Scales data from (minv, maxv) to (target_min, target, max)'''
    
    return (value - minv)/(maxv - minv) * (target_max - target_min) + target_min


def fit_model(model, t_norm, q_norm, boundaries):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    # Curve fitting and decline
    curve_fitted = False
    MAXFEV = 5000

    while not curve_fitted:
        valid = ~(np.isnan(t_norm) | np.isnan(q_norm))
        popt, _ = curve_fit(model, t_norm[valid], q_norm[valid],
            maxfev=int(MAXFEV), bounds=boundaries)
        curve_fitted = True

    return popt


def calc_t_and_cum_arrays(last_t, last_cum, model, final_time, cumi, qi, di, b):
    '''
    Calculates times and gas cumulatives arrays for a well based on
    Newton-Raphson method.
    
    Params:
        - last_t
        - last_cum
        - model
        - final_time
        - cumi
        - qi
        - di
        - b

    Returns:
        - t_forecast:
        - cum_forecast:
    '''

    t_forecast, cum_forecast = [last_t], [last_cum]

    if model == 'HYP':
        func = lambda cum: 30.44 - (cum - cum_prev) / hyperbolic(cum - cumi,
            qi, di, b)
    else:
        func = lambda cum: 30.44 - (cum - cum_prev) / exponential(cum - cumi,
            qi, di)

    while (t_forecast[-1] + 30.44) < final_time:
        cum_prev = cum_forecast[-1]
        cum_forecast.append(newton(func, cum_prev, tol=1e-01, maxiter=100,
            disp=False))
        t_forecast.append(t_forecast[-1] + 30.44)

    cum_forecast = np.around(cum_forecast, decimals=2).astype('float64')
    t_forecast = np.array(t_forecast, dtype='float64')

    return t_forecast, cum_forecast
    
    
def oil_dca_HM_by_t(well, dca_model, exp_start_t, end_time):
    '''
    TODO: AGREGAR DOCSTRING
    '''
    
    # Get parameters for DCA
    dca_data, ti, qi, _ = get_dca_params(well['well_data'], 'oil')
    q_max, t_max = qi, ti
    end_time_days = round(end_time * 365.25)
    
    if dca_model == 'HYP': exp_start_t = end_time_days

    # If well has 1 data or exp_start_t < 0, return empty
    if len(dca_data) <= 1 or exp_start_t < 0:
        well['t_forecast'] = np.array([], dtype='float64')
        well['qo_forecast'] = np.array([], dtype='float64')
        well['b'] = 'None'
        well['d_hyp'] = 'None'
        well['d_exp'] = 'None'
        well['dca_model'] = dca_model

        return copy.deepcopy(well)

    # Split data into hyp and exp models, based on exp_start_t
    t_history_hyp = np.array(dca_data['TdP'][dca_data['TdP'] < exp_start_t])
    t_history_exp = np.array(dca_data['TdP'][dca_data['TdP'] >= exp_start_t])

    qo_history_hyp = np.array(dca_data['qo_ef'][dca_data['TdP'] < exp_start_t])
    qo_history_exp = np.array(dca_data['qo_ef'][dca_data['TdP'] >= exp_start_t])

    #----------------------------------------
    # Hyperbolic section
    #----------------------------------------
    # Normalize dca data
    t_aux = t_history_hyp - ti
    q_aux = qo_history_hyp
    t_norm, q_norm = normalize_data(t_aux, q_aux, ti, qi)

    # Calculate times
    t_forecast_hyp = np.append(t_aux,
        np.arange(t_aux[-1] + 30.44, exp_start_t - ti, 30.44))

    # Curve fitting
    qi, di, b = fit_model(hyperbolic, t_norm, q_norm, ((0, 0, 0), (np.inf, np.inf, 1.2)))

    # De-normalize dca data
    qi, di = qi * q_max, di / t_max

    # Decline hyperbolic section
    qo_forecast_hyp = hyperbolic(t_forecast_hyp, qi, di, b)

    if dca_model == 'HYP':
        # Store rates forecast
        well['t_forecast'] = np.array(t_forecast_hyp + ti, dtype='float64')
        well['qo_forecast'] = np.array(qo_forecast_hyp, dtype='float64')

        # Store forecast params
        well['b'] = f'{b:.4f}' if b else 'None'
        well['d_hyp'] = f'{di * 365.25 * 100:.4f}' if di else 'None'
        well['d_exp'] = 'None'
        well['dca_model'] = dca_model

        return copy.deepcopy(well)
    
    #----------------------------------------
    # Exponential section
    #----------------------------------------
    if len(qo_forecast_hyp) > 1:
        # Calculate di_exp
        last_q_hyp = qo_forecast_hyp[-1]
        last_t_hyp = t_forecast_hyp[-1]
        prev_last_q_hyp = qo_forecast_hyp[-2]
        prev_last_t_hyp = t_forecast_hyp[-2]
        di_exp = -(last_q_hyp - prev_last_q_hyp) / (last_q_hyp * (last_t_hyp - prev_last_t_hyp))

        # Calculate times
        t_aux = t_history_exp - ti
        t_forecast_exp = np.append(t_aux,
        np.arange(last_t_hyp + 30.44, end_time_days - ti, 30.44))

        qo_forecast_exp = exponential(t_forecast_exp - last_t_hyp, last_q_hyp, di_exp)
    else:
        # Normalize dca data
        if len(t_history_exp):
            t_aux = t_history_exp - t_history_exp[0]
        else:
            t_aux = np.array([])

        q_aux = qo_history_exp
        t_norm, q_norm = normalize_data(t_aux, q_aux, ti, qi)

        # Calculate times
        t_forecast_exp = np.arange(t_aux[-1], end_time_days - t_aux[0], 30.44)

        # Curve fitting
        qi, di_exp = fit_model(exponential, t_norm, q_norm, ((0, 0), (np.inf, np.inf)))

        # De-normalize dca data
        qi, di_exp = qi * q_max, di_exp / t_max

        # Decline exponential section
        qo_forecast_exp = exponential(t_forecast_exp, qi, di_exp)
        t_forecast_exp += (dca_data['TdP'][dca_data['TdP'] >= exp_start_t].iloc[0] - ti)

    # Store rates forecast
    well['t_forecast'] = (np.append(t_forecast_hyp, t_forecast_exp) + ti).astype('float64')
    well['qo_forecast'] = (np.append(qo_forecast_hyp, qo_forecast_exp)).astype('float64')

    # Store forecast params
    well['b'] = f'{b:.4f}' if b else 'None'
    well['d_hyp'] = f'{di * 365.25 * 100:.4f}' if di else 'None'
    well['d_exp'] = f'{di_exp * 365.25 * 100:.4f}' if di_exp else 'None'
    well['dca_model'] = dca_model

    return copy.deepcopy(well)


def gas_dca_HM_by_t(well, dca_model, exp_start_t, end_time):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    # Get parameters for DCA
    dca_data, ti, qi, cumi = get_dca_params(well['well_data'], 'gas')
    q_max, cum_max = qi, cumi
    end_time_days = round(end_time * 365.25)
    
    if dca_model == 'HYP': exp_start_t = end_time_days

    # If well has 1 data or exp_start_t < 0, return empty
    if len(dca_data) <= 1 or exp_start_t < 0:
        well['t_forecast'] = np.array([], dtype='float64')
        well['qg_forecast'] = np.array([], dtype='float64')
        well['cumg_forecast'] = np.array([], dtype='float64')
        well['b'] = 'None'
        well['d_hyp'] = 'None'
        well['d_exp'] = 'None'
        well['dca_model'] = dca_model

        return copy.deepcopy(well)

    # Split data into hyp and exp models, based on exp_start_t
    t_history_hyp = np.array(dca_data['TdP'][dca_data['TdP'] < exp_start_t])
    t_history_exp = np.array(dca_data['TdP'][dca_data['TdP'] >= exp_start_t])

    qg_history_hyp = np.array(dca_data['qg_ef'][dca_data['TdP'] < exp_start_t])
    qg_history_exp = np.array(dca_data['qg_ef'][dca_data['TdP'] >= exp_start_t])

    cumg_history_hyp = np.array(dca_data['Acu_Gas'][dca_data['TdP'] < exp_start_t])
    cumg_history_exp = np.array(dca_data['Acu_Gas'][dca_data['TdP'] >= exp_start_t])

    #----------------------------------------
    # Hyperbolic section
    #----------------------------------------
    # Normalize dca data
    cum_aux = cumg_history_hyp - cumi
    q_aux = qg_history_hyp
    cum_norm, q_norm = normalize_data(cum_aux, q_aux, cumi, qi)

    # Curve fitting
    qi, di, b = fit_model(hyperbolic, cum_norm, q_norm,
        ((0, 0, 0), (np.inf, np.inf, 1.2)))

    # De-normalize dca data
    qi, di = qi * q_max, di / cum_max

    # Create cumulatives and times arrays
    last_t, last_cum = dca_data['TdP'].iloc[-1], dca_data['Acu_Gas'].iloc[-1]
    t_forecast_hyp, cumg_forecast_hyp = calc_t_and_cum_arrays(last_t, last_cum,
        'HYP', exp_start_t, cumi, qi, di, b)
    
    # Decline hyperbolic section
    qg_forecast_hyp = hyperbolic(cumg_forecast_hyp - cumi, qi, di, b)

    if dca_model == 'HYP':
        # Store rates and cumulatives forecast
        well['t_forecast'] = np.array(t_forecast_hyp, dtype='float64')
        well['qg_forecast'] = np.array(qg_forecast_hyp, dtype='float64')
        well['cumg_forecast'] = np.array(cumg_forecast_hyp, dtype='float64')

        # Store forecast params
        well['b'] = f'{b:.4f}' if b else 'None'
        well['d_hyp'] = f'{di * 365.25 * 100:.4f}' if di else 'None'
        well['d_exp'] = 'None'
        well['dca_model'] = dca_model

        return copy.deepcopy(well)

    #----------------------------------------
    # Exponential section
    #----------------------------------------
    if len(qg_forecast_hyp) > 1:
        # Calculate di_exp
        last_q_hyp = qg_forecast_hyp[-1]
        last_cum_hyp = cumg_forecast_hyp[-1]
        last_t_hyp = t_forecast_hyp[-1]
        prev_last_q_hyp = qg_forecast_hyp[-2]
        prev_last_cum_hyp = cumg_forecast_hyp[-2]
        di_exp = -(last_q_hyp - prev_last_q_hyp) / (last_q_hyp * 
            (last_cum_hyp - prev_last_cum_hyp))

        # Create cumulatives and times arrays
        t_forecast_exp, cumg_forecast_exp = calc_t_and_cum_arrays(last_t_hyp,
            last_cum_hyp, dca_model, end_time_days, last_cum_hyp, last_q_hyp,
            di_exp, 0)

        # Decline exponential section
        qg_forecast_exp = exponential(cumg_forecast_exp - last_cum_hyp,
            last_q_hyp, di_exp)
    else:
        # Normalize dca data
        if len(cumg_history_exp):
            cum_aux = cumg_history_exp #- cumi
        else:
            cum_aux = np.array([])

        q_aux = qg_history_exp
        cum_norm, q_norm = normalize_data(cum_aux, q_aux, cumi, qi)

        # Curve fitting
        qi, di_exp = fit_model(exponential, cum_norm, q_norm, ((0, 0), (np.inf, np.inf)))

        # De-normalize dca data
        qi, di_exp = qi * q_max, di_exp / cum_max

        # Create cumulatives and times arrays
        last_t, last_cum = dca_data['TdP'].iloc[-1], dca_data['Acu_Gas'].iloc[-1]
        t_forecast_exp, cumg_forecast_exp = calc_t_and_cum_arrays(last_t, last_cum,
            'EXP', end_time_days, cumi, qi, di, b)

        # Decline exponential section
        qg_forecast_exp = exponential(cumg_forecast_exp, qi, di_exp)

    # Store rates forecast
    well['t_forecast'] = np.append(t_forecast_hyp[:-1], t_forecast_exp).astype('float64')
    well['qg_forecast'] = np.append(qg_forecast_hyp[:-1], qg_forecast_exp).astype('float64')
    well['cumg_forecast'] = np.append(cumg_forecast_hyp[:-1], cumg_forecast_exp).astype('float64')

    # Store forecast params
    well['b'] = f'{b:.4f}' if b else 'None'
    well['d_hyp'] = f'{di * 365.25 * 100:.4f}' if di else 'None'
    well['d_exp'] = f'{di_exp * 365.25 * 100:.4f}' if di_exp else 'None'
    well['dca_model'] = dca_model

    return copy.deepcopy(well)


def dca_HM_by_t_manual(dca_model, exp_start_t, end_time, qi, ti, b, d):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    # Get parameters for DCA
    di = d / 100 / 365
    end_time_days = round(end_time * 365.25)
    
    if dca_model == 'HYP': exp_start_t = end_time_days

    # If end_time < ti, return empty
    if end_time_days < ti:
        return (np.array([], dtype='float64'), np.array([], dtype='float64'),
            (None, None, None))

    #----------------------------------------
    # Hyperbolic section
    #----------------------------------------
    # Calculate times
    t_forecast_hyp = np.arange(0, exp_start_t - ti, 30.44).astype('float64')

    # Decline hyperbolic section
    q_forecast_hyp = np.array(hyperbolic(t_forecast_hyp, qi, di, b), dtype='float64')

    if dca_model == 'HYP':
        return t_forecast_hyp + ti, q_forecast_hyp, (b, di * 365, None)
    
    #----------------------------------------
    # Exponential section
    #----------------------------------------
    if len(q_forecast_hyp) > 1:
        # Calculate di_exp
        last_q_hyp = q_forecast_hyp[-1]
        last_t_hyp = t_forecast_hyp[-1]
        prev_last_q_hyp = q_forecast_hyp[-2]
        prev_last_t_hyp = t_forecast_hyp[-2]
        di_exp = -(last_q_hyp - prev_last_q_hyp) / (last_q_hyp * (last_t_hyp - prev_last_t_hyp))

        # Calculate times and rates
        t_forecast_exp = np.arange(last_t_hyp + 30.44, end_time_days - ti, 30.44).astype('float64')
        q_forecast_exp = exponential(t_forecast_exp - last_t_hyp, last_q_hyp, di_exp).astype('float64')
    else:
        t_forecast_exp, q_forecast_exp = np.array([], dtype='float64'), np.array([], dtype='float64')
        di_exp = None

    return (np.append(t_forecast_hyp, t_forecast_exp) + ti,
        np.append(q_forecast_hyp, q_forecast_exp),
        (b, di * 365, di_exp * 365))


def oil_dca_HM_by_d(well, dca_model, exp_start_d, end_time):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    # Assert exp_start_d
    if exp_start_d is None: exp_start_d = 1

    # Get parameters for DCA
    dca_data, _, _, _ = get_dca_params(well['well_data'], 'oil')

    # If well has 1 data, return empty
    if len(dca_data) <= 1:
        well['t_forecast'] = np.array([], dtype='float64')
        well['qo_forecast'] = np.array([], dtype='float64')
        well['b'] = 'None'
        well['d_hyp'] = 'None'
        well['d_exp'] = 'None'
        well['dca_model'] = dca_model

        return copy.deepcopy(well)

    # Hyperbolic decline to find tlim
    well_hyp = well.copy()
    well_hyp = oil_dca_HM_by_t(well, 'HYP', 0, end_time)
    d_calc = np.array(np.diff(well_hyp['qo_forecast']) / 
        np.diff(well_hyp['t_forecast'])) / (-well_hyp['qo_forecast'][1:]) * 365
    tlim_pos = np.argmax(d_calc < (exp_start_d / 100))
    if not tlim_pos: tlim_pos = 1
    tlim = well_hyp['t_forecast'][tlim_pos]

    return oil_dca_HM_by_t(well, dca_model, tlim, end_time)


def dca_HM_by_d_manual(dca_model, exp_start_d, end_time, qi, ti, b, d):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    # Assert exp_start_d
    if exp_start_d is None: exp_start_d = 1

    # Hyperbolic decline to find tlim
    t_hyp, qo_hyp, _ = dca_HM_by_t_manual('HYP', 0, end_time, qi, ti, b, d)
    d_calc = np.array(np.diff(qo_hyp) / np.diff(t_hyp)) / (-qo_hyp[1:])*365
    tlim_pos = np.argmax(d_calc < (exp_start_d / 100))
    if not tlim_pos: tlim_pos = 1
    tlim = t_hyp[tlim_pos]

    return dca_HM_by_t_manual(dca_model, tlim, end_time, qi, ti, b, d)
    
    
def oil_dca(well, dca_model, exp_start_method, exp_start_input, end_time):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    if exp_start_method == 'EXP_START_TIME' or dca_model == 'HYP':
        return oil_dca_HM_by_t(well, dca_model, exp_start_input, end_time)
    else:
        return oil_dca_HM_by_d(well, dca_model, exp_start_input, end_time)


def gas_dca(well, dca_model, exp_start_input, end_time):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    return gas_dca_HM_by_t(well, dca_model, exp_start_input, end_time)


def oil_dca_manual(dca_model, exp_start_method, exp_start_input, end_time, qi,
    ti, b, d):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    if exp_start_method == 'EXP_START_TIME' or dca_model == 'HYP':
        t_forecast, q_forecast, params = dca_HM_by_t_manual(dca_model, exp_start_input, end_time, qi, ti, b, d)
    else:
        t_forecast, q_forecast, params = dca_HM_by_d_manual(dca_model, exp_start_input, end_time, qi, ti, b, d)
    
    # Append incline segment to forecast
    t_to_append = np.arange(0, ti, 30.44).astype('float64')
    q_to_append = np.interp(t_to_append, [0, ti], [0, qi]).astype('float64')
    t_forecast = np.append(t_to_append, t_forecast).astype('float64')
    q_forecast = np.append(q_to_append, q_forecast).astype('float64')

    return t_forecast, q_forecast, params


def apply_dca_offset(well, fluid):
    '''
    Apply oil/gas rate offset over decline to match last data point.

    Params:
        - well
        - fluid
    
    Returns:
        - well

    TODO: COMPLETAR DOCSTRING
    '''

    if len(well['t_forecast']):
        if fluid == 'oil':
            # Get parameters for DCA
            dca_data, _, _, _ = get_dca_params(well['well_data'], fluid)

            # Find forecasted rate for last historical point
            pos = np.where(well['t_forecast'].astype(int) == int(dca_data['TdP'].iloc[-1]))[0][0]

            # Apply offset
            well['qo_forecast'] *= dca_data['qo_ef'].iloc[-1] / well['qo_forecast'][pos]

        elif fluid == 'gas':
            t_forecast = copy.deepcopy(well['t_forecast'])
            qg_forecast = copy.deepcopy(well['qg_forecast'])
            cumg_forecast = copy.deepcopy(well['cumg_forecast'])
            
            last_q = well['well_data']['qg_ef'].iloc[-1]
            last_cum = np.around(well['well_data']['Acu_Gas'].iloc[-1], decimals=2)

            try:
                index_offset = list(cumg_forecast >= last_cum).index(True)
                forecasted_q = copy.deepcopy(qg_forecast[index_offset])

                # Apply offset
                qg_forecast[index_offset:] *= last_q/forecasted_q

                # Recalculate times
                for i in range(index_offset, len(t_forecast) - 1):
                    t_forecast[i+1] = t_forecast[i] + (
                        cumg_forecast[i+1] - cumg_forecast[i])/qg_forecast[i+1]

                # Interpolate values to make equispaced array of times
                well['qg_forecast'][index_offset:] = np.interp(
                    well['t_forecast'][index_offset:], t_forecast[index_offset:],
                    qg_forecast[index_offset:]).astype('float64')
                well['cumg_forecast'][index_offset:] = np.interp(
                    well['t_forecast'][index_offset:], t_forecast[index_offset:],
                    cumg_forecast[index_offset:]).astype('float64')
            except:
                pass

    return copy.deepcopy(well)


def cumulative(well, fluid):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    if fluid == 'oil':
        q_forecast = 'qo_forecast'
        cum_history = 'Acu_Pet'
        cum_forecast = 'cumo_forecast'
    elif fluid == 'gas':
        q_forecast = 'qg_forecast'
        cum_history = 'Acu_Gas'
        cum_forecast = 'cumg_forecast'

    # If well has no forecast, return empty cumulative
    if not len(well[q_forecast]):
        well[cum_forecast] = np.array([], dtype='float64')
        return copy.deepcopy(well)

    # Accumulate
    try:
        last_cum_history = well['well_data'][cum_history].iloc[-1]
    except:
        last_cum_history = [0]
    acum_forecast = np.add.accumulate(np.append(last_cum_history,
        np.multiply(np.diff(well['t_forecast']), well[q_forecast][1:])))

    # Store cumulatives
    well[cum_forecast] = acum_forecast.astype('float64')

    return copy.deepcopy(well)


def trim_curve(well, end_time, q_lim, fluid):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    t_history = well['well_data']['TdP'].values
    end_time_days = round(end_time * 365.25)

    t_curve = well['t_forecast']

    if fluid == 'oil':
        q_curve, cum_curve = well['qo_forecast'], None
    elif fluid == 'gas':
        q_curve, cum_curve = well['qg_forecast'], well['cumg_forecast']

    # Trim by times
    mask = (t_history[-1] <= t_curve) & (t_curve < end_time_days)
    t_curve = t_curve[mask]
    q_curve = q_curve[mask]
    if cum_curve is not None: cum_curve = cum_curve[mask]

    # Trim by rates
    mask = q_curve.copy() < q_lim
    q_curve[mask] = 0
    if cum_curve is not None and mask.any():
        pos = np.where(mask)[0][0] - 1
        if pos >= 0:
            # Last valid cumulative from forecast
            cum_constant_val = cum_curve[pos]
        else:
            # Last cumulative from history
            if fluid == 'gas':
                cum_constant_val = well['well_data']['Acu_Gas'].iloc[-1]
            elif fluid == 'oil':
                cum_constant_val = well['well_data']['Acu_Pet'].iloc[-1]

        cum_curve[mask] = cum_constant_val

    # Store forecasts
    well['t_forecast'] = np.array(t_curve, dtype='float64')
    if fluid == 'oil':
        well['qo_forecast'] = np.array(q_curve, dtype='float64')
    elif fluid == 'gas':
        well['qg_forecast'] = np.array(q_curve, dtype='float64')
        well['cumg_forecast'] = np.array(cum_curve, dtype='float64')

    return copy.deepcopy(well)


def add_fig_trace(i, fig, well, trace, trace_type, params=True):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    colors = px.colors.qualitative.Plotly
    i %= len(colors)

    if trace_type == 'history':
        if 'v_Gp' in trace:
            x = well['well_data']['Acu_Gas']
        elif 'v_Np' in trace:
            x = well['well_data']['Acu_Pet']
        else:
            x = well['well_data']['TdP']

        if trace == 'qo':
            # qo history
            y = well['well_data']['qo_ef']
            hovertemplate = 'qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'

        elif trace == 'cumo':
            # cumo history
            y = well['well_data']['Acu_Pet']
            hovertemplate = 'Np = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'

        elif trace == 'GOR_v_Np':
            # GOR history
            GOR_col = [x for x in well['well_data'].columns if x.startswith('GOR')][0]
            y = well['well_data'][GOR_col]
            hovertemplate = 'GOR = %{y:,.0f}'+'<br>Np = %{x:,.0f}'

        elif trace == 'GOR_v_Gp':
            # GOR history
            GOR_col = [x for x in well['well_data'].columns if x.startswith('GOR')][0]
            y = well['well_data'][GOR_col]
            hovertemplate = 'GOR = %{y:,.0f}'+'<br>Gp = %{x:,.0f}'
        
        elif trace == 'GOR_v_tdp':
            # GOR history
            GOR_col = [x for x in well['well_data'].columns if x.startswith('GOR')][0]
            y = well['well_data'][GOR_col]
            hovertemplate = 'GOR = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        
        elif trace == 'qg':
            # qo history
            y = well['well_data']['qg_ef']
            hovertemplate = 'qg = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'

        elif trace == 'cumg':
            # cumo history
            y = well['well_data']['Acu_Gas']
            hovertemplate = 'Gp = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'

        elif trace == 'qg_v_Gp':
            # qg history
            y = well['well_data']['qg_ef']
            hovertemplate = 'qg = %{y:,.0f}'+'<br>Gp = %{x:,.0f}'
        
        line = dict(color=colors[i], width=1)
        mode = 'lines+markers'
        name = well['wellname']

    elif trace_type == 'forecast':
        if 'v_Gp' in trace:
            x = well['cumg_forecast']
        elif 'v_Np' in trace:
            x = well['cumo_forecast']
        else:
            x = well['t_forecast']

        if trace == 'qo':
            # qo forecast
            y = well['qo_forecast']
            if params:
                hovertemplate = (
                    'qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'+
                        '<br>'.join((
                        '',
                        f'<b>b</b>: {well["b"]}',
                        f'<b>d_hyp [% 1/yr]</b>: {well["d_hyp"]}',
                        f'<b>d_exp [% 1/yr]</b>: {well["d_exp"]}'
                    ))
                )
            else:
                hovertemplate = ('qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}')

        elif trace == 'cumo':
            # cumo forecast
            y = well['cumo_forecast']
            hovertemplate = 'Np = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        
        elif trace == 'GOR_v_Np':
            # GOR forecast
            if 'Manual' not in well['wellname']:
                x = np.append(well['well_data']['Acu_Pet'], x[1:])
            y = well['GOR_forecast']
            hovertemplate = 'GOR = %{y:,.0f}'+'<br>Np = %{x:,.0f}'
            
        elif trace == 'GOR_v_tdp':
            # GOR forecast
            if 'Manual' not in well['wellname']:
                x = np.append(well['well_data']['TdP'], x[1:])
            y = well['GOR_forecast']
            hovertemplate = 'GOR = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'

        elif trace == 'GOR_v_Gp':
            # GOR forecast
            if 'Manual' not in well['wellname']:
                x = np.append(well['well_data']['TdP'], x[1:])
            y = well['GOR_forecast']
            hovertemplate = 'GOR = %{y:,.0f}'+'<br>Gp = %{x:,.0f}'

        elif trace == 'qg':
            # qg forecast
            y = well['qg_forecast']
            hovertemplate = 'qg = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        
        elif trace == 'cumg':
            # cumg forecast
            y = well['cumg_forecast']
            hovertemplate = 'Gp = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'

        elif trace == 'qg_v_Gp':
            # qg forecast
            y = well['qg_forecast']
            hovertemplate = 'qg = %{y:,.0f}'+'<br>Gp = %{x:,.0f}'

        mode = 'lines'
        line = dict(color=colors[i], width = 1, dash = 'dash')
        name = well['wellname'] + '_forecast'

    fig.add_trace(
        go.Scatter(
            x = x,
            y = y,
            mode = mode,
            line = line,
            name = name,
            hovertemplate = hovertemplate
        )
    )


def serialize_forecast(wells):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    for well in wells:
        wells[well]['well_data'] = wells[well]['well_data'].to_json()
        
        try:
            wells[well]['t_forecast'] = wells[well]['t_forecast'].tolist()
            wells[well]['qo_forecast'] = wells[well]['qo_forecast'].tolist()
            wells[well]['cumo_forecast'] = wells[well]['cumo_forecast'].tolist()
            wells[well]['GOR_forecast'] = wells[well]['GOR_forecast'].tolist()
            wells[well]['qg_forecast'] = wells[well]['qg_forecast'].tolist()
            wells[well]['cumg_forecast'] = wells[well]['cumg_forecast'].tolist()
        except:
            wells[well]['t_forecast'] = None
            wells[well]['qo_forecast'] = None
            wells[well]['cumo_forecast'] = None
            wells[well]['GOR_forecast'] = None
            wells[well]['qg_forecast'] = None
            wells[well]['cumg_forecast'] = None

    return json.dumps(wells)


def replace_outliers(data):
    '''
    Replaces outliers with nan.
    
    Params:
        data:

    Returns:
        data:
    '''
    # Set upper and lower limit to 1.25 standard deviation
    data_std = np.nanstd(data)
    data_mean = np.nanmean(data)
    lower_limit  = data_mean - (data_std * 1.25)
    upper_limit = data_mean + (data_std * 1.25)

    # Replace outliers
    for i, item in enumerate(data):
        if item > upper_limit or item < lower_limit:
            data[i] = np.nan

    return data


def get_Gp_EUR_dew(well):
    '''
    Retrieve Gp/EUR at dewpoint depending on field.
    If the field has no Gp/EUR at dewpoint, returns 0.18.

    Params:
        well:

    Returns:
        Gp_EUR_dew:
    '''

    Gp_EUR_dew_by_field = {
        'RINCON LA CENIZA': 0.074747547,
        'LA CALERA': 0.095730339,
        'LA RIBERA BLOQUE I': 0.069230787,
        'FORTIN DE PIEDRA': 0.01,
        'AGUADA DE LA ARENA': 0.185075339,
        }

    field = well['well_data']['areayacimiento'].iloc[-1]

    return Gp_EUR_dew_by_field.get(field, 0.18)
    

def reciprocal_quadratic(x, a, b, c):
    '''
    Equation for reciprocal quadratic.
    
    Params:
        x:
        a:
        b:
        c:
    
    Returns:
        calc:
    '''
    return x/(a + b * x + c * x**2)


def GOR_forecast_gas(well: dict):
    '''
    Forecast GOR for a gas well. TODO: COMPLETAR DOCSTRING
    
    Params:
        well(dict): contains relevant data about a well

    Returns:
        well(dict):
    '''

    # If well has no forecasts, return empty GOR
    if not well['t_forecast'].size:
        well['GOR_forecast'] = np.array([], dtype='float64')
        well['GORi'] = 'None'
        well['GOR_a'] = 'None'
        return copy.deepcopy(well)

    # If fluid is dry gas, return infinite GOR
    if well['well_data']['Fluido_gor'].iloc[-1] == 'GS':
        well['GOR_forecast'] = np.full(len(well['well_data']['GOR_ef'])
            + len(well['t_forecast']), 1_000_000)
        well['GORi'] = 'None'
        well['GOR_max'] = 'None'
        return copy.deepcopy(well)

    # Replace zero historical GOR with NaN
    well['well_data']['GOR_ef'].iloc[1:].replace(to_replace=0, value=np.nan, inplace=True)

    # If fluid is wet gas, return constant GOR
    if well['well_data']['Fluido_gor'].iloc[-1] == 'GH':
        # Fit horizontal line with GOR history data
        GOR_history_aux = replace_outliers(
            copy.deepcopy(well['well_data']['GOR_ef'].iloc[2:]))

        if len(well['well_data']['GOR_ef']) > 2:
            GORi = np.nanmean(well['well_data']['GOR_ef'].iloc[2:]) 
        else:
            GORi = 1_000_000
        
        # Replace zero historical GOR NaN with zero
        well['well_data']['GOR_ef'].iloc[1:].replace(to_replace=np.nan, value=0, inplace=True)
        
        well['GOR_forecast'] = np.full(len(well['well_data']['GOR_ef'])
            + len(well['t_forecast']), GORi).astype('float64')
        well['GORi'] = GORi
        well['GOR_max'] = well['GOR_forecast'].max()
        return copy.deepcopy(well)

    EUR = well['cumg_forecast'][-1]

    # Get Gp/EUR at Dew
    Gp_EUR_dew = get_Gp_EUR_dew(well)
    
    # Determine if well has historical data beyond Dew
    if len(np.where(well['well_data']['Acu_Gas']/EUR > Gp_EUR_dew)[0]):
        # Find Dew position into cumg_history
        try:
            dew_pos = np.where(
                well['well_data']['Acu_Gas']/EUR <= Gp_EUR_dew)[0][-1] + 1
        except:
            dew_pos = 0

        # Fit horizontal line with GOR history data (discard outliers)
        GOR_history_aux = replace_outliers(
            copy.deepcopy(well['well_data']['GOR_ef'].iloc[1:dew_pos]))
        GORi = np.nanmean(GOR_history_aux)
        if np.isnan(GORi): GORi = well['well_data']['GOR_ef'].iloc[0]
        if GORi > 15_000: GORi = 15_000

        GOR_until_dew = np.full(dew_pos, GORi)

        # Forecast final GOR curve
        Gp_EUR_after_dew = np.append(well['well_data']['Acu_Gas'][dew_pos:] / EUR,
            well['cumg_forecast'] / EUR)

        Gp_EUR_to_fit = well['well_data']['Acu_Gas'][dew_pos:]/EUR
        GOR_to_fit = well['well_data']['GOR_ef'].iloc[dew_pos:]/1000
        
        MAXFEV = 5000
        try:
            valid = ~(np.isnan(Gp_EUR_to_fit) | np.isnan(GOR_to_fit)) 
            popt, _ = curve_fit(reciprocal_quadratic, Gp_EUR_to_fit[valid],
                GOR_to_fit[valid], maxfev=int(MAXFEV), bounds=((0,-np.inf,0),
                (np.inf,0,np.inf)))
            popt /= 1000
        except:
            popt = (2.46e-05, -4.63e-05, 3.11e-04) # EN UN FUTURO HABRIA QUE PONER PARAMETROS DE POZOS SIMILARES
        
        GOR_after_dew = reciprocal_quadratic(Gp_EUR_after_dew, popt[0], popt[1],
            popt[2])
    else:
        # Find dew position into cumg_forecast
        dew_pos = np.where(well['cumg_forecast']/EUR <= Gp_EUR_dew)[0][-1] + 1

        # Fit horizontal line with GOR history data (discard first 30 days)
        GORi = np.nanmean(well['well_data']['GOR_ef'].iloc[1:])
        if np.isnan(GORi): GORi = well['well_data']['GOR_ef'].iloc[0]
        if GORi > 15_000: GORi = 15_000
        
        GOR_until_dew = np.full(len(well['well_data']['GOR_ef']) + dew_pos, GORi)

        # Forecast final GOR curve
        Gp_EUR_after_dew = well['cumg_forecast'][dew_pos:]/EUR
        
        popt = (2.46e-05, -4.63e-05, 3.11e-04) # EN UN FUTURO HABRIA QUE PONER PARAMETROS DE POZOS SIMILARES
            
        GOR_after_dew = reciprocal_quadratic(Gp_EUR_after_dew, popt[0], popt[1],
            popt[2])

    # Replace negatives GOR with zero
    GOR_after_dew[GOR_after_dew < 0] = 0

    # Correct final curve shape
    max_pos = np.nanargmax(GOR_after_dew)
    
    if well['well_data']['GOR_ef'].iloc[-1] < GORi:
        GOR_terminal = well['well_data']['GOR_ef'].iloc[-1]
    else:
        GOR_terminal = np.mean([GORi, well['well_data']['GOR_ef'].iloc[-1]])

    shrink_range = GOR_after_dew[max_pos] - GOR_terminal
    
    GOR_after_dew_normalized = ((GOR_after_dew[max_pos:] - GOR_after_dew[-1]) /
        (GOR_after_dew[max_pos] - GOR_after_dew[-1]))

    GOR_after_dew[max_pos:] = GOR_terminal + shrink_range * GOR_after_dew_normalized

    # Replace zero historical GOR NaN with zero
    well['well_data']['GOR_ef'].replace(to_replace=np.nan, value=0, inplace=True)

    well['GOR_forecast'] = np.append(GOR_until_dew, GOR_after_dew).astype('float64')
    well['GORi'] = GORi
    well['GOR_max'] = well['GOR_forecast'].max()

    return copy.deepcopy(well)


def GOR_forecast_oil(well: dict):
    '''
    Forecast GOR based on historical data, ML model (to find NP_Pb) and equation
    from SPE-197096-MS.

    Params:
        well(dict): contains relevant data about a well

    Returns:
        well(dict): contains relevant data about a well
    '''

    lateral_len = well['well_data']['Rama'].iloc[-1]
    qo_peak = well['well_data']['qo_ef_peak'].iloc[-1]
    if well['t_forecast'].size:
        last_t = well['t_forecast'][-1]
    else:
        well['GOR_forecast'] = np.array([], dtype='float64')
        well['GORi'] = 'None'
        well['GOR_a'] = 'None'
        return copy.deepcopy(well)

    #Replace zero historical GOR with NaN
    well['well_data']['GOR_ef'].iloc[1:].replace(to_replace=0, value=np.nan, inplace=True)

    #Get Np at Pb
    Np_Pb = calculate_Np_Pb(lateral_len, qo_peak, well['cumo_forecast'][-1])

    #Definition of aux GOR function
    GOR_aux = lambda t, a: GOR(t, a, GORi, GORi * 5, last_t)

    #Determine if well has historical data beyond Np_Pb
    if len(np.where(well['well_data']['Acu_Pet'] > Np_Pb)[0]) > 0:
        #Find Pb position into cumo history
        try:
            Pb_pos = np.where(well['well_data']['Acu_Pet'] <= Np_Pb)[0][-1] + 1
        except:
            Pb_pos = 0

        #Fit horizontal line with GOR history data (discard first 60 days)
        GORi = np.nanmean(well['well_data']['GOR_ef'].iloc[2:int(Pb_pos*2/3)])
        GOR_until_Pb = np.full(Pb_pos, GORi)

        #Forecast final GOR curve
        times_after_Pb = np.append(well['well_data']['TdP'][Pb_pos:], well['t_forecast'])
        
        times_to_fit = well['well_data']['TdP'].iloc[Pb_pos:] - well['well_data']['TdP'].iloc[Pb_pos]
        GOR_to_fit = well['well_data']['GOR_ef'].iloc[Pb_pos:]
        MAXFEV = 2000
        try:
            valid = ~(np.isnan(times_to_fit) | np.isnan(GOR_to_fit))
            popt, _ = curve_fit(GOR_aux, times_to_fit[valid], GOR_to_fit[valid], 
                maxfev=int(MAXFEV), bounds=(0, 0.003), p0=0.001)
            GOR_a = popt[0]
        except:
            GOR_a = 0.002
        GOR_after_Pb = GOR_aux(times_after_Pb - times_after_Pb[0], GOR_a)
    else:
        # #Find Pb position into cumo_history
        Pb_pos = np.where(well['cumo_forecast'] <= Np_Pb)[0][-1] + 1

        #Fit horizontal line with GOR history data (discard first 60 days)
        GORi = np.nanmean(well['well_data']['GOR_ef'].iloc[2:])
        GOR_a = 0.002
        GOR_until_Pb = np.full(len(well['well_data']['GOR_ef']) + Pb_pos, GORi)

        #Forecast final curve
        if Pb_pos != len(well['t_forecast']):
            times_after_Pb = well['t_forecast'][Pb_pos:]
            GOR_after_Pb = GOR_aux(times_after_Pb - times_after_Pb[0], GOR_a)
        else:
            GOR_after_Pb = []

    # Replace zero historical GOR NaN with zero
    well['well_data']['GOR_ef'].iloc[1:].replace(to_replace=np.nan, value=0, inplace=True)

    well['GOR_forecast'] = np.append(GOR_until_Pb, GOR_after_Pb).astype('float64')
    well['GORi'] = str(GORi)
    well['GOR_a'] = str(GOR_a)

    return copy.deepcopy(well)


def GOR_forecast(well: dict, fluid):
    '''
    Forecast GOR depending on fluid

    Params:
        well (dict): contains relevant data about a well
        fluid (str): main fluid

    Returns:
        well(dict): contains relevant data about a well
    '''

    if fluid == 'oil':
        return GOR_forecast_oil(well)
    elif fluid == 'gas':
        return GOR_forecast_gas(well)


def GOR_manual_forecast(well: dict, GORi, Np_Pb, GORmax, Np_GORmax, GORf,
    Np_GORf, GOR_a):
    '''
    Forecast GOR based on equation from SPE-197096-MS.

    Params:
        well(dict): contains relevant data about a well

    Returns:

    '''

    # Well main fluid is oil or gas?
    try:
        # Supose is oil
        cum_forecast = well['cumo_forecast']   # If fails, main fluid is gas
        cum_history = well['well_data']['Acu_Pet']
    except:
        # Then is gas
        cum_forecast = well['cumg_forecast']
        cum_history = well['well_data']['Acu_Gas']

    # Assert forecasts size
    if not len(well['t_forecast']):
        well['GOR_forecast'] = np.full_like(cum_history, GORi).astype('float64')
        well['GORi'] = 'None'
        well['GOR_a'] = 'None'

        return copy.deepcopy(well)

    if 'Manual' in well['wellname']:
        t_aux = well['t_forecast']
        cum_aux = cum_forecast
        GOR_aux = np.full_like(cum_aux, GORi)
    else:
        t_aux = np.append(well['well_data']['TdP'], well['t_forecast']).astype('float64')
        cum_aux = np.append(cum_history, cum_forecast).astype('float64')
        GOR_aux = np.full_like(cum_aux, GORi).astype('float64')

    # Assert inputs
    if (Np_GORmax < Np_Pb) or (GORmax < GORi) or (cum_aux[-1] < Np_Pb):
        well['GOR_forecast'] = GOR_aux
        well['GORi'] = 'None'
        well['GOR_a'] = 'None'

        return copy.deepcopy(well)

    # GOR from Pb to GOR max
    GOR1_func = lambda t: GOR_manual(t, GOR_a, GORi, GORmax)
    GOR1_aux = np.array(list(map(GOR1_func, t_aux)))
    
    # Scale y and x
    y1_scale = lambda GOR: scale_to_range(GOR, np.amin(GOR1_aux),
        np.amax(GOR1_aux), GORi, GORmax)
    
    x1_scale = lambda cum: scale_to_range(cum, np.amin(cum_aux),
        np.amax(cum_aux), Np_Pb, Np_GORmax)
    
    GOR1 = np.array(list(map(y1_scale, GOR1_aux)))
    cum1 = np.array(list(map(x1_scale, cum_aux)))

    # Interpolate values to match forecasted data
    mask = (cum_aux > Np_Pb) & (cum_aux <= Np_GORmax)
    GOR_aux[mask] = np.interp(cum_aux[mask], cum1, GOR1)
    max_value = GOR_aux[mask][-1] if mask.any() else GORmax

    # GOR after GOR max
    mask = (cum_aux > Np_GORmax) & (cum_aux < Np_GORf)
    GOR_aux[mask] = np.interp(cum_aux[mask], [Np_GORmax, Np_GORf], [max_value, GORf])

    mask = (cum_aux >= Np_GORf)
    GOR_aux[mask] = GORf

    well['GOR_forecast'] = GOR_aux.astype('float64')
    well['GORi'] = str(GORi)
    well['GOR_a'] = str(GOR_a)

    return copy.deepcopy(well)


def calculate_Np_Pb(lateral_len, qo_peak, EUR):
    '''
    Calculates Np at bubble point, using coefficients provided by linear
    regression model.
    
    Params:
        well:
    
    Returns:
        np_pb(float):
    '''
    
    if np.nan_to_num(lateral_len):
        #Coefficients provided by linear regression
        return 13.76946405 * lateral_len + 85.10611085 * qo_peak
    else:
        # TODO: MEJORAR ESTA CORRELACION
        np_pb = (-0.0027 * qo_peak + 0.6183) * EUR
        return np_pb if np_pb > 0 else 0


def GOR(t, a, GORi, GORf, last_t):
    '''
    Modified equation from SPE-197096-MS for forecasting GOR vs time.

    Params:
        a(float): parameter that controls the slope of the curvature at inflection
        t(float):
        GORi:
        GORf:
        last_t:
    
    Returns:
        GOR(float):
    '''

    try:
        return GORf * (GORi / GORf)**(e**(-a * t))*(last_t - t)/last_t
    except:
        return 0


def GOR_manual(t, a, GORi, GORf):
    '''
    Modified equation from SPE-197096-MS for forecasting GOR vs time.

    Params:
        a(float): parameter that controls the slope of the curvature at inflection
        t(float):
        GORi:
        GORf:
        last_t:
    
    Returns:
        GOR(float):
    '''

    try:
        return GORf * (GORi / GORf)**(e**(-a * t))
    except:
        return 0


def gas_forecast(well: dict):
    '''
    Multiplies forecasted qo and GOR to calculate qg.

    Params:
        well(dict): contains relevant data about a well

    Returns:

    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    if well['GOR_forecast'].size:
        try:
            pos = len(well['well_data']['TdP'])
            if 'Manual' in well['wellname']: pos -= 1
        except:
            pos = 0

        well['qg_forecast'] = (np.multiply(well['qo_forecast'], 
            well['GOR_forecast'][pos:]) / 1000).astype('float64')

    else:
        well['qg_forecast'] = np.full(len(well['t_forecast']), 0).astype('float64')

    return copy.deepcopy(well)
    

def oil_forecast(well: dict):
    '''
    Divides forecasted qg by GOR to calculate qo.
    
    Params:
        well(dict): contains relevant data about a well

    Returns:
        well(dict):

    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    if well['GOR_forecast'].size:
        try:
            pos = len(well['well_data']['TdP'])
        except:
            pos = 0

        well['qo_forecast'] = np.nan_to_num(np.divide(well['qg_forecast'],
            well['GOR_forecast'][pos:]) * 1000).astype('float64')
    else:
        well['qo_forecast'] = np.full(len(well['t_forecast']), 0).astype('float64')

    return copy.deepcopy(well)


def get_params_from_forecast_ID(forecast_id):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    return forecast_id.split('_')


def compress_forecast_mask(well):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    t_forecast = np.array(well['t_forecast'])
    qo_forecast = np.array(well['qo_forecast'])
    qg_forecast = np.array(well['qg_forecast'])

    mask = np.diff((t_forecast/365).astype(int)) == 1
    mask = np.append(mask, True) # Append last element
    
    # Force first element
    mask[0] = True 

    # Force qo_peak
    qo_peak_index = np.argmax(qo_forecast)
    mask[qo_peak_index] = True

    # Force qg_peak
    qg_peak_index = np.argmax(qg_forecast)
    mask[qg_peak_index] = True

    # Force 180 days element
    if (t_forecast < 180).any():
        d180_index = np.where(t_forecast < 180)[0][-1]
        mask[d180_index] = True

    return mask


def normalize_by_fracs(well, method, norm_value):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    # Get well data
    t_history = well['well_data']['TdP'].values
    qo_history = well['well_data']['qo_ef'].values
    cumo_history = well['well_data']['Acu_Pet'].values
    qg_history = well['well_data']['qg_ef'].values
    cumg_history = well['well_data']['Acu_Gas'].values

    if 'stages' in method:
        well_fracs = well['well_data']['Fracturas']
        valid = True if well_fracs.to_numpy()[-1] > 10 else False # Well has to have more than 10 frac stages
    elif 'latlen' in method:
        well_fracs = well['well_data']['Rama']
        valid = True if well_fracs.to_numpy()[-1] > 100 else False # Well has to have more than 100 lat len
    
    # If well has fracs and last value > 0, recalulate rates and cumulatives
    if valid and well_fracs.notna().all():
        qo_history = qo_history.copy() * (norm_value / well_fracs.values)

        cumo_history = np.add.accumulate(
            np.append(
                t_history[0] * qo_history[0],
                np.multiply(np.diff(t_history), qo_history[1:])))

        qg_history = qg_history.copy() * (norm_value / well_fracs.values)

        cumg_history = np.add.accumulate(
            np.append(
                t_history[0] * qg_history[0],
                np.multiply(np.diff(t_history), qg_history[1:])))

        # Store normalization method
        well['normalization']['enabled'] = True
        well['normalization'][method] = norm_value

    # Store normalized rates and cumulatives
    well['well_data']['qo_ef'] = qo_history
    well['well_data']['Acu_Pet'] = cumo_history
    well['well_data']['qg_ef'] = qg_history
    well['well_data']['Acu_Gas'] = cumg_history

    return well