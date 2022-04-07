# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 19:17:36 2021

This script iteratively performs many simulations using the Multi-Node version
of Flexi-HPWH. It was designed specifically for the Creekside project, but
can be modified for other projects as needed.

@author: Peter Grant
"""

import pandas as pd
import os
import json
from HPWH_Utilities import Simulate_MonitoredData

# Use the following code for Creekside load shifting evaluation

cwd = os.getcwd()
Folder = cwd
File = 'Test_Cases.csv'
Test_Cases = pd.read_csv(os.path.join(Folder, File), index_col = 0)
Installation_Configuration = 'Ducted_Exhaust'
Two_Week_Sim = False # Set to True for testing simulations, False for simulations using the full draw profile
Output_Folder = os.path.join(cwd, '..', 'Output')
Used_Inputs = pd.DataFrame(index = Test_Cases.index)
Simulation_Name = 'ExampleSimulation'

Case_Previous = None
for Simulation in Test_Cases.index:
    
    if Two_Week_Sim == True:
        Simulation_Name = '{}_Testing_{}.csv'.format(Simulation_Name, Simulation)
    else:
        Simulation_Name = '{}_Annual_{}.csv'.format(Simulation_Name, Simulation)
    
    case = Test_Cases.loc[Simulation, 'Draw Profile Source']

    # If the simulation is a single dwelling case
    if ' * 25%' in case:
        print('SF case found')
        case = case[0:4].replace(' ', '')
        Case_Type = 'SF'
    elif ' * 75%' in case:
        print('3 dwelling case found')
        case = case[0:4].replace(' ', '')
        Case_Type = '3'
    else:
        Case_Type = '4'
        
    # To avoid issues with Excel saving 3E98 as scientific notation...
    if case == '398':
        case = '3E98'
        
    set_temperature_profile = Test_Cases.loc[Simulation, 'Set Temperature Profile']
    note = str(Test_Cases.loc[Simulation, 'Notes'])

    # Print the details of the simulation for error checking
    print('simulation number {}'.format(Simulation))
    print('case is {}'.format(case))
    print('Case_Type is {}'.format(Case_Type))
    print('set temperature profile is {}'.format(set_temperature_profile))
    print('note is {}'.format(note))
    
    Used_Inputs.loc[Simulation, 'Case'] = case
    Used_Inputs.loc[Simulation, 'Case Type'] = Case_Type
    Used_Inputs.loc[Simulation, 'Set Temperature Profile'] = set_temperature_profile
    Used_Inputs.loc[Simulation, 'note'] = note
    
    # Only read config or draw profile if necessary
    if case != Case_Previous:

        # Get the configuration
        Config = 'Rheem_PROPH80_Config.txt'
        Path_Config = os.path.join(cwd, Config)
        print('Path_Config is {}'.format(Path_Config))        
        
        with open(Path_Config) as f:
            data = f.read()
        config = json.loads(data)
        print('read config')
        
        Path_DrawProfile = os.path.join(cwd, '..', 'Input',  'ExampleInput.csv')
        print('Path_DrawProfile is {}'.format(Path_DrawProfile))
        Draw_Profile = pd.read_csv(Path_DrawProfile, index_col = 0)
        Draw_Profile.index = pd.to_datetime(Draw_Profile.index)
        
#         Limits to the first two weeks for testing
        if Two_Week_Sim == True:
            Draw_Profile = Draw_Profile[Draw_Profile.index[0].month]
            Draw_Profile = Draw_Profile[Draw_Profile.index.day < 15]
            Reduced_Output = False
            print(Draw_Profile.index)
        else:
            Reduced_Output = True
        
    # If this is simulating a single family case reduce the size and UA losses
    # of the storage tank
    if Case_Type == 'SF':
        config['Volume Tank (L)'] = 170.34
        config['Jacket Loss Coefficient (W/K)'] = 2.8 * 0.83
    elif Case_Type == '3':
        config['Volume Tank (L)'] = 280
        config['Jacket Loss Coefficient (W/K)'] = 2.8
    elif '100 gal' in note:
        config['Volume Tank (L)'] = 340.69
        config['Jacket Loss Coefficient (W/K)'] = 2.8 * 1.112
    else:
        config['Volume Tank (L)'] = 280
        config['Jacket Loss Coefficient (W/K)'] = 2.8
    
    if '3516.85 W' in note:
        config['Heat Pump Heat Addition Rate (W)'] = 3516.85
    else:
        config['Heat Pump Heat Addition Rate (W)'] = 1230.9
        
    print('Compressor size is {}'.format(config['Heat Pump Heat Addition Rate (W)']))
    print('Tank volume is : {}'.format(config['Volume Tank (L)']))
    print('UA is {}'.format(config['Jacket Loss Coefficient (W/K)']))  

    Used_Inputs.loc[Simulation, 'Compressor size (W)'] = config['Heat Pump Heat Addition Rate (W)']
    Used_Inputs.loc[Simulation, 'Tank volume (L)'] = config['Volume Tank (L)']
    Used_Inputs.loc[Simulation, 'UA (W/K)'] = config['Jacket Loss Coefficient (W/K)']
    Used_Inputs.loc[Simulation, 'Two Week Sim'] = Two_Week_Sim
        
    # Call the function to analyze the case
    Test_Cases = Simulate_MonitoredData(Draw_Profile, config, set_temperature_profile, 
                                        Installation_Configuration, Output_Folder = Output_Folder, 
                                        Simulation_Name = Simulation_Name, 
                                        Case_Type = Case_Type, note = note, 
                                        Reduced_Output = Reduced_Output, 
                                        summary = Test_Cases, Simulation = Simulation)
    output_file = 'results_testing_' + File
    Test_Cases.to_csv(os.path.join(Folder, output_file))
    
    Used_Inputs_File = 'inputs_' + File
    Used_Inputs.to_csv(os.path.join(Folder, Used_Inputs_File))
     
    case_previous = case



# Use the following code for HPWH ducting evaluation

#cwd = os.getcwd()
#folder = r'C:\Users\Peter Grant\Dropbox (Beyond Efficiency)\Beyond Efficiency Team Folder\Frontier-HPWH Ducting Analysis\Modeling\FullYear'
#file = 'Test_Cases.csv'
#Test_Cases = pd.read_csv(os.path.join(folder, file), index_col = 0)
#
#case_previous = None
#for simulation in Test_Cases.index:
##if True:
##    simulation = Test_Cases.index[3]
#    case = Test_Cases.loc[simulation, 'Draw Profile Source']
#    if case == 398:
#        case = '3E98'
#        Test_Cases.loc[simulation, 'Draw Profile Source'] = '3E98'
#       
#    if ' * 25%' in case:
#        print('SF case found')
#        case = case[0:4]
#        SF_Case = True
#    else:
#        SF_Case = False
#    set_temperature_profile = Test_Cases.loc[simulation, 'Set Temperature Profile']
#    Installation_Configuration = Test_Cases.loc[simulation, 'Installation Configuration']
#    note = Test_Cases.loc[simulation, 'Note'].astype(str)
#
#    print('simulation number {}'.format(simulation))
#    print('Installation_Configuration is {}'.format(Installation_Configuration))
#    print('case is {}'.format(case))
#    print(case_previous)
#    print('SF_Case is {}'.format(SF_Case))
#    print('set temperature profile is {}'.format(set_temperature_profile))
#    print('note is {}'.format(note))
#    
#    if case != case_previous:
#        
#        Config = 'Rheem_PROPH80_Config.txt'
#        Path_Config = os.path.join(cwd, Config)
#        print('Path_Config is {}'.format(Path_Config))        
#        
#        with open(Path_Config) as f:
#            data = f.read()
#        config = json.loads(data)
#        print('read config')
#        
#        Path_DrawProfile = cwd + r'\Input\Creekside Data for {}.csv'.format(case)
#        print('Path_DrawProfile is {}'.format(Path_DrawProfile))
#        Draw_Profile = pd.read_csv(Path_DrawProfile, index_col = 0)
#        Draw_Profile.index = pd.to_datetime(Draw_Profile.index)
#        
#        # Limits to the first two weeks for testing
##        Draw_Profile = Draw_Profile[Draw_Profile.index.month == 10]
##        Draw_Profile = Draw_Profile[Draw_Profile.index.day < 15]
##        print(Draw_Profile.index)
#        
#        Draw_Profile['Timestamp'] = Draw_Profile.index
#        Draw_Profile.index = pd.to_datetime(Draw_Profile.index)
#        Draw_Profile['Time (s)'] = (Draw_Profile.index - Draw_Profile.index[0]).total_seconds()
#        Draw_Profile['Time (min)'] = Draw_Profile['Time (s)'] / 60.
#        Draw_Profile['Hour'] = pd.DatetimeIndex(Draw_Profile['Timestamp']).hour
#
##    if SF_Case == True:
##        config['Volume Tank (L)'] = 170.34
##        config['Jacket Loss Coefficient (W/K)'] = 2.8 * 0.83
##    else:
##        config['Volume Tank (L)'] = 280
##        config['Jacket Loss Coefficient (W/K)'] = 2.8
##    print(config)
##    
#    Test_Cases = Simulate_MonitoredData(Draw_Profile, config, set_temperature_profile, Installation_Configuration, 'DuctEval_{}'.format(simulation), SF_Case, note, Reduced_Output = False, summary = Test_Cases, simulation = simulation)
#
#    output_file = 'results_' + file
#    Test_Cases.to_csv(os.path.join(folder, output_file))    
#     
#    case_previous = case