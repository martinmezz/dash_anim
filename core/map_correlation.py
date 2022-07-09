import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def calculate_fluid(ro):
    '''
    Calculates GORi based on Ro, and classifies the well fluid as OIL or GAS.

    Params:
        ro(float): vitrinite reflectance (as percentage)
    
    Returns:
        fluid(str): fluid type ('OIL' / 'GAS')
    '''
    
    # Calculate GOR based on Ro correlation
    log_GOR_qo_peak = 8.9232 * ro**3 - 24.207 * ro**2 + 22.773 *ro - 5.5395
    GOR_qo_peak = 10**log_GOR_qo_peak

    # Make fluid classification based on table (Dow, Javie, Elias & Gelin, GIGA)
    if ro < 1.35:
        fluid = 'OIL' if GOR_qo_peak < 300 else 'OIL'
    else:
        fluid = 'GAS' if GOR_qo_peak < 4500 else 'GAS'

    return fluid

def Qi_correlacion(ESPESOR, RO, TOC, FRACTURAS):
    '''CALCULAR EL Qi CON LA CORRELACION DE MAPA'''

    Qi_pronosticada = (-6.882648 + 26.248586*(FRACTURAS/TOC)
            + -2.229511*(ESPESOR/RO) + (-12.719978)*((FRACTURAS/TOC)**2)
            + 0.003212*((ESPESOR/RO)**2) + 0.604173*((FRACTURAS/TOC)**3)
            + (0.000023)*((ESPESOR/RO)**3)
            + 1.176622*(FRACTURAS/TOC)*(ESPESOR/RO)
            + (-0.002563) * ((FRACTURAS/TOC)**2)*(ESPESOR/RO)
            + (-0.003845)*((ESPESOR/RO)**2)*(FRACTURAS/TOC))
    
    return Qi_pronosticada


def Qi_simulacion(FRACTURAS):
    '''CALCULAR EL Qi CON LA CORRELACION OBTENIDA POR SIMULACION. ASINTOTICA 
    PARA FRACS GRANDES'''
    
    Qi_pronosticada = np.exp(0.5639 * np.log(FRACTURAS) + 5.4708) / 6.29
    
    return Qi_pronosticada


def Qi_calculado(ESPESOR,RO,TOC,FRACTURAS):
    '''
    CALCULAR EL CAUDAL SEGUN MAPA Y NUMERO DE FRACTURAS DE ACUERDO A 
    SIMULACION Y CORRELACION
    - ES UNA BUSQUEDA DE INTERSECCION CROTA. NO SE PUEDE DESPEJAR FRACS
    DE LA CORRELACION PARA CALCULAR LA INTERSECCION ANALITICAMENTE
    
    PODRIA BUSCARSE UNA SOLUCION MAS EFICIENTE. 
    
    '''
    
    fracturas_a_probar = np.linspace(35,65,31)
    
    Qi_pronosticado_simulacion = Qi_simulacion(fracturas_a_probar)
    Qi_pronosticado_correlacion = Qi_correlacion(ESPESOR, RO, TOC, fracturas_a_probar)
    
    indice_fracs_interseccion = np.argmin(np.abs((Qi_pronosticado_correlacion 
        - Qi_pronosticado_simulacion) / Qi_pronosticado_simulacion))
    
    fracs_interseccion = fracturas_a_probar[indice_fracs_interseccion]
    
    if FRACTURAS < fracs_interseccion:
        Qi_pronosticada = Qi_correlacion(ESPESOR, RO, TOC, FRACTURAS)
    else:
        Qi_pronosticada = Qi_simulacion(FRACTURAS)
    
    
    return Qi_pronosticada


def oil_correlation(RAMA, FRACTURAS, TOC, RO, ESPESOR, T_PICO, TARGET_PROF, margen_best):
    '''TODO: AGREGAR DOCSTRING'''
    #TARGET: C para COCINA y O para ORGANICO, NADA PARA USAR EL PROMEDIO

    # Generamos los parametros de las correlaciones serían los parametros de una P50
    def parametros(RAMA, FRACTURAS, TOC, RO, ESPESOR, TARGET_PROF):
        """ Qi_pronosticada = (-635.896346 + 270.004742*(FRACTURAS/TOC)
            + (-2.755761)*(ESPESOR/RO) + (-31.825876)*((FRACTURAS/TOC)**2)
            + 0.036103*((ESPESOR/RO)**2) + 1.325105*((FRACTURAS/TOC)**3)
            + (-0.000107)*((ESPESOR/RO)**3)) """
        
        Qi_pronosticada = Qi_calculado(ESPESOR,RO,TOC,FRACTURAS)
        #Qi_pronosticada = Qi_correlacion(ESPESOR,RO,TOC,FRACTURAS)              
        
        Np_pronosticada = 4164.72 + 189.19*Qi_pronosticada
        EUR_pronosticada =  0.025625*FRACTURAS + 0.000235*RAMA + 10.4018
        EUR_pronosticada = np.exp(EUR_pronosticada)
        Np_180_pronosticada = 128.11*Qi_pronosticada - 157.91

        if TARGET_PROF == 1:
            Qi_pronosticada = Qi_pronosticada * 1.14
            Np_180_pronosticada = Np_180_pronosticada * 1.18
            Np_pronosticada = Np_pronosticada * 1.1
            EUR_pronosticada = EUR_pronosticada * 1.21
        elif TARGET_PROF == 2:
            Qi_pronosticada = Qi_pronosticada * 0.87
            Np_180_pronosticada = Np_180_pronosticada * 0.84 
            Np_pronosticada = Np_pronosticada * 0.8
            EUR_pronosticada = EUR_pronosticada * 1.3

        return EUR_pronosticada, Qi_pronosticada,  Np_pronosticada, Np_180_pronosticada

    # Generamos los parametros P10 y P90 partiendo de los valores anteriores.
    def incertidumbre(EUR, Np, Qi,Np_180, margen_best):
        EUR_P90 = EUR - EUR * margen_best/100
        Np_P90 = Np - Np * margen_best/100
        Qi_P90 = Qi - Qi * margen_best/100
        EUR_P10 = EUR + EUR * margen_best/100
        Np_P10 = Np + Np * margen_best/100
        Qi_P10 = Qi + Qi * margen_best/100
        Np_180_P10 = Np_180 + Np_180 * margen_best/100
        Np_180_P90 = Np_180 - Np_180 * margen_best/100

        return EUR_P90, Np_P90, Qi_P90, EUR_P10, Np_P10, Qi_P10, Np_180_P90, Np_180_P10

    # Ajustamos b y Dn
    def cum_hyper_modif_correlation(t, qi, di, b):
        '''
        funcion para la acumulada de una hiperbola modificada
                
        '''
        tiempo_cambio = 2432
        
        # Dividir vector
        tiempo_hip = t[t < tiempo_cambio]
        tiempo_exp = t[t >= tiempo_cambio]
        
        acum_hip = (qi**b / (di*(1 - b))) * (qi**(1 - b) - (qi/((b * di *
            tiempo_hip + 1)**(1 / b)))**(1 - b))

        acum_cambio = acum_hip[-1]

        caudal_cambio = qi * (1 + b * di * tiempo_cambio)**(-1/b)

        dn_cambio = di / (1 + b*di*(tiempo_cambio - 20))

        #dn_cambio = -(caudal_hip[-1] - caudal_hip[-2]) /(caudal_hip[-1] * (tiempo_hip[-1] - tiempo_hip[-2]))

        acum_exp = acum_cambio + caudal_cambio * (1 - np.exp(-dn_cambio * (tiempo_exp - tiempo_cambio)))/dn_cambio
        
        # Juntarlos
        acumulada = np.append(acum_hip, acum_exp)
        
        return acumulada


    def generar_bydn(Qi, Np1, EUR, T_PICO, Np_180):
                
        #T_PICO = 0
        t_aux = np.array([T_PICO,  180, 365, 365*35])
        cum_aux = np.array([Qi*T_PICO / 2, Np_180,   Np1, EUR])

        # Curve fitting
        MAXFEV = len(cum_aux) * 50
        
        y_weight = np.empty(len(cum_aux))
        y_weight[0] = 5
        y_weight[1] = 0.1
        y_weight[2] = 0.1
        y_weight[3] = 1

        popt, pcov = curve_fit(cum_hyper_modif_correlation, t_aux,
        cum_aux, maxfev=int(MAXFEV), bounds=((Qi * 0.99, 0.001, 0.4),
            (Qi * 1.01, 10, 1.3)), sigma = y_weight)
                
        qi, dn_final, b_final = popt
        
        #b_final = 1.2
        #dn_final = 0.00570841889

        return qi, b_final, dn_final

    #Generamos hiperbolica modificada con opción 2
    def hiperbola_modificada(t, Qi, Dni, b_coeff, T_PICO):
        '''
        TODO: AGREGAR DOCSTRING
        '''
        tiempo_cambio = 2432

        # Dividir vector
        tiempo_hip = t[t < tiempo_cambio]
        tiempo_exp = t[t >= tiempo_cambio]
        
        # calcular cada uno con su func
        caudal_hip = Qi * (1 + Dni * b_coeff * (tiempo_hip - T_PICO)) ** (-1/b_coeff)
        dn_cambio = Dni / (1+b_coeff*Dni*(tiempo_cambio-20))
        #dn_cambio = -(caudal_hip[-1] - caudal_hip[-2]) /(caudal_hip[-1] * (tiempo_hip[-1] - tiempo_hip[-2]))
        
        caudal_de_cambio = Qi * (1 + Dni * b_coeff * tiempo_cambio) ** (-1/b_coeff)
        caudal_exp = caudal_de_cambio * np.exp(-dn_cambio * (tiempo_exp-tiempo_cambio))

        # juntarlos
        caudal = np.append(caudal_hip, caudal_exp)

        return caudal


    EUR_pronosticada, Qi_pronosticada, Np_pronosticada, Np_180_pronosticado = \
        parametros(RAMA, FRACTURAS, TOC, RO, ESPESOR, TARGET_PROF)

    EUR_P90, Np_P90, Qi_P90, EUR_P10, Np_P10, Qi_P10, Np_180_P90, Np_180_P10 = \
        incertidumbre(EUR_pronosticada, Np_pronosticada, Qi_pronosticada,
        Np_180_pronosticado, margen_best)

    # Hasta acá tengo todas las correlaciones
    qi_1, b_1, dn_1 = generar_bydn(Qi_pronosticada, Np_pronosticada,
        EUR_pronosticada, T_PICO, Np_180_pronosticado)
    
    qi_2, b_2, dn_2 = generar_bydn(Qi_P90, Np_P90, EUR_P90, T_PICO, Np_180_P90)
    
    qi_3, b_3, dn_3 = generar_bydn(Qi_P10, Np_P10, EUR_P10, T_PICO,Np_180_P10)

    tiempo = np.linspace(T_PICO, 35*365, 250)

    caudales_pronostico_P50 = hiperbola_modificada(tiempo, qi_1, dn_1, b_1, T_PICO)
    caudales_pronostico_P90 = hiperbola_modificada(tiempo, qi_2, dn_2, b_2, T_PICO)
    caudales_pronostico_P10 = hiperbola_modificada(tiempo, qi_3, dn_3, b_3, T_PICO)

    acum_final_P50 = cum_hyper_modif_correlation(tiempo, qi_1, dn_1, b_1)
    acum_final_P90 = cum_hyper_modif_correlation(tiempo, qi_2, dn_2, b_2)
    acum_final_P10 = cum_hyper_modif_correlation(tiempo, qi_3, dn_3, b_3)

    # Completar el tramo inicial de curvas
    tiempo = np.append(0, tiempo)

    caudales_pronostico_P50 = np.append(0, caudales_pronostico_P50)
    caudales_pronostico_P90 = np.append(0, caudales_pronostico_P90)
    caudales_pronostico_P10 = np.append(0, caudales_pronostico_P10)

    acum_final_P50 = np.append(0, acum_final_P50)
    acum_final_P90 = np.append(0, acum_final_P90)
    acum_final_P10 = np.append(0, acum_final_P10)

    # Build forecasted wells
    well_P50 = {
        'wellname': 'Best estimate',
        't_forecast': tiempo,
        'qo_forecast': caudales_pronostico_P50,
        'cumo_forecast': acum_final_P50,
        'GOR': np.full_like(tiempo, fill_value=0),
        'qg_forecast': np.full_like(tiempo, fill_value=0),
        'cumg_forecast': np.full_like(tiempo, fill_value=0),
        'b': b_1,
        'd_hyp': dn_1
    }

    well_P90 = {
        'wellname': 'Low estimate',
        't_forecast': tiempo,
        'qo_forecast': caudales_pronostico_P90,
        'cumo_forecast': acum_final_P90,
        'GOR': np.full_like(tiempo, fill_value=0),
        'qg_forecast': np.full_like(tiempo, fill_value=0),
        'cumg_forecast': np.full_like(tiempo, fill_value=0),
        'b': b_2,
        'd_hyp': dn_2
    }

    well_P10 = {
        'wellname': 'High estimate',
        't_forecast': tiempo,
        'qo_forecast': caudales_pronostico_P10,
        'cumo_forecast': acum_final_P10,
        'GOR': np.full_like(tiempo, fill_value=0),
        'qg_forecast': np.full_like(tiempo, fill_value=0),
        'cumg_forecast': np.full_like(tiempo, fill_value=0),
        'b': b_3,
        'd_hyp': dn_3
    }

    return well_P50, well_P90, well_P10


def gas_correlation(RAMA, FRACTURAS, TOC, RO, ESPESOR, T_PICO, TARGET_PROF, margen_best):
    '''TODO: AGREGAR DOCSTRING'''

    #Generamos los parametros de las correlaciones serían los parametros de una P50
    def parametros(RAMA, FRACTURAS, TOC, RO, ESPESOR, TARGET_PROF):
        Qi_pronosticada = 302.918687 + (-133.212931)*(FRACTURAS/TOC) + 1.874151*(ESPESOR/RO)+ 0.348858*((FRACTURAS/TOC)**2)+ (-0.061000)*((ESPESOR/RO)**2) + (0.010730)*((FRACTURAS/TOC)**3) + 0.000217*((ESPESOR/RO)**3) + 2.644869*(FRACTURAS/TOC)*(ESPESOR/RO) + (-0.021607)*((FRACTURAS/TOC)**2)*(ESPESOR/RO) + (-0.008116)*((ESPESOR/RO)**2)*(FRACTURAS/TOC)
        Np_pronosticada = 265.79425461*Qi_pronosticada-7871.27016980
        EUR_pronosticada =  0.522371*((np.log(FRACTURAS)-np.log(5))/(np.log(63)-np.log(5))) + 1.61496954*((np.log(RAMA)-np.log(500))/(np.log(5083)-np.log(500))) + 11.63259
        EUR_pronosticada = np.exp(EUR_pronosticada)
        Np_180_pronosticada = 128.11*Qi_pronosticada - 157.91

        if TARGET_PROF == 1:
            Qi_pronosticada = Qi_pronosticada * 1.14
            Np_180_pronosticada = Np_180_pronosticada * 1.18
            Np_pronosticada = Np_pronosticada * 1.1
            EUR_pronosticada = EUR_pronosticada * 1.21
        elif TARGET_PROF == 2:
            Qi_pronosticada = Qi_pronosticada * 0.87
            Np_180_pronosticada = Np_180_pronosticada * 0.84 
            Np_pronosticada = Np_pronosticada * 0.8
            EUR_pronosticada = EUR_pronosticada * 1.3

        return EUR_pronosticada, Qi_pronosticada,  Np_pronosticada, Np_180_pronosticada


    #Generamos los parametros P10 y P90 partiendo de los valores anteriores
    def incertidumbre(EUR, Np, Qi,Np_180, margen_best):
        EUR_P90 = EUR - EUR * margen_best/100
        Np_P90 = Np - Np * margen_best/100
        Qi_P90 =  Qi - Qi * margen_best/100
        EUR_P10 =  EUR + EUR * margen_best/100
        Np_P10 = Np + Np * margen_best/100
        Qi_P10 = Qi + Qi * margen_best/100
        Np_180_P10 = Np_180 + Np_180 * margen_best/100
        Np_180_P90 = Np_180 - Np_180 * margen_best/100

        return EUR_P90, Np_P90, Qi_P90, EUR_P10, Np_P10, Qi_P10, Np_180_P90,Np_180_P10

    #Ajustamos b y Dn
    def cum_hyper_modif_correlation(t, qi, di, b):
        '''
        TODO: AGREGAR DOCSTRING
        '''
        tiempo_cambio = 2432
        
        # Dividir vector
        tiempo_hip = t[t < tiempo_cambio]
        tiempo_exp = t[t >= tiempo_cambio]
         
        acum_hip = (qi**b / (di*(1 - b))) * (qi**(1 - b) - (qi/((b*di*tiempo_hip+1)**(1/b)))**(1 - b))
        acum_cambio = acum_hip[-1]
        caudal_cambio = qi * (1 + b * di * tiempo_cambio)**(-1/b)
        dn_cambio = di / (1+b*di*(tiempo_cambio-20))
        #dn_cambio = -(caudal_hip[-1] - caudal_hip[-2]) /(caudal_hip[-1] * (tiempo_hip[-1] - tiempo_hip[-2]))
        acum_exp = acum_cambio + caudal_cambio * (1 - np.exp(-dn_cambio * (tiempo_exp - tiempo_cambio)))/dn_cambio
         
         # juntarlos
        acumulada = np.append(acum_hip, acum_exp)
        
        return acumulada

    def generar_bydn(Qi, Np1, EUR, T_PICO, Np_180):
        if Qi > 10:
            t_aux = np.array([T_PICO, 180, 365, 25*365])
            cum_aux = np.array([Qi*T_PICO/2, Np_180, Np1, EUR])

            # Curve fitting
            MAXFEV = len(cum_aux) * 50
            
            y_weight = np.empty(len(cum_aux))
            y_weight[0] = 5
            y_weight[1] = 0.1
            y_weight[2] = 0.1
            y_weight[3] = 1
        
            popt, pcov = curve_fit(cum_hyper_modif_correlation, t_aux,
            cum_aux, maxfev=int(MAXFEV), bounds=((Qi*0.95, 0, 0.4),
                        (Qi*1.05, 1.1, 1.5)))
            curve_fitted = True
                
            qi, dn_final, b_final = popt
        else:
            t_aux = np.array([T_PICO, 365, 25*365.25])
            cum_aux = np.array([Qi*T_PICO/2, Np1, EUR])

            # Curve fitting
            MAXFEV = len(cum_aux) * 50
        
        
            popt, pcov = curve_fit(cum_hyper_modif_correlation, t_aux,
            cum_aux, maxfev=int(MAXFEV), bounds=((10, 0, 0.4),
                        (20, 1.1, 1.3)))
            curve_fitted = True
                
            qi, dn_final, b_final = popt

        return qi, b_final, dn_final

    #Generamos hiperbolica modificada con opción 2
    def hiperbola_modificada(t, Qi, Dni, b_coeff, T_PICO):
        '''
        TODO: AGREGAR DOCSTRING
        '''
        tiempo_cambio = 2432

        # Dividir vector
        tiempo_hip = t[t < tiempo_cambio]
        tiempo_exp = t[t >= tiempo_cambio]

        # calcular cada uno con su func
        caudal_hip = Qi * (1 + Dni * b_coeff * (tiempo_hip - T_PICO)) ** (-1/b_coeff)
        dn_cambio = Dni / (1+b_coeff*Dni*(tiempo_cambio-20))
        #dn_cambio = -(caudal_hip[-1] - caudal_hip[-2]) /(caudal_hip[-1] * (tiempo_hip[-1] - tiempo_hip[-2]))
        
        caudal_de_cambio = Qi * (1 + Dni * b_coeff * tiempo_cambio) ** (-1/b_coeff)
        caudal_exp = caudal_de_cambio * np.exp(-dn_cambio * (tiempo_exp-tiempo_cambio))

        # juntarlos
        caudal = np.append(caudal_hip, caudal_exp)

        return caudal

    
    EUR_pronosticada, Qi_pronosticada, Np_pronosticada, Np_180_pronosticado = \
        parametros(RAMA, FRACTURAS, TOC, RO, ESPESOR, TARGET_PROF)

    EUR_P90, Np_P90, Qi_P90, EUR_P10, Np_P10, Qi_P10, Np_180_P90,Np_180_P10 = \
        incertidumbre(EUR_pronosticada, Np_pronosticada, Qi_pronosticada,
        Np_180_pronosticado, margen_best)

    # Hasta acá tengo todas las correlaciones
    qi_1, b_1, dn_1 = generar_bydn(Qi_pronosticada, Np_pronosticada,
        EUR_pronosticada, T_PICO, Np_180_pronosticado)
    
    qi_2, b_2, dn_2 = generar_bydn(Qi_P90, Np_P90, EUR_P90, T_PICO, Np_180_P90)

    qi_3, b_3, dn_3 = generar_bydn(Qi_P10, Np_P10, EUR_P10, T_PICO, Np_180_P10)

    tiempo = np.linspace(T_PICO, 35*365, 250)
    
    caudales_pronostico_P50 = hiperbola_modificada(tiempo, qi_1, dn_1, b_1, T_PICO)
    caudales_pronostico_P90 = hiperbola_modificada(tiempo, qi_2, dn_2, b_2, T_PICO)
    caudales_pronostico_P10 = hiperbola_modificada(tiempo, qi_3, dn_3, b_3, T_PICO)

    acum_final_P50 = cum_hyper_modif_correlation(tiempo, qi_1, dn_1, b_1)
    acum_final_P90 = cum_hyper_modif_correlation(tiempo, qi_2, dn_2, b_2)
    acum_final_P10 = cum_hyper_modif_correlation(tiempo, qi_3, dn_3, b_3)

    # Completar el tramo inicial de curvas
    tiempo = np.append(0, tiempo)

    caudales_pronostico_P50 = np.append(0, caudales_pronostico_P50)
    caudales_pronostico_P90 = np.append(0, caudales_pronostico_P90)
    caudales_pronostico_P10 = np.append(0, caudales_pronostico_P10)

    acum_final_P50 = np.append(0, acum_final_P50)
    acum_final_P90 = np.append(0, acum_final_P90)
    acum_final_P10 = np.append(0, acum_final_P10)
    
    # Build forecasted wells
    well_P50 = {
        'wellname': 'Best estimate',
        't_forecast': tiempo,
        'qo_forecast': np.full_like(tiempo, fill_value=0),
        'cumo_forecast': np.full_like(tiempo, fill_value=0),
        'GOR': np.full_like(tiempo, fill_value=0),
        'qg_forecast': caudales_pronostico_P50,
        'cumg_forecast': acum_final_P50,
        'b': b_1,
        'd_hyp': dn_1
    }

    well_P90 = {
        'wellname': 'Low estimate',
        't_forecast': tiempo,
        'qo_forecast': np.full_like(tiempo, fill_value=0),
        'cumo_forecast': np.full_like(tiempo, fill_value=0),
        'GOR': np.full_like(tiempo, fill_value=0),
        'qg_forecast': caudales_pronostico_P90,
        'cumg_forecast': acum_final_P90,
        'b': b_2,
        'd_hyp': dn_2
    }

    well_P10 = {
        'wellname': 'High estimate',
        't_forecast': tiempo,
        'qo_forecast': np.full_like(tiempo, fill_value=0),
        'cumo_forecast': np.full_like(tiempo, fill_value=0),
        'GOR': np.full_like(tiempo, fill_value=0),
        'qg_forecast': caudales_pronostico_P10,
        'cumg_forecast': acum_final_P10,
        'b': b_3,
        'd_hyp': dn_3
    }

    return well_P50, well_P90, well_P10