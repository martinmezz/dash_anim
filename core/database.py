import numpy as np
import pandas as pd
from core.global_vars import *
from core import decline_curve_analysis as dca
from datetime import date, datetime, timedelta
import sqlalchemy as sa
import pytz
import re


# Set config for SQL Server connection
db_config = CONFIG['DB'][ENV]
sql_driver = db_config['DRIVER']
sql_server = db_config['SERVER']
sql_user = db_config['USER']
sql_pass = db_config['PASS']
sql_database = db_config['DATABASE']
sql_trusted = db_config['TRUSTED']
if ENV == 'DEVELOPMENT':
    conn_string = f'mssql+pyodbc://{sql_server}/{sql_database}?trusted_connection=yes&driver={sql_driver}'
else:
    conn_string = f'mssql+pyodbc://{sql_user}:{sql_pass}@{sql_server}/{sql_database}?trusted_connection={sql_trusted}&driver={sql_driver}'

engine = sa.create_engine(conn_string)


def filter_wellnames(well_type, start_date, end_date):
    '''
    TODO: completar docstring
    '''

    if not start_date: start_date = '1970-01-01'
    if not end_date: end_date = date.today().strftime('%Y-%m-%d')

    start_date = "'" + start_date + "'"
    end_date = "'" + end_date + "'"

    query = f" \
        select distinct \
	        A.Pozo_Form, A.Formacion, C.Rama, A.Empresa, A.Yacimiento, \
            C.Fracturas, D.Fluido_gor \
        from \
	        Pozos_Form as A \
        left join \
	        Pozos_Form_Acum as B \
        on \
	        A.Pozo_Form = B.Pozo_Form \
        left join \
            Pozos_Form_Frac as C \
        on \
            B.Pozo_Form = C.Pozo_Form \
        right join \
            Pozos_Form_ProduAcu as D \
        on \
            A.Pozo_Form = D.Pozo_Form \
        where \
	        B.MinFecha between {start_date} and {end_date}"
    
    if well_type: query += f' and B.TipoPozo = {well_type}'

    df = pd.read_sql_query(query, engine)
    df['Fluido_gor'].fillna(value='', inplace=True)

    return df


def filter_dataset(selected_wells):
    '''
    TODO: completar docstring
    '''

    return_empty = not selected_wells

    selected_wells.append('') # Avoid errors when query the tuple

    query = f" \
        select \
	        A.Pozo_Form, B.TdP, B.qo_ef, B.Acu_Pet, B.qg_ef, B.Acu_Gas, B.GOR_ef, \
            B.qw_ef, C.Rama, C.Fracturas, B.MinFecha, B.empresa, B.areayacimiento, \
            D.qo_ef_peak, B.cuenca, D.qo_avg, D.qg_avg, B.Fluido_gor, \
            C.agua_inyectada_m3, C.ArenaTotal \
        from \
            Pozos_Form as A \
        right join \
            Pozos_Form_ProduAcu as B \
        on \
            A.Pozo_Form = B.Pozo_Form \
        left join \
            Pozos_Form_Frac as C \
        on \
            B.Pozo_Form = C.Pozo_Form \
        right join \
            Pozos_Form_Acum as D \
        on \
            C.Pozo_Form = D.Pozo_Form \
        where \
	        A.Pozo_Form in ({','.join(['?' for _ in selected_wells])})"
    
    if return_empty:
        # Get columns from query
        match = re.search(r'(?<=select).*(?=from)', query).group()
        column_names = re.findall(r'[a-zA-Z]\.(\w*)', match)
        
        # Return empty df with columns
        return pd.DataFrame(columns=column_names)

    return pd.read_sql_query(query, engine, params=selected_wells).sort_values(by=['Pozo_Form', 'TdP']).reset_index(drop=True)


def forecasts_to_sql(data, app_session, fluid=None):
    '''
    TODO: completar docstring
    '''

    # Json to DataFrame with wells data
    df = pd.DataFrame(json.loads(data)).T

    # Delete identical forecasts already on DB
    for table in ['Pronos_DCA_Dash', 'Pronos_Parametros_Dash',
        'Pronos_VolAnual_Dash', 'H_P_Dash']:
        delete_existing_forecasts(table, df, app_session)

    # Insert forecasts into tables
    write_Pronos_DCA_table(df, app_session, fluid)

    write_Pronos_Parametros_table(df, app_session, fluid)

    write_H_P_table(df, app_session)

    write_Pronos_VolAnual_table(df, app_session)


def delete_existing_forecasts(table_name, df, app_session):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - Jun 2022
    '''
    # Load user data
    user = app_session['USER'].split('@')
    company = user[1].split('.')[0]

    # Iterate over each row (each row is a well)
    forecast_ids = [build_forecast_id(row, company) for _, row in df.iterrows()]

    # If table is H_P, append ids for history wells
    if table_name == 'H_P_Dash':
        history_ids = ['H_' + row['wellname'] for _, row in df.iterrows()]
        forecast_ids.extend(history_ids)

    # Map the table
    table = sa.Table(table_name, sa.MetaData(), autoload=True, autoload_with=engine)    

    statement = table.delete().where(
        table.columns.ID_Pronos.in_(forecast_ids))
    engine.execute(statement)


def write_Pronos_DCA_table(df, app_session, fluid):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    # Load user data
    user = app_session['USER'].split('@')
    company = user[1].split('.')[0]

    Pronos_DCA = pd.DataFrame({})

    # Iterate over each row (each row is a well)
    for _, row in df.iterrows():
        wellname = row['wellname']
        GOR_pos = len(dict(json.loads(df.loc[wellname]['well_data']))['TdP'])
        if 'Manual' in wellname or 'Correlation' in wellname: GOR_pos -= 1

        t_forecast = np.array(df.loc[wellname]['t_forecast'])
        qo_forecast = np.array(df.loc[wellname]['qo_forecast'])
        cumo_forecast = np.array(df.loc[wellname]['cumo_forecast'])
        GOR_forecast = np.array(df.loc[wellname]['GOR_forecast'][GOR_pos:])
        qg_forecast = np.array(df.loc[wellname]['qg_forecast'])
        cumg_forecast = np.array(df.loc[wellname]['cumg_forecast'])

        if len(t_forecast) > 1:
            mask = dca.compress_forecast_mask(df.loc[wellname])
            t_forecast = t_forecast[mask]
            qo_forecast = qo_forecast[mask]
            cumo_forecast = cumo_forecast[mask]
            GOR_forecast = GOR_forecast[mask]
            qg_forecast = qg_forecast[mask]
            cumg_forecast = cumg_forecast[mask]

        TdP = pd.Series(t_forecast, name='TdP').astype('float64')

        Caudal_Pet = pd.Series(qo_forecast, name='Caudal_Pet').astype('float64')

        Pozo_Form_P = pd.Series([wellname+'(P50)']*len(TdP), name='Pozo_Form_P')

        Acumulada_Pet = pd.Series(cumo_forecast, name='Acumulada_Pet').astype('float64')

        Caudal_Gas = pd.Series(qg_forecast, name='Caudal_Gas').astype('float64')

        Acumulada_Gas = pd.Series(cumg_forecast, name='Acumulada_Gas').astype('float64')

        GOR = pd.Series(GOR_forecast, name='GOR').astype('float64')

        Fluido = pd.Series([fluid]*len(TdP), name='Fluido')

        forecast_id = build_forecast_id(row, company)

        ID_Pronos = pd.Series([forecast_id]*len(TdP), name='ID_Pronos')

        # Concat all Series for the well
        well_DCA = pd.concat([ID_Pronos, Pozo_Form_P, TdP, Caudal_Pet,
            Acumulada_Pet, Caudal_Gas, Acumulada_Gas, GOR, Fluido], axis=1)

        # Concat well DataFrame to Pronos_DCA DataFrame
        Pronos_DCA = pd.concat([Pronos_DCA, well_DCA], axis=0)

    if Pronos_DCA.empty: raise ValueError('Pronósticos vacíos')

    # Split df for limitation of 2100 parameters inserting into SQL DB
    chunk_size = int(2000/len(Pronos_DCA.columns))
    chunks = split_dataframe(Pronos_DCA, chunk_size=chunk_size)

    # Insert into Pronos_DCA
    for chunk in chunks:
        chunk.to_sql(
            name = 'Pronos_DCA_Dash',
            con = engine,
            if_exists = 'append',
            index = False,
            chunksize = 5000,
            method = 'multi')


def write_Pronos_Parametros_table(df, app_session, fluid):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    # Load user data
    user = app_session['USER'].split('@')
    company = user[1].split('.')[0]

    # Build Pronos_Parametros table
    get_min_date = lambda row: datetime.strptime(
        dict(json.loads(row['well_data']))['MinFecha']['0'].split('T')[0], '%Y-%m-%d')

    Pronos_Parametros = pd.DataFrame({})
    Pronos_Parametros['Pozo_Form'] = df['wellname']
    Pronos_Parametros['Parametro_b'] = df['b'].replace(['None', 'inf'], np.nan)
    Pronos_Parametros['Parametro_D'] = df['d_hyp'].replace(['None', 'inf'], np.nan)
    Pronos_Parametros['TipoDeclinacion'] = df['dca_model']
    Pronos_Parametros['ID_Pronos'] = df.apply(build_forecast_id, args=(company,), axis=1)
    Pronos_Parametros['MinFecha'] = df.apply(get_min_date, axis=1)
    Pronos_Parametros['Pozo_Form_P'] = Pronos_Parametros['Pozo_Form']+'(P50)'
    Pronos_Parametros['TipoPronos'] = 'P50'
    Pronos_Parametros['Fluido'] = fluid
    Pronos_Parametros['EUR'] = df.apply(get_primary_EUR, axis=1, args=((fluid,)))
    Pronos_Parametros['EURfs'] = df.apply(get_secondary_EUR, axis=1, args=((fluid,)))
    Pronos_Parametros['Empresa'] = df.apply(get_well_info, args=('empresa',), axis=1)
    Pronos_Parametros['Yacimiento'] = df.apply(get_well_info, args=('areayacimiento',), axis=1)

    if Pronos_Parametros.empty: raise ValueError('Pronósticos vacíos')

    # Split df for limitation of 2100 parameters inserting into SQL DB
    chunk_size = int(2000/len(Pronos_Parametros.columns))
    chunks = split_dataframe(Pronos_Parametros, chunk_size=chunk_size)

    # Insert into Pronos_Parametros
    for chunk in chunks:
        chunk.to_sql(
            name = 'Pronos_Parametros_Dash',
            con = engine,
            if_exists = 'append',
            index = False,
            chunksize = 5000,
            method = 'multi')


def write_H_P_table(df, app_session):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - Jun 2022
    '''

    # Load user data
    user = app_session['USER'].split('@')
    company = user[1].split('.')[0]

    H_P = pd.DataFrame({})

    # Iterate over each row (each row is a well)
    for _, row in df.iterrows():
        # Well parameters for history and forecast
        wellname = row['wellname']

        well_data = json.loads(row['well_data'])
        
        empresa_value = pd.Series(well_data['empresa']).dropna().iloc[-1]

        yacimiento_value = pd.Series(well_data['areayacimiento']).dropna().iloc[-1]

        forecast_id = build_forecast_id(row, company)

        if 'norm' in forecast_id:
            match = re.search(r'_norm_(.*:.*)_', forecast_id)
            norm_config = match.group()[:-1]
        else:
            norm_config = ''

        # History section
        TdP = pd.Series(well_data['TdP'].values(), name='TdP').astype('float64')

        qo_ef = pd.Series(well_data['qo_ef'].values(), name='qo_ef').astype('float64')
        Acu_Pet = pd.Series(well_data['Acu_Pet'].values(), name='Acu_Pet').astype('float64')

        qg_ef = pd.Series(well_data['qg_ef'].values(), name='qg_ef').astype('float64')
        Acu_Gas = pd.Series(well_data['Acu_Gas'].values(), name='Acu_Gas').astype('float64')

        GOR = pd.Series(well_data['GOR_ef'].values(), name='GOR').astype('float64')

        qw_ef = pd.Series(well_data['qw_ef'].values(), name='qw_ef').astype('float64')

        Pozo_Form = pd.Series([wellname]*len(TdP), name='Pozo_Form')

        Pozo_Form_P = pd.Series([wellname]*len(TdP), name='Pozo_Form_P')

        ID_Pronos = pd.Series(['H_' + wellname + norm_config]*len(TdP), name='ID_Pronos')

        Empresa = pd.Series([empresa_value]*len(TdP), name='Empresa')

        Yacimiento = pd.Series([yacimiento_value]*len(TdP), name='Yacimiento')

        # Concat all Series for the history
        history = pd.concat([TdP, qo_ef, Acu_Pet, qg_ef, Acu_Gas, GOR, qw_ef,
            Pozo_Form, Pozo_Form_P, ID_Pronos, Empresa, Yacimiento], axis=1)

        # Concat history well DataFrame to H_P DataFrame
        H_P = pd.concat([H_P, history], axis=0).reset_index(drop=True)


        # Forecast section
        GOR_pos = len(dict(json.loads(df.loc[wellname]['well_data']))['TdP'])
        if 'Manual' in wellname or 'Correlation' in wellname: GOR_pos -= 1

        t_forecast = np.array(df.loc[wellname]['t_forecast'])
        qo_forecast = np.array(df.loc[wellname]['qo_forecast'])
        cumo_forecast = np.array(df.loc[wellname]['cumo_forecast'])
        GOR_forecast = np.array(df.loc[wellname]['GOR_forecast'][GOR_pos:])
        qg_forecast = np.array(df.loc[wellname]['qg_forecast'])
        cumg_forecast = np.array(df.loc[wellname]['cumg_forecast'])

        if len(t_forecast) > 1:
            mask = dca.compress_forecast_mask(df.loc[wellname])
            t_forecast = t_forecast[mask]
            qo_forecast = qo_forecast[mask]
            cumo_forecast = cumo_forecast[mask]
            GOR_forecast = GOR_forecast[mask]
            qg_forecast = qg_forecast[mask]
            cumg_forecast = cumg_forecast[mask]

        TdP = pd.Series(t_forecast, name='TdP').astype('float64')

        qo_ef = pd.Series(qo_forecast, name='qo_ef').astype('float64')
        Acu_Pet = pd.Series(cumo_forecast, name='Acu_Pet').astype('float64')

        qg_ef = pd.Series(qg_forecast, name='qg_ef').astype('float64')
        Acu_Gas = pd.Series(cumg_forecast, name='Acu_Gas').astype('float64')

        GOR = pd.Series(GOR_forecast, name='GOR').astype('float64')

        qw_ef = pd.Series([None]*len(TdP), name='qw_ef').astype('float64')

        Pozo_Form = pd.Series([wellname]*len(TdP), name='Pozo_Form')

        Pozo_Form_P = pd.Series([wellname+'(P50)']*len(TdP), name='Pozo_Form_P')

        ID_Pronos = pd.Series([forecast_id]*len(TdP), name='ID_Pronos')

        Empresa = pd.Series([empresa_value]*len(TdP), name='Empresa')

        Yacimiento = pd.Series([yacimiento_value]*len(TdP), name='Yacimiento')

        # Concat all Series for the forecast
        forecast = pd.concat([TdP, qo_ef, Acu_Pet, qg_ef, Acu_Gas, GOR, qw_ef,
            Pozo_Form, Pozo_Form_P, ID_Pronos, Empresa, Yacimiento], axis=1)

        # Concat history well DataFrame to H_P DataFrame
        H_P = pd.concat([H_P, forecast], axis=0).reset_index(drop=True)

    if H_P.empty: raise ValueError('Pronósticos vacíos')

    # Split df for limitation of 2100 parameters inserting into SQL DB
    chunk_size = int(2000/len(H_P.columns))
    chunks = split_dataframe(H_P, chunk_size=chunk_size)

    # Insert into H_P
    for chunk in chunks:
        chunk.to_sql(
            name = 'H_P_Dash',
            con = engine,
            if_exists = 'append',
            index = False,
            chunksize = 5000,
            method = 'multi')        

def write_Pronos_VolAnual_table(df, app_session):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    # Load user data
    user = app_session['USER'].split('@')
    company = user[1].split('.')[0]

    # Build Pronos_VolAnual table
    df_aux = pd.DataFrame({})
    df_aux['Pozo_Form_P'] = df['wellname'] + '(P50)'
    df_aux['cumo_by_year'] = df.apply(lambda row: annualize_cumulatives(row, 'oil'), axis=1) # TODO: lambda is not necessary
    df_aux['cumg_by_year'] = df.apply(lambda row: annualize_cumulatives(row, 'gas'), axis=1) # TODO: lambda is not necessary
    df_aux['ID_Pronos'] = df.apply(lambda row: build_forecast_id(row, company), axis=1) # TODO: lambda is not necessary
    df_aux['cuenca'] = df.apply(get_well_info, args=('cuenca',), axis=1)
    
    # Iterate over each row (each row is a well)
    Pronos_VolAnual = pd.DataFrame({})
    for _, row in df_aux.iterrows():
        subrows = len(row['cumo_by_year']) + 1

        ID_Pronos = pd.Series([row['ID_Pronos']]*subrows, name='ID_Pronos')

        Pozo_Form_P = pd.Series([row['Pozo_Form_P']]*subrows, name='Pozo_Form_P')

        Anio = pd.Series(range(subrows), name='Anio')

        Fecha = pd.Series(pd.Series([None]*subrows, name='Fecha'))
        Fecha.iloc[1:] = [datetime(year, 12, 15) for year in row['cumo_by_year'].index]

        FechaTIR = pd.Series([None]*subrows, name='FechaTIR')
        FechaTIR[0] = datetime(row['cumo_by_year'].index[0] - 1, 12, 15)

        VolAnual_Pet = pd.Series([0]*subrows, name='VolAnual_Pet').astype('float64')
        VolAnual_Pet[1:] = row['cumo_by_year']['diff'].values

        VolAnual_Gas = pd.Series([0]*subrows, name='VolAnual_Gas').astype('float64')
        VolAnual_Gas[1:] = row['cumg_by_year']['diff'].values

        Cuenca_Anio = pd.Series([row['cuenca']+str(year) for year in range(
            row['cumo_by_year'].index[0] -1,
            row['cumo_by_year'].index[-1] + 1)], name='Cuenca_Anio')

        # Concat all Series for the well
        well_VolAnual = pd.concat([ID_Pronos, Pozo_Form_P, Anio, Fecha, FechaTIR,
            VolAnual_Pet, VolAnual_Gas, Cuenca_Anio], axis=1)

        # Concat well DataFrame to Pronos_DCA DataFrame
        Pronos_VolAnual = pd.concat([Pronos_VolAnual, well_VolAnual], axis=0)

    if Pronos_VolAnual.empty: raise ValueError('Pronósticos vacíos')
    
    # Split df for limitation of 2100 parameters inserting into SQL DB
    chunk_size = int(2000/len(Pronos_VolAnual.columns))
    chunks = split_dataframe(Pronos_VolAnual, chunk_size=chunk_size)

    # Insert into Pronos_VolAnual
    for chunk in chunks:
        chunk.to_sql(
            name = 'Pronos_VolAnual_Dash',
            con = engine,
            if_exists = 'append',
            index = False,
            chunksize = 5000,
            method = 'multi')


def split_dataframe(df, chunk_size=500):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    chunks = list()
    num_chunks = len(df) // chunk_size + 1
    for i in range(num_chunks):
        chunks.append(df[i*chunk_size:(i+1)*chunk_size])
    return chunks


def build_forecast_id(well, company):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    date = datetime.now(tz=pytz.timezone('America/Buenos_Aires')).strftime("%Y%m%d")

    forecast_params = [company, date, well['dca_model']]

    if well['b'] == 'None':
        forecast_params.append('b:None')
    else:
        b = float(well['b'])
        forecast_params.append('b:'+'{:.2f}'.format(b))

    if well['d_hyp'] == 'None':
        forecast_params.append('Dhyp:None')
    else:
        d_hyp = float(well['d_hyp'])
        forecast_params.append('Dhyp:'+'{:.2f}'.format(d_hyp))

    if well['d_exp'] == 'None':
        forecast_params.append('Dexp:None')
    else:
        d_exp = float(well['d_exp'])
        forecast_params.append('Dexp:'+'{:.2f}'.format(d_exp))
    
    forecast_params.append(well['wellname'])

    if 'normalization' in well and well['normalization']['enabled']:
        forecast_params.append('norm')
        norm = well['normalization'].copy()
        norm.pop('enabled')
        norm_params = [f'{k}:{v}' for k,v in norm.items()]
        forecast_params.append('_'.join(norm_params))

    if 'Correlation-High' in well['wellname']:
        forecast_params.append('(P10)')
    elif 'Correlation-Best' in well['wellname']:
        forecast_params.append('(P50)')
    elif 'Correlation-Low' in well['wellname']:
        forecast_params.append('(P90)')
    else:
        forecast_params.append('(P50)')

    return '_'.join(forecast_params)


def read_my_forecasts(query_type, query_data, app_session):
    '''
    TODO: COMPLETAR DOCSTRING
    '''
    
    # Load user data
    user = app_session['USER'].split('@')
    company = user[1].split('.')[0]

    if query_type == 'parameters':
        query = f" \
            select \
                * \
            from \
                Pronos_Parametros_Dash as A \
            where \
                A.ID_Pronos like '{company}%'"

    elif query_type == 'H_P':
        forecasts_ids = list(query_data.values)
        forecasts_ids.append('') # Avoid errors when query the tuple
        
        if query_data.empty: return pd.DataFrame(
            columns = ['ID_Pronos', 'Pozo_Form', 'Pozo_Form_P', 'TdP', 'qo_ef', \
                'qg_ef', 'qw_ef', 'Acu_Pet', 'Acu_Gas', 'GOR', 'Empresa', 'Yacimiento'])

        query = f" \
            select \
                * \
            from \
                H_P_Dash as A \
            where \
                A.ID_Pronos in {tuple(forecasts_ids)}"
    
    return pd.read_sql_query(query, engine)


def get_oil_EUR(row):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    if row['cumo_forecast']:
        return row['cumo_forecast'][-1]
    else:
        return list(json.loads(row['well_data'])['Acu_Pet'].values())[-1]


def get_gas_EUR(row):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    if row['cumg_forecast']:
        return row['cumg_forecast'][-1]
    else:
        return list(json.loads(row['well_data'])['Acu_Gas'].values())[-1]
        

def get_primary_EUR(row, fluid):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    if fluid == 'oil':
        return get_oil_EUR(row)
    elif fluid == 'gas':
        return get_gas_EUR(row)


def get_secondary_EUR(row, fluid):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    if fluid == 'gas':
        return get_oil_EUR(row)
    elif fluid == 'oil':
        return get_gas_EUR(row)


def annualize_cumulatives(row, fluid):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    YEARS_FOR_ECONOMIC_EV = 35
    well_data = json.loads(row['well_data'])

    min_date = list((well_data)['MinFecha'].values())[-1]
    min_date = datetime.strptime(min_date[:10], '%Y-%m-%d')

    # Append history + forecast
    t = np.append(list(well_data['TdP'].values()), row['t_forecast'])
    dates = [min_date + timedelta(days=i) for i in t]
    if fluid == 'oil':
        cum = np.append(list(well_data['Acu_Pet'].values()), row['cumo_forecast'])
        column = 'cumo'
    elif fluid == 'gas':
        cum = np.append(list(well_data['Acu_Gas'].values()), row['cumg_forecast'])
        column = 'cumg'

    # Annualize
    cum_by_year = {}
    for i in range(YEARS_FOR_ECONOMIC_EV):
        year = min_date.year + i
        mask = np.array(dates) < datetime(year, 12, 31)
        
        if i != YEARS_FOR_ECONOMIC_EV - 1:
            cum_by_year[year] = np.nan_to_num(
            cum[mask][-1]) if any(mask) else 0
        else:
            cum_by_year[year] = np.nan_to_num(
            cum[-1])

    # Construct dataFrame
    result = pd.DataFrame.from_dict(cum_by_year, orient='index', columns=[column])
    
    # Calculate cumulative for each year
    cum_by_year_array = np.array(list(cum_by_year.values()))
    result['diff'] = np.append(cum_by_year_array[0], np.diff(cum_by_year_array))

    return result


def get_well_info(row, column):
    '''
    TODO: AGREGAR DOCSTRING
    '''
    
    return list(json.loads(row['well_data'])[column].values())[-1]


def get_wells_props():
    '''
    TODO: AGREGAR DOCSTRING
    '''

    query = f" \
        select distinct \
	        A.Pozo_Form, A.Coordenadax, A.Coordenaday, \
            B.Rama, B.Fracturas \
        from \
	        Pozos_Form as A \
        left join \
            Pozos_Form_Frac as B \
        on \
            A.Pozo_Form = B.Pozo_Form \
        where \
            A.formprod = 'VMUT'"

    return pd.read_sql_query(query, engine)