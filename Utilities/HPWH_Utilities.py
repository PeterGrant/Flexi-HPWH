# -*- coding: utf-8 -*-
"""
Created on Sun Sep 19 08:20:35 2021

This script contains utility functions that can be used when performing simulations
with Flexi-HPWH.

@author: Peter Grant
"""

import time
import pandas as pd
import math
import numpy as np
import os
import sys
from Installation_Configuration import get_temperatures
from Set_Temperature_Profiles import get_profile
from CZ_Assumptions import overwrite_parameter
from sklearn.metrics import mean_squared_error

cwd = os.getcwd()
sys.path.append(cwd, '..')
from HPWH_Model import HPWH_MultipleNodes

#Constants used in water-based calculations
SpecificHeat_Water = 4.190 #J/g-C
Density_Water = 1000 #g/L
Update_Frequency = 60 # Prints a status update after this many seconds
kWh_In_J = 2.7777777777e-7 #kWh per J

#Constants used for unit conversions
Hours_In_Day = 24 #The number of hours in a day
Minutes_In_Hour = 60 #The number of minutes in an hour
Seconds_In_Minute = 60 #The number of seconds in a minute
W_To_BtuPerHour = 3.412142 #Converting from Watts to Btu/hr
K_To_F_MagnitudeOnly = 1.8/1. #Converting from K/C to F. Only applicable for magnitudes, not actual temperatures (E.g. Yes for "A temperature difference of 10 C" but not for "The water temperature is 40 C")
Btu_Per_CubicFoot_NaturalGas = 1015 #Energy density of natural gas, in Btu/ft^3
Btu_Per_WattHour = 3.412142 #Conversion factor between Btu nad W-h
Btu_In_Therm = 100000 #The number of Btus in a therm
Pounds_In_MetricTon = 2204.62 #Pounds in a metric ton
Pounds_In_Ton = 2000 #Pounds in a US ton
kWh_In_MWh = 1000 #kWh in MWh
Liters_In_Gallon = 3.78541 #The number of liters in a gallon
Temperature_MixingValve_Set = 48.9

def Prepare_Creekside_DrawProfile(data, config, Installation_Configuration, note):
    '''
    This function accepts a Creekside draw profile and performs the
    calculations needed to convert it to SI units and return the Flexi-HPWH
    input data set.
    
    This function does not include filtering the data set to specified days.
    If that is necessary do it before calling this function.
    
    inputs:
        data: The Creekside draw profile being used in this simulaiton.
        config: The configuration file used to specify the HPWH.
        Installation_Configuration: The manner in which this HPWH is installed.
                                    Must match an entry in Installation_Configuration.py
    '''
    
    Draw_Profile = data.copy(deep = True)
    
    # Add time data to the draw profile
    Draw_Profile['Timestamp'] = Draw_Profile.index
    Draw_Profile['Time (s)'] = (Draw_Profile.index - Draw_Profile.index[0]).total_seconds()
    Draw_Profile['Time (min)'] = Draw_Profile['Time (s)'] / 60.
    Draw_Profile['Hour'] = pd.DatetimeIndex(Draw_Profile['Timestamp']).hour    
    
    # The Creekside data set used multiple loggers sampling at different frequencies.
    # Fill the blanks caused by this
    Draw_Profile = Draw_Profile.fillna(method='ffill') #Fills empty cells by projecting the most recent reading forward to the next reading
    Draw_Profile = Draw_Profile.fillna(method='bfill') #Fills empty cells by copying the following reading into these cells. Note that this only happens for cells at the start of the data set because all other cells were filled by the previous line

    Draw_Profile['Month'] = Draw_Profile['Timestamp'].dt.month
    Draw_Profile['Month'] = Draw_Profile['Month'].astype(int)
    Draw_Profile['Day'] = Draw_Profile['Timestamp'].dt.day
    Draw_Profile['Day'] = Draw_Profile['Day'].astype(int)

    Draw_Profile['Time (hr)'] = Draw_Profile['Time (min)'] / Minutes_In_Hour #Creates new column representing the simulation time in hours instead of minutes

    #These lines calculate the time change between two rows in the data set and calculate the timestep for use in calculations
    Draw_Profile['Time shifted (min)'] = Draw_Profile['Time (min)'].shift(1)
    Draw_Profile['Time shifted (min)'].iloc[0] = Draw_Profile['Time (min)'].iloc[0]
    Draw_Profile['Timestep (min)'] =  Draw_Profile['Time (min)'] - Draw_Profile['Time shifted (min)']
    Draw_Profile = Draw_Profile[Draw_Profile['Timestep (min)'] != 0]
    Draw_Profile['Timestep (min)'] = np.minimum(0.25, Draw_Profile['Timestep (min)'])
#    Draw_Profile = Draw_Profile.reset_index(inplace = True) #Do not delete this when removing the Creekside, 3FCA filter
#    del Draw_Profile['index'] #Do not delete this when removing the Creekside, 3FCA filter

    if note.startswith('CZ'):
        cz = note.split(' ')[-1]
        if len(cz) == 1:
            cz = '0' + cz
        print('Changing inlet assumptions to CZ {}'.format(cz))
        Draw_Profile = overwrite_parameter(cz, Draw_Profile, 
                                                 'Water_RemoteTemp_F',
                                                 't_Inlet')
        
        Draw_Profile = overwrite_parameter(cz, Draw_Profile, 
                                                 'T_Outdoor_F',
                                                 't_outdoor_drybulb')        

    # Convert IP units to SI units
    Draw_Profile['Water_FlowRate_LPerMin'] = Draw_Profile['Water_FlowRate_gpm'] * Liters_In_Gallon #Creates a new column representing the measured water flow rate, converted from gal/min to L/min
    Draw_Profile['Water_FlowTotal_L'] = Draw_Profile['Water_FlowTotal_gal'] * Liters_In_Gallon #Creates a new column representing the total measured water flow, converted from gal to L
    Draw_Profile['Water_FlowTemp_C'] = (Draw_Profile['Water_FlowTemp_F']-32) * 1/K_To_F_MagnitudeOnly #Creates a new column representing the outlet water temperature, converted from F to C
    Draw_Profile['Water_RemoteTemp_C'] = (Draw_Profile['Water_RemoteTemp_F']-32) * 1/K_To_F_MagnitudeOnly #Creates a new column representing the inlet water temperature, converted from F to C
    Draw_Profile['Inlet Water Temperature (deg C)'] = Draw_Profile['Water_RemoteTemp_C']
    Draw_Profile['Set Temperature (deg C)'] = (Draw_Profile['T_Setpoint_F']-32) * 1/K_To_F_MagnitudeOnly #Create a column in the Draw_Profile representing the user-supplied, possibly varying, set temperature in deg C. If Variable_Set_Temperature == 1 this will be the set temperature used in the Draw_Profile
    Draw_Profile['Power_EnergyCumsum_kWh'] = Draw_Profile['Power_EnergySum_kWh'].cumsum()
    Draw_Profile['T_Ambient_EcoNet_C'] = (Draw_Profile['T_Ambient_EcoNet_F']-32) * 1/K_To_F_MagnitudeOnly #Creates a new column representing the ambient temperature, converted from F to C
    Draw_Profile['Ambient Temperature (deg C)'] = (Draw_Profile['T_Cabinet_F']-32) * 1/K_To_F_MagnitudeOnly #Creates a new column representing the air temperature in the cabinet, converted from F to C
    Draw_Profile['T_Tank_Upper_C'] = (Draw_Profile['T_TankUpper_F']-32) * 1/K_To_F_MagnitudeOnly #Creates a new column representing the water temperature reported by the upper thermostat in the tank, converted from F to C
    Draw_Profile['T_Tank_Lower_C'] = (Draw_Profile['T_TankLower_F']-32) * 1/K_To_F_MagnitudeOnly #Creates a new column representing the water temperature reported by the lower thermostat in the tank, converted from F to C
    Draw_Profile['Timestamp'] = pd.to_datetime(Draw_Profile['Timestamp'])
    Draw_Profile['Outdoor Temperature (deg C)'] = (Draw_Profile['T_Outdoor_F']-32) * 1/K_To_F_MagnitudeOnly
    
    # Estimate the hot water draw volume based on the temperatures and the 
    # mixing valve set temperature
    Draw_Profile['Water Draw Volume (L)'] = np.minimum(4, Draw_Profile['Water_FlowTotal_L'])
    Draw_Profile['Calculated Water Draw Volume (L)'] = (Draw_Profile['Water Draw Volume (L)'] * Draw_Profile['Water_RemoteTemp_C'] - 
         Draw_Profile['Water Draw Volume (L)'] * Temperature_MixingValve_Set) / (Draw_Profile['Water_RemoteTemp_C'] - 
         Draw_Profile['T_Tank_Upper_C'])
    Draw_Profile['Hot Water Draw Volume (L)'] = np.minimum(Draw_Profile['Calculated Water Draw Volume (L)'],
         Draw_Profile['Water Draw Volume (L)'])    
    
    # Get the ambient and evaporator air inlet temperatures 
    Draw_Profile = get_temperatures(Draw_Profile, Installation_Configuration)
    # Smooth the set temperature profile, removing odd blips in EcoNet data
#    Draw_Profile.index = Draw_Profile['Timestamp']
    shift_start = 8
    shift_end = 16
    Draw_Profile.loc[Draw_Profile.index.hour < shift_start, 'Set Temperature (deg C)'] = 51.6666
    Draw_Profile.loc[Draw_Profile.index.hour > shift_end, 'Set Temperature (deg C)'] = 51.6666  
    
    return Draw_Profile

def Calculate_InitialTemps_Creekside(config, Draw_Profile):
    
    # Initialize tank temperatures using a linear regression between the measured
    # upper and lower thermostat temperatures
    x = [config['Lower Thermostat Node'], config['Upper Thermostat Node']]
    y = [Draw_Profile.loc[Draw_Profile.index[0], 'T_Tank_Lower_C'], Draw_Profile.loc[Draw_Profile.index[0], 'T_Tank_Upper_C']]
    coefficients = np.polyfit(x, y, 1)
    regression = np.poly1d(coefficients)
    Nodes = range(config['Number of Nodes'])
    config['Node Temperatures (deg C)'] = regression(Nodes)
    
    return config
    
def Prepare_Creekside_InputData(Draw_Profile, config):
    
    # Create the input data set, taking a reduced subset of the columns
    input_data = Draw_Profile.copy(deep = True)
    input_data = input_data[['Set Temperature (deg C)', 'Ambient Temperature (deg C)', 
                             'Timestep (min)', 'Inlet Water Temperature (deg C)', 'Water Draw Volume (L)',
                             'Water_RemoteTemp_C', 'Hot Water Draw Volume (L)', 
                             'Calculated Water Draw Volume (L)', 'Evaporator Air Inlet Temperature (deg C)']]

    # Initialize model output columns
    input_data['Jacket Losses (kWh)'] = 0
    input_data['Energy Withdrawn (kWh)'] = 0
    input_data['Heat Added Heat Pump (kWh)'] = 0
    input_data['Heat Added Backup (kWh)'] = 0    
    input_data['Total Energy Change (kWh)'] = 0  
    input_data['Node Temperatures (deg C)'] = 0
#    input_data['COP Adjust Tamb'] = 0
    input_data['PowerMultiplier'] = 0
    input_data['Electricity Consumed Heat Pump (kWh)'] = 0
    input_data['Electricity Consumed Resistance (kWh)'] = 0
    input_data['Electricity Consumed Total (kWh)'] = 0
    input_data['Total Jacket Losses (kWh)'] = 0
    input_data['Total Energy Withdrawn (kWh)'] = 0
    input_data['Total Heat Added Heat Pump (kWh)'] = 0
    input_data['Total Heat Added Backup (kWh)'] = 0
    input_data['Total Heat Added (kWh)'] = 0
    input_data['Node Energy Change (kWh)'] = 0
#    input_data['Time Elapsed (s)'] = 0
    input_data['Heat Pump Heat Addition (kW)'] = 0
    input_data['Time Since Set Change (s)'] = 0
    input_data['Heat Pump Deadband (deg C)'] = 0
    input_data['Resistance Set Temperature (deg C)'] = 0
    input_data['Resistance Set Temperature, HP Active (deg C)'] = 0

    # Add the column index to the configuration
    col_index = dict(zip(input_data.columns, list(range(0,len(input_data.columns)))))
    config['Column Index'] = col_index
    input_data = input_data.to_numpy()
    input_data = input_data.astype('object')   
    
    print('created input data set')
    
    return input_data, config
    
def calc_rmse(Model, config, rejected, Update_Frequency):
    
        Model_month = Model.copy(deep = True)
        Model_month['Power_EnergySum_kWh'] -= Model_month.loc[Model_month.index[0], 'Power_EnergySum_kWh']
        print('First timestep is {} min'.format(Model_month.loc[Model_month.index[0], 'Timestep (min)']))      

        input_data = Model_month.copy(deep = True)
        input_data = input_data[['Set Temperature (deg C)', 'Ambient Temperature (deg C)', 
           'Timestep (min)', 'Inlet Water Temperature (deg C)',
           'Hot Water Draw Volume (L)', 'Evaporator Air Inlet Temperature (deg C)']]

        input_data['Jacket Losses (kWh)'] = 0
        input_data['Energy Withdrawn (kWh)'] = 0
        input_data['Heat Added Heat Pump (kWh)'] = 0
        input_data['Heat Added Backup (kWh)'] = 0    
        input_data['Total Energy Change (kWh)'] = 0  
        input_data['Node Temperatures (deg C)'] = 0
        input_data['COP Adjust Tamb'] = 0
        input_data['COP'] = 0
        input_data['Electricity Consumed Heat Pump (kWh)'] = 0
        input_data['Electricity Consumed Resistance (kWh)'] = 0
        input_data['Electricity Consumed Total (kWh)'] = 0
        input_data['Total Jacket Losses (kWh)'] = 0
        input_data['Total Energy Withdrawn (kWh)'] = 0
        input_data['Total Heat Added Heat Pump (kWh)'] = 0
        input_data['Total Heat Added Backup (kWh)'] = 0
        input_data['Total Heat Added (kWh)'] = 0
        input_data['Node Energy Change (kWh)'] = 0
        input_data['Heat Pump Heat Addition (kW)'] = 0
        print(input_data.index)
        col_index = dict(zip(input_data.columns, list(range(0,len(input_data.columns)))))
        config['Column Index'] = col_index
        input_data = input_data.to_numpy()
        input_data = input_data.astype('object')

        print('created input data set')

        HPWH = HPWH_MultipleNodes(config)
        print('initialized model')

        start_time = time.time()

        print('{} timestamps'.format(len(input_data)))

        Time_Since_Update = time.time()
        for row in range(0, len(input_data)):
            timestamp = Model_month.loc[Model_month.index[row], 'Timestamp']
            prior_date = timestamp - pd.Timedelta(1, unit = 'd')
            if len(rejected.index > 0):
                if prior_date in rejected.index:
                    print('Re-initializing at {}'.format(timestamp))
                    x = [config['Lower Thermostat Node'], config['Upper Thermostat Node']]
                    y = [Model_month.loc[timestamp, 'T_Tank_Lower_C'], Model_month.loc[timestamp, 'T_Tank_Upper_C']]
                    coefficients = np.polyfit(x, y, 1)
                    regression = np.poly1d(coefficients)
                    Nodes = range(config['Number of Nodes'])
                    HPWH.Node_Temperatures = regression(Nodes)
                    input_data[row, col_index['Timestep (min)']] = 0
                    dQ_Measured = Model_month.loc[Model_month.index[row], 'Power_EnergySum_kWh'] - Model_month.loc[Model_month.index[row-1], 'Power_EnergySum_kWh']
                    Model_month.loc[Model_month.index[row]:, 'Power_EnergySum_kWh'] += -dQ_Measured
            output = HPWH.calculate_timestep(input_data[row])

            input_data[row] = output

            if time.time() - Time_Since_Update >= Update_Frequency:
                print('completed timestamp {}'.format(timestamp))
                Time_Since_Update = time.time()
                
        result = pd.DataFrame(input_data, index = Model.index, columns = col_index.keys())
        end_time = time.time()
        print('processing time is {}'.format(end_time - start_time))
        print('time per iteration is {}'.format((end_time - start_time)/len(input_data)))

        columns = []
        for i in range(len(result.loc[result.index[0], 'Node Temperatures (deg C)'])):
            columns.append('Node Temperature {} (deg C)'.format(i))
        result[columns] = pd.DataFrame(result['Node Temperatures (deg C)'].tolist(), index = result.index)

        if result['Node Temperature {} (deg C)'.format(HPWH.Lower_Thermostat_Node)].isnull().values.any() == False:
            rmse = math.sqrt(mean_squared_error(Model_month['T_Tank_Lower_C'], result['Node Temperature {} (deg C)'.format(HPWH.Lower_Thermostat_Node)]))
        else:
            print('config yielded NaN')
            rmse = 1000

        Model_month['T_Tank_Lower_C'].plot(figsize = (12, 6))
        result['Node Temperature {} (deg C)'.format(HPWH.Lower_Thermostat_Node)].plot(figsize = (12, 6))
        
        print('rmse is {}'.format(rmse))
        
def Simulate_MonitoredData(Draw_Profile, config, Set_Temperature_Profile, Installation_Configuration, 
                           output_folder, Simulation_Name, Case_Type, note, Reduced_Output, summary, 
                           simulation):
    '''
    This function can be called to run a simulation using monitored data
    from Creekside. It is used by the multi simulation tool
    
    inputs:
        Draw_Profile: The draw profile used in this simulation
        config: The configuration file for the HPWH
        Set_Temperature_Profile: The name of the set temperature profile to
            use in the simulation. Must match a profile indicated in 
            Set_Temperature_Profiles.py
        Installation_Configuration: The name of the installation configuration
           to use in the simulation. Must match a configuration listed in 
           Installation_Configuration.py
        Simulation_Name: The name of the simulation to use when saving results.
        Case_Type: Enables control of cases with different numbers of dwellings
            served by the HPWH. Options are 'SF', '3', and '4'.
            SF: Reduces the flow rate used in the simulation to 25%. Used
            when simulating a HPWH connected to a single dwelling.
            '3': Reduces the flow rate in the simulation to 75%. Used when
            simulating a HPWH connected to 3 dwellings.
            '4': Does not modify the flow rate. Used when simulating the 4
            dwellings served by each HPWH in the monitoring data.
        note: A note specified in the test matrix. Can be any note, but must
            match expectations in this script if an action is desired
        Reduced_Output: A boolean flag stating whether this script should
            reduce the columns tored in the output file or not.
        summary: A dataframe summarizing the test cases and results in this
            series of simulations. The script will store results in new columns
            in this file.
        simulation: The test number of the current simulation.
    '''
    
    print('In Simulate_MonitoredData')
    beginning = time.time()

    Draw_Profile = Prepare_Creekside_DrawProfile(Draw_Profile, 
                                                 config, 
                                                 Installation_Configuration,
                                                 note)
    if Set_Temperature_Profile != False:    
        Temperature_Tank_Set = get_profile(Set_Temperature_Profile)
        Draw_Profile['Hour'] = Draw_Profile['Hour'].astype(str)
        Draw_Profile['Set Temperature (deg C)'] = Draw_Profile['Hour'].map(Temperature_Tank_Set)
        Draw_Profile['Hour'] = Draw_Profile['Hour'].astype(int)    

    if Case_Type == 'SF':
        print('Reducing flow to 25%')
        Draw_Profile['Water Draw Volume (L)'] = Draw_Profile['Water Draw Volume (L)'] * 0.25
    elif Case_Type == '3':
        print('Reducing flow to 75%')
        Draw_Profile['Water Draw Volume (L)'] = Draw_Profile['Water Draw Volume (L)'] * 0.75
    
    config = Calculate_InitialTemps_Creekside(config, Draw_Profile)
    input_data, config = Prepare_Creekside_InputData(Draw_Profile, config)
    col_index = config['Column Index']

    HPWH = HPWH_MultipleNodes(config)
    print('Compressor size is {}'.format(HPWH.HeatAddition_HeatPump))
    print('Tank volume is {}'.format(HPWH.ThermalMass_Tank / (SpecificHeat_Water * Density_Water * kWh_In_J)))
    print('Jacket loss coefficient is {}'.format(HPWH.Coefficient_JacketLoss))
    print('initialized model')

    start_time = time.time()
    print('preparation time is {}'.format(start_time - beginning))

    print('{} timestamps'.format(len(input_data)))

    result = pd.DataFrame(columns = col_index.keys())
    Time_Last_Update = time.time()
    adjusting_ER = False
    for row in range(0, len(input_data)):
        timestamp = Draw_Profile.loc[Draw_Profile.index[row], 'Timestamp']
        Set_Temperature = Draw_Profile.loc[Draw_Profile.index[row], 'Set Temperature (deg C)']
        if note.startswith('ER'):
            adjusting_ER = True
            if Set_Temperature != 51.6:
                HPWH.Upper_Resistance_Deadband = Set_Temperature - 40.55
                HPWH.Upper_Resistance_Deadband_HPActive = Set_Temperature - 40.55
            else:
                HPWH.Upper_Resistance_Deadband = config['Resistance Deadband (deg C)']
                HPWH.Upper_Resistance_Deadband_HPActive = config['Resistance Deadband, HP Active (deg C)']
        input_data[row, col_index['Resistance Set Temperature (deg C)']] = Set_Temperature - HPWH.Upper_Resistance_Deadband
        input_data[row, col_index['Resistance Set Temperature, HP Active (deg C)']] = Set_Temperature - HPWH.Upper_Resistance_Deadband_HPActive
        
        input_data[row, col_index['Calculated Water Draw Volume (L)']] = (input_data[row, col_index['Water Draw Volume (L)']] * input_data[row, col_index['Water_RemoteTemp_C']] - 
            input_data[row, col_index['Water Draw Volume (L)']] * Temperature_MixingValve_Set) / (input_data[row, col_index['Water_RemoteTemp_C']] - HPWH.Node_Temperatures[HPWH.Upper_Thermostat_Node])
        input_data[row, col_index['Hot Water Draw Volume (L)']] = np.minimum(input_data[row, col_index['Calculated Water Draw Volume (L)']],
            input_data[row, col_index['Water Draw Volume (L)']])        

        output = HPWH.calculate_timestep(input_data[row])

        input_data[row] = output
     
        if time.time() - Time_Last_Update >= Update_Frequency:
            print('completed timestamp {}'.format(timestamp))
            Time_Last_Update = time.time()

    result = pd.DataFrame(input_data, index = Draw_Profile.index, columns = col_index.keys())
    
    # Extract water temperatures for each node
    columns = []
    for i in range(len(result.loc[result.index[0], 'Node Temperatures (deg C)'])):
        columns.append('Node Temperature {} (deg C)'.format(i))
    result[columns] = pd.DataFrame(result['Node Temperatures (deg C)'].tolist(), index = result.index)    
    result['Energy Supplied (kWh)'] = result['Hot Water Draw Volume (L)'] * SpecificHeat_Water * Density_Water * (result['Node Temperature 19 (deg C)'] - result['Inlet Water Temperature (deg C)']) * 2.7777777777e-7

    print('ER adjustement: {}'.format(adjusting_ER))

    summary.loc[simulation, 'Electricity Consumed (kWh)'] = result['Electricity Consumed Total (kWh)'].sum()
    summary.loc[simulation, 'Electricity Consumed Heat Pump (kWh)'] = result['Electricity Consumed Heat Pump (kWh)'].sum()
    summary.loc[simulation, 'Energy Added Heat Pump (kWh)'] = result['Total Heat Added Heat Pump (kWh)'].sum()
    summary.loc[simulation, 'Electricity Consumed Backup (kWh)'] = result['Electricity Consumed Resistance (kWh)'].sum()
    summary.loc[simulation, 'Jacket Losses (kWh)'] = result['Total Jacket Losses (kWh)'].sum()
    summary.loc[simulation, 'Mean Ambient Temperature (deg F)'] = 1.8 * result['Ambient Temperature (deg C)'].mean() + 32
    summary.loc[simulation, 'Min Ambient Temperature (deg F)'] = 1.8 * result['Ambient Temperature (deg C)'].min() + 32
    summary.loc[simulation, 'Max Ambient Temperature (deg F)'] = 1.8 * result['Ambient Temperature (deg C)'].max() + 32
    summary.loc[simulation, 'Mean Evaporator Air Inlet Temperature (deg F)'] = 1.8 * result['Evaporator Air Inlet Temperature (deg C)'].mean() + 32
    summary.loc[simulation, 'Average Inlet Temperature (deg F)'] = 1.8 * result['Inlet Water Temperature (deg C)'].mean() + 32
    summary.loc[simulation, 'Average Heat Pump COP'] = summary.loc[simulation, 'Energy Added Heat Pump (kWh)'] / summary.loc[simulation, 'Electricity Consumed Heat Pump (kWh)']
    summary.loc[simulation, 'Electricity Consumed Peak (kWh, 4-9P)'] = result.loc[(result.index.hour >= 16) & (result.index.hour < 21), 'Electricity Consumed Total (kWh)'].sum()
    summary.loc[simulation, 'Water Draw Volume (gal)'] = result['Water Draw Volume (L)'].sum() / Liters_In_Gallon
    summary.loc[simulation, 'Annual COP'] = result['Energy Supplied (kWh)'].sum() / summary.loc[simulation, 'Electricity Consumed (kWh)']
    
    daily = result[['Energy Supplied (kWh)', 'Electricity Consumed Total (kWh)', 'Electricity Consumed Heat Pump (kWh)', 'Electricity Consumed Resistance (kWh)']].groupby(result.index.date).sum()
    daily['HPWH COP'] = daily['Energy Supplied (kWh)'] / daily['Electricity Consumed Total (kWh)']
    
    monthly = result[['Energy Supplied (kWh)', 'Electricity Consumed Total (kWh)', 'Electricity Consumed Heat Pump (kWh)', 'Electricity Consumed Resistance (kWh)']].groupby(result.index.month).sum()
    monthly['HPWH COP'] = monthly['Energy Supplied (kWh)'] / monthly['Electricity Consumed Total (kWh)']
    
    Simulation_Number = Simulation_Name.split('_')[-1].split('.')[0]
    


#    This code calculates the predicted volume of water delivered below 112 deg F
#    It is currently commented out because the model tends to underpredict runouts
#    columns = []
#    for i in range(len(result.loc[result.index[0], 'Node Temperatures (deg C)'])):
#        columns.append('Node Temperature {} (deg C)'.format(i))
#    result[columns] = pd.DataFrame(result['Node Temperatures (deg C)'].tolist(), index = result.index)
#    summary.loc[simulation, 'Volume Delivered Below 112 deg F (gal)'] = result.loc[result['Node Temperature {} (deg C)'.format(HPWH.Upper_Thermostat_Node)] < (112-32)/1.8, 'Hot Water Draw Volume (L)'].sum() / Liters_In_Gallon

    if Reduced_Output == True:
        print('Reducing output file')
        result = result[['Electricity Consumed Heat Pump (kWh)', 'Electricity Consumed Resistance (kWh)', 'Electricity Consumed Total (kWh)']]

    end_time = time.time()
    print('processing time is {} min'.format((end_time - start_time)/Seconds_In_Minute))
    print('time per iteration is {}'.format((end_time - start_time)/len(input_data)))    
    print('Electricity consumption is {}'.format(result['Electricity Consumed Total (kWh)'].sum()))
    
    cumsum = result['Electricity Consumed Total (kWh)'].cumsum()
    cumsum.plot(figsize = (12, 6))

    import os
    output_path = os.path.join(output_folder, Simulation_Name)
    result.to_csv(output_path)
    
    daily.to_csv(os.path.join(output_folder, 'daily COP', 'daily_COP_{}.csv'.format(Simulation_Number)))
    monthly.to_csv(os.path.join(output_folder, 'monthly COP', 'monthly_COP_{}.csv'.format(Simulation_Number)))

    return summary
    