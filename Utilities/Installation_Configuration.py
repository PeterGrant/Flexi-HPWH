# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 20:36:26 2021

This script contains equations used to adjust the ambient air temperature
used when calculating the COP of the HPWH. It performs different calculations
based on the type of ducting used.

Consider changing the code in this script to use DataFrame.to_dict to convert
the data to a dictionary, .map to create a new column, and algebra to calculate
ambient temperature. That would likely dramatically improve processing times.
Also consider changing it to be a function so it's easier to maintain

@author: Peter Grant
"""

import pandas as pd
import os

cwd = os.getcwd()

# Read data for difference between OAT and surrounding air temperature when
# the HPWH is installed in a small closet
Closet = pd.read_csv(os.path.join(cwd, 'Data', 'TCloset-TOutdoor_C.csv'))
# Read data for difference between OAT and surrounding air temperature when
# the HPWH is installed in a standard attic
Standard_Attic = pd.read_csv(os.path.join(cwd, 'Data', 'TAttic-TOutdoor_Standard_C.csv'), 
                             index_col = 0)
# Read data for difference between OAT and surrounding air temperature when
# the HPWH is installed ina high performance attic
HP_Attic = pd.read_csv(os.path.join(cwd, 'Data', 'TAttic-TOutdoor_HPAttic_C.csv'), 
                            index_col = 0)

def get_temperatures(Model, Installation):
    '''
    This function returns predicted ambient air and evaporator air temperatures
    given a dataset describing typical conditions and a specified installation
    configuration.
    
    inputs:
    Model: A dataframe containing the data describing the operating conditions.
           Must include a set of the following columns depending on the
           selected installation configuration:
               'Ambient Temperature (deg C)'
               'Outdoor Temperature (deg C)'
               'Month'
               'Hour'
    Installation: The description of the installation configuration. Must match
                  one of the options defined in this function. String format.
           
    outputs:
    Model: The input dataframe with new columns added describing the data
           analysis process and updated HPWH operating conditions.
    '''
    
    if Installation == 'Open_Area':
        # Representing a scenario when the HPWH is installed in an area
        # with adequate air flow, does not impact the ambient temperature, and
        # the assumed ambient temperature matches the surroundings
        Model['Ambient Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
        Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
    elif Installation == 'Outdoor':
        Model['Ambient Temperature (deg C)'] = Model['Outdoor Temperature (deg C)']
        Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
    elif Installation == 'Closet_AdequateAirflow':
        # Represents the case where a HPWH is installed in an external closet
        # with adequate airflow across the heat pump. Ambient temperature is 
        # modified based on the difference between outdoor and closet temperatures
        # Evaporator air inlet temperature matches the closet air temperature
        for month in Closet.columns:
            for hour in Closet.index:
                dT = Closet.loc[hour, month]

                Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour), 
                          'dT'] = dT     
                Model['Ambient Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT']
        Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
    elif Installation == 'Unducted_Closet':
        # Represents a scenario where the HPWH is in a closet with restricted air
        # flow. The closet will have different ambient temperatures than the
        # outdoor air, both impacted by the HPWH and by insulation & thermal mass
        # Change this code to reference correlation when Marc sends it
        # The reduction in ambient air temperature is based on Frontier Energy measurements
        # showing that the ambient air is 11 deg F cooler when unducted than when exhaust is ducted
        for month in Closet.columns:
            for hour in Closet.index:
                dT = Closet.loc[hour, month] - 6.111
                Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour), 
                          'Ambient Temperature (deg C)'] = Model.loc[(Model['Month'] == int(month)) & 
                          (Model['Hour'] == hour), 'Outdoor Temperature (deg C)'] + dT
        Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
    elif Installation == 'Ducted_Exhaust':
        # Represents a case where a HPWH is installed in a closet with exhaust
        # air ducted outside of the building. The closet temperature is 
        # different from the OAT. The HPWH receives reduced airflow due to
        # constraints in the closet
        # 4.16666 deg C = 7.5 deg F, per email with Marc H on Jul 28, 2021
        # Add calculations to adjust ambient temperature when Marc sends it
        for month in Closet.columns:
            for hour in Closet.index:
                dT = Closet.loc[hour, month]
                Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour), 
                          'dT'] = dT
        Model['Ambient Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT']
        Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)'] - 4.166666
    elif Installation == 'Ducted_Both':
        # Represents a case where a HPWH is installed in a closet with both
        # inlet and exhaust air outside of the building. The close temperature
        # is different from the OAT. The HPWH receives reduced air flow due to
        # constraints in the closet
        # This is a placeholder, and will likely be replaced with real functionality
        # when future data is available
        Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
        Model['Ambient Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
    elif Installation == 'StandardAttic':
        # Represents a case where a HPWH is installed in a standard attic.
        
        for season in Standard_Attic.columns:
            if season == 'Winter':
                months = [1, 2, 12]
            elif season == 'Summer':
                months = [5, 6, 7, 8, 9, 10]
            elif season == 'Spring/Fall':
                months = [3, 4, 11]
            else:
                print('ERROR: Unexpected season encountered.')

            for month in months:
                for hour in Standard_Attic.index:
                    dT = Standard_Attic.loc[hour, season]
                    Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour),
                              'dT'] = dT
            Model['Ambient Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT']
            Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)']

    elif Installation == 'Ducted_StandardAtticInlet':
        # Represents a case where a HPWH is installed in a closet with supply air ducted
        # in from the attic, and exhaust air ducted outside.
        
        for season in Standard_Attic.columns:
            if season == 'Winter':
                months = [1, 2, 12]
            elif season == 'Summer':
                months = [5, 6, 7, 8, 9, 10]
            elif season == 'Spring/Fall':
                months = [3, 4, 11]
            else:
                print('ERROR: Unexpected season encountered.')

            for month in months:
                for hour in Closet.index:
                    dT = Standard_Attic.loc[hour, season]
                    Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour),
                              'dT_Ambient'] = dT
            Model['Ambient Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT_Ambient']
            
            for month in months:
                for hour in Standard_Attic.index:
                    dT = Standard_Attic.loc[hour, season]
                    Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour),
                              'dT_Supply'] = dT
            Model['HPWH Supply Air Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT_Supply']
            Model['Evaporator Air Inlet Temperature (deg C)'] = Model['HPWH Supply Air Temperature (deg C)'] - 4.166666
            
    elif Installation == 'HPAttic':
        # Represents a case where a HPWH is installed in a high performance attic.
        
        for season in HP_Attic.columns:
            if season == 'Winter':
                months = [1, 2, 12]
            elif season == 'Summer':
                months = [5, 6, 7, 8, 9, 10]
            elif season == 'Spring/Fall':
                months = [3, 4, 11]
            else:
                print('ERROR: Unexpected season encountered.')

            for month in months:
                for hour in HP_Attic.index:
                    dT = HP_Attic.loc[hour, season]
                    Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour),
                              'dT'] = dT
            Model['Ambient Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT']
            Model['Evaporator Air Inlet Temperature (deg C)'] = Model['Ambient Temperature (deg C)']
            
    elif Installation == 'Ducted_HPAtticInlet':
        # Represents a case where a HPWH is installed in a closet with supply air ducted in
        # from a high performance attic and exhaust air ducted outside.
        
        for season in HP_Attic.columns:
            if season == 'Winter':
                months = [1, 2, 12]
            elif season == 'Summer':
                months = [5, 6, 7, 8, 9, 10]
            elif season == 'Spring/Fall':
                months = [3, 4, 11]
            else:
                print('ERROR: Unexpected season encountered.')

            for month in months:
                for hour in HP_Attic.index:
                    dT = HP_Attic.loc[hour, season]
                    Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour),
                              'dT'] = dT
            for month in months:
                for hour in Closet.index:
                    dT = Standard_Attic.loc[hour, season]
                    Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour),
                              'dT_Ambient'] = dT
            Model['Ambient Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT_Ambient']
            
            for month in months:
                for hour in HP_Attic.index:
                    dT = Standard_Attic.loc[hour, season]
                    Model.loc[(Model['Month'] == int(month)) & (Model['Hour'] == hour),
                              'dT_Supply'] = dT
            Model['HPWH Supply Air Temperature (deg C)'] = Model['Outdoor Temperature (deg C)'] + Model['dT_Supply']
            Model['Evaporator Air Inlet Temperature (deg C)'] = Model['HPWH Supply Air Temperature (deg C)'] - 4.166666        
    else:
        print('ERROR: Unexpected installation configuration')
        return None
        
        
    return Model