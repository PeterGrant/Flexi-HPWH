# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 15:18:50 2022

@author: Peter Grant
"""

import numpy as np

def Prepare_Inputs(Input_Data, Config):
    
    Inputs = Input_Data.copy(deep = True)
    
    # Initialize model output columns
    Inputs['Jacket Losses (kWh)'] = 0
    Inputs['Energy Withdrawn (kWh)'] = 0
    Inputs['Heat Added Heat Pump (kWh)'] = 0
    Inputs['Heat Added Backup (kWh)'] = 0
    Inputs['Total Energy Change (kWh)'] = 0
    Inputs['Node Temperatures (deg C)'] = 0
    Inputs['PowerMultiplier'] = 0
    Inputs['Electricity Consumed Heat Pump (kWh)'] = 0
    Inputs['Electricity Consumed Resistance (kWh)'] = 0
    Inputs['Electricity Consumed Total (kWh)'] = 0
    Inputs['Total Jacket Losses (kWh)'] = 0
    Inputs['Total Energy Withdrawn (kWh)'] = 0
    Inputs['Total Heat Added Heat Pump (kWh)'] = 0
    Inputs['Total Heat Added Backup (kWh)'] = 0
    Inputs['Total Heat Added (kWh)'] = 0
    Inputs['Node Energy Change (kWh)'] = 0
    Inputs['Heat Pump Heat Addition (kW)'] = 0
    Inputs['Time Since Set Change (s)'] = 0
    Inputs['Heat Pump Deadband (deg C)'] = 0
    Inputs['Resistance Set Temperature (deg C)'] = 0
    Inputs['Resistance Set Temperature, HP Active (deg C)'] = 0
    Inputs['State of Charge (%)'] = 0
    
    Col_Index = dict(zip(Inputs.columns, list(range(0, len(Inputs.columns)))))
    Config['Column Index'] = Col_Index
    Inputs = Inputs.to_numpy()
    Inputs = Inputs.astype('object')
    
    return Inputs, Config, Col_Index