# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 14:10:22 2022

@author: Peter Grant
"""


import os
import sys
import json
import pandas as pd
import datetime
from HPWH_Model import HPWH_MultipleNodes
from Utilities.Set_Temperature_Profiles import Profiles
from Utilities.Installation_Configuration import get_temperatures
from Utilities.Prepare_Inputs import Prepare_Inputs
import Utilities.Conversions as Conversions

cwd = os.getcwd()

Start_Time = datetime.datetime.now()


#%%-----------------------DEFINE INPUTS------------------------------------

Config = 'Rheem_PROPH80_Config.txt' # The name of the configuration file

# State the folder and file name for the hot water draw profile
# This example is designed to use timestep-based T24 draw profiles in SI
Input_Folder = os.path.join(cwd, 'Input')
Input_File = 'S_03_Hot_2_Yes_1897_FSCDB_2019_SI.csv'

# State the set temperature and installation configuration for the HPWH
# More information is available in the packages and documentation
Set_Temperature_Profile = '8A-4P LoadShift, 51.6 & 56.1 deg C, Stepped'
Installation_Configuration = 'Ducted_Exhaust'

# The initial temperature of the nodes in the HPWH
Initial_Temperature = 51.7

# The frequency with which the simulation should print updates
Update_Frequency = 5

#%%-----------------------READ INPUT DATA-----------------------------------

# Read the draw profile data, convert as needed
Input_Data = pd.read_csv(os.path.join(Input_Folder, Input_File), index_col = 0)
Input_Data.index = pd.to_datetime(Input_Data.index)
Input_Data['Timestamp'] = Input_Data.index
ix = Input_Data.index

Input_Data = Input_Data.rename(columns = {
    'Mains Temperature (deg C)': 'Inlet Water Temperature (deg C)'})

# Add the set temperature profile to the input data set
Set_Temperature = Profiles[Set_Temperature_Profile]
Input_Data['Set Temperature, Heat Pump (deg C)'] = Input_Data.index.hour.astype(str).map(Set_Temperature)
Input_Data['Set Temperature, Resistance (deg C)'] = Input_Data.index.hour.astype(str).map(Set_Temperature)

# Modify the ambient and evaporator air temperatures as needed
Input_Data = get_temperatures(Input_Data, Installation_Configuration)

# Read the configuration data
with open(Config) as f:
    data = f.read()
Config = json.loads(data)

# Add initial temperatures to the configuration data
# This example uses the user-defined user set temperature
# You can also use linear interpolation between upper and lower thermostat
# temperatures to approximate stratification
Config['Node Temperatures (deg C)'] = [Initial_Temperature] * Config['Number of Nodes']

# Convert the inputs to the needed format for simulation
Input_Data, Config, Column_Index = Prepare_Inputs(Input_Data, Config)

#%%---------------------INITIALIZE MODEL-----------------------------------

# Set parameters for the HPWH model using the configuration data
HPWH = HPWH_MultipleNodes(Config)

#%%--------------------PERFORM THE SIMULATION------------------------------

print('Starting simulation')
Time_Last_Update = datetime.datetime.now()
for row in range(0, len(Input_Data)):
    
    # Process the timestep, store the outputs in the data set
    Output = HPWH.calculate_timestep(Input_Data[row])
    Input_Data[row] = Output
    
    # Update the user on simulation progress as appropriate
    if (datetime.datetime.now() - Time_Last_Update).total_seconds() >= Update_Frequency:
        Time_Last_Update = datetime.datetime.now()
        Timestamp = Input_Data[row, Column_Index['Timestamp']]
        print('Completed timestamp {} at {}'.format(Timestamp, Time_Last_Update))
        
# Create a pd.DataFrame with the results        
Result = pd.DataFrame(Input_Data, index = ix, columns = Column_Index.keys())

# Print the total simulation time
Time_Elapsed = (datetime.datetime.now() - Start_Time).total_seconds() / Conversions.seconds_in_minute
print('Total simulation time is {} minutes'.format(Time_Elapsed))

