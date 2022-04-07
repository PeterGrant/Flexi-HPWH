# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 20:38:42 2021

These functions read external assumptions of air or inlet water temperature
and overwrite any monitored data to allow simulations in other climate zones.

The functions work in degrees Fahrenheit and are intended to modify the inputs
BEFORE they are converted to deg C.

@author: Peter Grant
"""
    
def overwrite_parameter(CZ, data, data_col_name, assumption_col_name):
    '''
    This function replaces data in the monitored data set with simulation
    assumptions from a CBECC-Res output file. It is designed for use 
    specifically for Creekside outdoor air temperature and inlet water
    temperature data, though it may work for other data sets. This function
    should be called before converting monitored data from deg F to deg C.
    
    This function currently only accepts hourly simulation assumption data and
    will need modification if you want to use finer timesteps. It reads the
    value for each hour from the simulation assumption data and uses it to
    replace the monitored data for those hours. This will overwrite the data
    in all timestamps within that hour regardless of sampling frequency in the
    monitored data.
    
    inputs:
        CZ: string. The climate zone of the desired CBECC-Res input data.
            Include '0' for single digit climate zones. E.g. CZ 3 is 
            represented as '03'.
        data: pd.DataFrame. The monitored data set.
        data_col_name: The name of the column containing the data you wish to 
            overwrite. For instance, outdoor air temperature may be 'T_Outdoor_F'
        assumption_col_name: The name of the column in the CBECC-Res data
            with the data you want to move into the monitored data set. For
            instance, inlet water temperature is 't_Inlet'
            
    outputs:
        mod: pd.DataFrame. A modified version of data with the desired data
            changes.
    '''
    
    import pandas as pd
    import os
    import datetime
    
    mod = data.copy(deep = True)
    mod['Timestamp'] = mod.index.month.astype(str) + ' ' + mod.index.day.astype(str) \
        + ' ' + mod.index.hour.astype(str)
    mod['Timestamp'] = pd.to_datetime(mod['Timestamp'], format = '%m %d %H')    

    assumption = pd.read_csv(os.path.join('CBECC Inputs', 'RESULTSDHWHR_CZ{}.csv'.format(CZ)),
                             skiprows=3)   
    assumption.loc[0, 'Timestamp'] = datetime.datetime(1900, 1, 1, 0)
    assumption.loc[1:, 'Timestamp'] = assumption.loc[0, 'Timestamp'] + pd.to_timedelta(assumption.index[1:], unit = 'h')    
    assumption.index = assumption['Timestamp']    
    
    temp = mod['Timestamp']
    t_outdoor = assumption[assumption_col_name].to_dict()
    
    temp = temp.map(t_outdoor)
    mod[data_col_name] = temp

    return mod

def remove_one_year(timestamp, start_month = 10):
    '''
    This function removes year from selected timestamps as needed for analysis.
    This is useful when comparing simulation assumption data to modified 
    Creekside data sets. It can remove one year from months that started in an
    earlier year to make them sync up with the monitored data set. For instance,
    if the monitored data set runs from Oct 1, 2020 to Sep 30, 2021 and the 
    index of the simulation assumptions is Jan 1, 2021 to Dec 31, 2021 you can
    use this function to remove one year from Oct - Dec.
    
    This function is designed to be called using pd.DataFrame.map, though you
    can iterate through as desired. If using .map the value of start_month should
    be changed here instead of in the function call.
    
    inputs:
        timestamp: datetime object, typically in a pd.DateTimeIndex
        start_month: integer. The starting month of the data set, and the first
            month that will be modifed. E.g. If start_month == 10 then Oct, Nov,
            Dec will have 1 year removed.
    
    outputs:
        timestamp: datetime object with one year removed if appropriate.
    '''
    
    import datetime
    
    if timestamp.month >= start_month:
        timestamp = datetime.datetime(timestamp.year - 1, timestamp.month, timestamp.day, timestamp.hour)
    return timestamp

if __name__ == "__main__":
    
    import pandas as pd
    import os
    import matplotlib.pyplot as plt
    import time
    import datetime
    
    print('Testing with CZ = 3')
    cwd = os.getcwd()
    case = '3D8C'
    CZ = '03'
    Path_DrawProfile = cwd + r'\Input\Creekside Data for {}.csv'.format(case)
    
    data = pd.read_csv(Path_DrawProfile, index_col = 0)
    data.index = pd.to_datetime(data.index)

    start_time = time.time()    
    modified = overwrite_parameter(CZ, data, 'T_Outdoor_F', 't_outdoor_drybulb')
    modified = overwrite_parameter(CZ, modified, 'Water_RemoteTemp_F', 't_Inlet')

    time_required = time.time() - start_time
    print('Process completed in {}s'.format(time_required))
    
    assumption = pd.read_csv(os.path.join('CBECC Inputs', 'RESULTSDHWHR_CZ{}.csv'.format(CZ)),
                             skiprows=3)   
    assumption.loc[0, 'Timestamp'] = datetime.datetime(2021, 1, 1, 0)
    assumption.loc[1:, 'Timestamp'] = assumption.loc[0, 'Timestamp'] + pd.to_timedelta(assumption.index[1:], unit = 'h')
    assumption['Timestamp'] = assumption['Timestamp'].map(remove_one_year)
    assumption.index = assumption['Timestamp'] 
    assumption = assumption.sort_index()
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(data['T_Outdoor_F'], label = 'Monitored')
    plt.plot(modified['T_Outdoor_F'], label = 'Modified')
    plt.plot(assumption['t_outdoor_drybulb'], label = 'Assumption')
    plt.ylabel('Outdoor Air Temperature (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))
    plt.legend()
    
    diff = modified['T_Outdoor_F'] - assumption['t_outdoor_drybulb']
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(diff)
    plt.ylabel('Difference Between Modified and Assumption (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))

    fig = plt.figure(figsize = (12, 6))
    plt.plot(data['Water_RemoteTemp_F'], label = 'Monitored')
    plt.plot(modified['Water_RemoteTemp_F'], label = 'Modified')
    plt.plot(assumption['t_Inlet'], label = 'Assumption')
    plt.ylabel('Inlet Water Temperature (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))
    plt.legend()
    
    diff = modified['Water_RemoteTemp_F'] - assumption['t_Inlet']
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(diff)
    plt.ylabel('Difference Between Modified and Assumption (\N{DEGREE SIGN}F)')    
    plt.title('CZ = {}'.format(CZ))
    
    print('Testing with CZ = 16')
    CZ = '16'
    Path_DrawProfile = cwd + r'\Input\Creekside Data for {}.csv'.format(case)
    
    data = pd.read_csv(Path_DrawProfile, index_col = 0)
    data.index = pd.to_datetime(data.index)

    start_time = time.time()    
    modified = overwrite_parameter(CZ, data, 'T_Outdoor_F', 't_outdoor_drybulb')
    modified = overwrite_parameter(CZ, modified, 'Water_RemoteTemp_F', 't_Inlet')

    time_required = time.time() - start_time
    print('Process completed in {}s'.format(time_required))
    
    assumption = pd.read_csv(os.path.join('CBECC Inputs', 'RESULTSDHWHR_CZ{}.csv'.format(CZ)),
                             skiprows=3)   
    assumption['Timestamp'] = assumption['Mo'].astype(str) + ' ' + assumption['Day'].astype(str) \
        + ' ' + (assumption['Hour'] - 1).astype(str)
    assumption['Timestamp'] = pd.to_datetime(assumption['Timestamp'], format = '%m %d %H')  
    assumption.loc[0, 'Timestamp'] = datetime.datetime(2021, 1, 1, 0)
    assumption.loc[1:, 'Timestamp'] = assumption.loc[0, 'Timestamp'] + pd.to_timedelta(assumption.index[1:], unit = 'h')
    assumption['Timestamp'] = assumption['Timestamp'].map(remove_one_year)
    assumption.index = assumption['Timestamp'] 
    assumption = assumption.sort_index()
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(data['T_Outdoor_F'], label = 'Monitored')
    plt.plot(modified['T_Outdoor_F'], label = 'Modified')
    plt.plot(assumption['t_outdoor_drybulb'], label = 'Assumption')
    plt.ylabel('Outdoor Air Temperature (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))
    plt.legend()
    
    diff = modified['T_Outdoor_F'] - assumption['t_outdoor_drybulb']
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(diff)
    plt.ylabel('Difference Between Modified and Assumption (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))

    fig = plt.figure(figsize = (12, 6))
    plt.plot(data['Water_RemoteTemp_F'], label = 'Monitored')
    plt.plot(modified['Water_RemoteTemp_F'], label = 'Modified')
    plt.plot(assumption['t_Inlet'], label = 'Assumption')
    plt.ylabel('Inlet Water Temperature (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))
    plt.legend()
    
    diff = modified['Water_RemoteTemp_F'] - assumption['t_Inlet']
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(diff)
    plt.ylabel('Difference Between Modified and Assumption (\N{DEGREE SIGN}F)')       
    plt.title('CZ = {}'.format(CZ))
    
    print('Testing with CZ = 12')
    CZ = '12'
    Path_DrawProfile = cwd + r'\Input\Creekside Data for {}.csv'.format(case)
    
    data = pd.read_csv(Path_DrawProfile, index_col = 0)
    data.index = pd.to_datetime(data.index)

    start_time = time.time()    
    modified = overwrite_parameter(CZ, data, 'T_Outdoor_F', 't_outdoor_drybulb')
    modified = overwrite_parameter(CZ, modified, 'Water_RemoteTemp_F', 't_Inlet')

    time_required = time.time() - start_time
    print('Process completed in {}s'.format(time_required))
    
    assumption = pd.read_csv(os.path.join('CBECC Inputs', 'RESULTSDHWHR_CZ{}.csv'.format(CZ)),
                             skiprows=3)   
    assumption['Timestamp'] = assumption['Mo'].astype(str) + ' ' + assumption['Day'].astype(str) \
        + ' ' + (assumption['Hour'] - 1).astype(str)
    assumption['Timestamp'] = pd.to_datetime(assumption['Timestamp'], format = '%m %d %H')  
    assumption.loc[0, 'Timestamp'] = datetime.datetime(2021, 1, 1, 0)
    assumption.loc[1:, 'Timestamp'] = assumption.loc[0, 'Timestamp'] + pd.to_timedelta(assumption.index[1:], unit = 'h')
    assumption['Timestamp'] = assumption['Timestamp'].map(remove_one_year)
    assumption.index = assumption['Timestamp'] 
    assumption = assumption.sort_index()
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(data['T_Outdoor_F'], label = 'Monitored')
    plt.plot(modified['T_Outdoor_F'], label = 'Modified')
    plt.plot(assumption['t_outdoor_drybulb'], label = 'Assumption')
    plt.ylabel('Outdoor Air Temperature (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))
    plt.legend()
    
    diff = modified['T_Outdoor_F'] - assumption['t_outdoor_drybulb']
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(diff)
    plt.ylabel('Difference Between Modified and Assumption (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))

    fig = plt.figure(figsize = (12, 6))
    plt.plot(data['Water_RemoteTemp_F'], label = 'Monitored')
    plt.plot(modified['Water_RemoteTemp_F'], label = 'Modified')
    plt.plot(assumption['t_Inlet'], label = 'Assumption')
    plt.ylabel('Inlet Water Temperature (\N{DEGREE SIGN}F)')
    plt.title('CZ = {}'.format(CZ))
    plt.legend()
    
    diff = modified['Water_RemoteTemp_F'] - assumption['t_Inlet']
    
    fig = plt.figure(figsize = (12, 6))
    plt.plot(diff)
    plt.ylabel('Difference Between Modified and Assumption (\N{DEGREE SIGN}F)')  
    plt.title('CZ = {}'.format(CZ))       