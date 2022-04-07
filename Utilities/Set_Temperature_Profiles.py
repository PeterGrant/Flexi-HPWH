# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 18:38:32 2021

# This script contains a single function used to implement different forms of 
# load shifting controls in heat pump water heaters (HPWHs). The profiles can
# be read by the simulation models to use as needed.

@author: Peter Grant
"""

def get_profile(profile):
    '''
    This function returns the information needed to perform simulations
    using a specified set temperature profile. The user must provide a
    strong profile name that matches an option specified here as an input.
    The function then returns a dictionary containing hourly set temperatures
    for that set temperature profile. That dictionary can be used to map
    the set temperatures onto the input data set creating the set temperature
    profile for the simulation. Each provided set temperature profile includes
    a descriptive name and a quick comment describing the returned profile.
    
    inputs: 
    profile: The name of a set temperature profile to use in the simulation.
             Must match the name of a profile provided here. String format.
    Outputs: 
    set_temperatures: The hourly set temperature profile for use in the
                      simulation. Dictionary with float values.
    '''
    
    if profile == 'Static_48.9': # Constant 120 deg F
        set_temperatures = {'0': 48.9, '1': 48.9, '2': 48.9, '3': 48.9, '4': 
            48.9, '5': 48.9, '6': 48.9, '7': 48.9, '8': 48.9, '9': 48.9, '10': 
            48.9, '11': 48.9, '12': 48.9, '13': 48.9, '14': 48.9, '15': 48.9, 
            '16': 48.9, '17': 48.9, '18': 48.9, '19': 48.9, '20': 48.9, '21': 
            48.9, '22': 48.9, '23': 48.9}
    elif profile == 'Static_51.6': # Constant 125 deg F
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 51.6, '9': 51.6, '10': 
            51.6, '11': 51.6, '12': 51.6, '13': 51.6, '14': 51.6, '15': 51.6, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}                    
    elif profile == 'Static_54.4': # Constant 130 deg F
        set_temperatures = {'0': 54.4, '1': 54.4, '2': 54.4, '3': 54.4, '4': 
            54.4, '5': 54.4, '6': 54.4, '7': 54.4, '8': 54.4, '9': 54.4, '10': 
            54.4, '11': 54.4, '12': 54.4, '13': 54.4, '14': 54.4, '15': 54.4, 
            '16': 54.4, '17': 54.4, '18': 54.4, '19': 54.4, '20': 54.4, '21': 
            54.4, '22': 54.4, '23': 54.4}        
    elif profile == 'Static_56.1': # Constant 133 deg F
        set_temperatures = {'0': 56.1, '1': 56.1, '2': 56.1, '3': 56.1, '4': 
            56.1, '5': 56.1, '6': 56.1, '7': 56.1, '8': 56.1, '9': 56.1, '10': 
            56.1, '11': 56.1, '12': 56.1, '13': 56.1, '14': 56.1, '15': 56.1, 
            '16': 56.1, '17': 56.1, '18': 56.1, '19': 56.1, '20': 56.1, '21': 
            56.1, '22': 56.1, '23': 56.1}               
    elif profile == 'Static_60': # Constant 140 deg F
        set_temperatures = {'0': 60, '1': 60, '2': 60, '3': 60, '4': 
            60, '5': 60, '6': 60, '7': 60, '8': 60, '9': 60, '10': 
            60, '11': 60, '12': 60, '13': 60, '14': 60, '15': 60, 
            '16': 60, '17': 60, '18': 60, '19': 60, '20': 60, '21': 
            60, '22': 60, '23': 60}
    elif profile == '8A-4P LoadShift, 48.9 & 60 deg C': # 120 deg F typical shifted to 140 F between 8A and 4P
        set_temperatures = {'0': 48.9, '1': 48.9, '2': 48.9, '3': 48.9, '4': 
            48.9, '5': 48.9, '6': 48.9, '7': 48.9, '8': 60, '9': 60, '10': 
            60, '11': 60, '12': 60, '13': 60, '14': 60, '15': 60, 
            '16': 48.9, '17': 48.9, '18': 48.9, '19': 48.9, '20': 48.9, '21': 
            48.9, '22': 48.9, '23': 48.9}
    elif profile == '8A-2P LoadShift, 48.9 & 60 deg C': # 120 deg F typical shifted to 140 deg F between 8A and 2P
        set_temperatures = {'0': 48.9, '1': 48.9, '2': 48.9, '3': 48.9, '4': 
            48.9, '5': 48.9, '6': 48.9, '7': 48.9, '8': 60, '9': 60, '10': 
            60, '11': 60, '12': 60, '13': 60, '14': 48.9, '15': 48.9, 
            '16': 48.9, '17': 48.9, '18': 48.9, '19': 48.9, '20': 48.9, '21': 
            48.9, '22': 48.9, '23': 48.9}
    elif profile == '8A-2P LoadShift, 51.6 & 60 deg C': # 125 deg F typical shifted to 140 deg F between 8A and 2P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 60, '9': 60, '10': 
            60, '11': 60, '12': 60, '13': 60, '14': 51.6, '15': 51.6, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}            
    elif profile == '8A-2P LoadShift, 48.9 & 56.1 deg C': #120 deg F typical shifted to 133 def F between 8A and 2P
        set_temperatures = {'0': 48.9, '1': 48.9, '2': 48.9, '3': 48.9, '4': 
            48.9, '5': 48.9, '6': 48.9, '7': 48.9, '8': 56.1, '9': 56.1, '10': 
            56.1, '11': 56.1, '12': 56.1, '13': 56.1, '14': 48.9, '15': 48.9, 
            '16': 48.9, '17': 48.9, '18': 48.9, '19': 48.9, '20': 48.9, '21': 
            48.9, '22': 48.9, '23': 48.9}   
    elif profile == '8A-2P LoadShift, 51.6 & 56.1 deg C': # 125 deg F typical shifted to 133 deg F between 8A and 2P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 56.1, '9': 56.1, '10': 
            56.1, '11': 56.1, '12': 56.1, '13': 56.1, '14': 51.6, '15': 51.6, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}            
    elif profile == '8A-4P LoadShift, 48.9 & 56.1 deg C': # 120 deg F typical shifted to 133 deg F between 8A and 4P
        set_temperatures = {'0': 48.9, '1': 48.9, '2': 48.9, '3': 48.9, '4': 
            48.9, '5': 48.9, '6': 48.9, '7': 48.9, '8': 56.1, '9': 56.1, '10': 
            56.1, '11': 56.1, '12': 56.1, '13': 56.1, '14': 56.1, '15': 56.1, 
            '16': 48.9, '17': 48.9, '18': 48.9, '19': 48.9, '20': 48.9, '21': 
            48.9, '22': 48.9, '23': 48.9}  
    elif profile == '8A-4P LoadShift, 51.6 & 60 deg C': # 125 deg F typical shifted to 140 deg F between 8A and 4P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 60, '9': 60, '10': 
            60, '11': 60, '12': 60, '13': 60, '14': 60, '15': 60, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}   
    elif profile == '1A-5A LoadShift, 51.6 & 60 deg C': # 125 deg F typical shifted to 140 deg F between 1) 1A and 5A, and 2) 8A and 4P
        set_temperatures = {'0': 51.6, '1': 60, '2': 60, '3': 60, '4': 
            60, '5': 51.6, '6': 51.6, '7': 51.6, '8': 51.6, '9': 51.6, '10': 
            51.6, '11': 51.6, '12': 51.6, '13': 51.6, '14': 51.6, '15': 51.6, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}              
    elif profile == '8A-4P LoadShift, 51.6 & 56.1 deg C': # 125 deg F typical shifted to 133 deg F between 8A and 4P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 56.1, '9': 56.1, '10': 
            56.1, '11': 56.1, '12': 56.1, '13': 56.1, '14': 56.1, '15': 56.1, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}  
    elif profile == '8A-4P LoadShift, 51.6 & 60 deg C, Stepped': # 125 deg F with stepped shift to 140 deg F between 8A and 4P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 52.8, '9': 53.9, '10': 
            55, '11': 56.1, '12': 57.2, '13': 58.3, '14': 59.4, '15': 60, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6} 
    elif profile == '8A-2P LoadShift, 51.6 & 60 deg C, Stepped': # 125 deg F with stepped shift to 140 deg F between 8A and 2P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 53, '9': 54.4, '10': 
            55.8, '11': 57.2, '12': 58.6, '13': 60, '14': 51.6, '15': 51.6, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}             
    elif profile == '8A-4P LoadShift, 51.6 & 56.1 deg C, Stepped': # 125 deg F with stepped shift to 133 deg F between 8A and 4P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 52.2, '9': 52.8, '10': 
            53.3, '11': 53.9, '12': 54.4, '13': 55, '14': 55.6, '15': 56.1, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}  
    elif profile == '8A-2P LoadShift, 51.6 & 56.1 deg C, Stepped': # 125 deg F with stepped shift to 133 deg F between 8A and 2P
        set_temperatures = {'0': 51.6, '1': 51.6, '2': 51.6, '3': 51.6, '4': 
            51.6, '5': 51.6, '6': 51.6, '7': 51.6, '8': 52.35, '9': 53.1, '10': 
            53.85, '11': 54.6, '12': 55.35, '13': 56.1, '14': 51.6, '15': 51.6, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}     
    elif profile == '1A-5A LoadShift, 51.6 & 56.1 deg C, Stepped': # 125 deg F with stepped shift to 133 deg F between 1A and 5A
        set_temperatures = {'0': 51.6, '1': 52.725, '2': 53.85, '3': 54.975, '4': 
            56.1, '5': 51.6, '6': 51.6, '7': 51.6, '8': 51.6, '9': 51.6, '10': 
            51.6, '11': 51.6, '12': 51.6, '13': 51.6, '14': 51.6, '15': 51.6, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}   
    elif profile == '1A-5A & 8A-4P Load Shift, 51.6 & 56.1 deg C, Stepped':# 125 deg F with stepped shift to 133 deg F between 1) 1A and 5A and 2) 8A and 4P
        set_temperatures = {'0': 51.6, '1': 52.725, '2': 53.85, '3': 54.975, '4': 
            56.1, '5': 51.6, '6': 51.6, '7': 51.6, '8': 52.2, '9': 52.8, '10': 
            53.3, '11': 53.9, '12': 54.4, '13': 55, '14': 55.6, '15': 56.1, 
            '16': 51.6, '17': 51.6, '18': 51.6, '19': 51.6, '20': 51.6, '21': 
            51.6, '22': 51.6, '23': 51.6}  
    else:
        print('ERROR: Unknown set temperature profile, {}'.format(profile))
        return None          
    return set_temperatures

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    plt.figure(figsize = (12, 5))
#    profiles = ['Static_48.9', 'Static_51.6', 'Static_54.4', 'Static_56.1',
#                'Static_60', '8A-4P LoadShift, 48.9 & 60 deg C', 
#                '8A-2P LoadShift, 48.9 & 60 deg C',
#                '8A-2P LoadShift, 51.6 & 60 deg C',
#                '8A-2P LoadShift, 48.9 & 56.1 deg C',
#                '8A-2P LoadShift, 51.6 & 56.1 deg C',
#                '8A-4P LoadShift, 48.9 & 56.1 deg C',
#                '8A-4P LoadShift, 51.6 & 60 deg C',
#                '1A-5A LoadShift, 51.6 & 60 deg C',
#                '8A-4P LoadShift, 51.6 & 56.1 deg C',
#                '8A-4P LoadShift, 51.6 & 60 deg C, Stepped',
#                '8A-4P LoadShift, 51.6 & 56.1 deg C, Stepped',
#                '8A-2P LoadShift, 51.6 & 60 deg C, Stepped',
#                '8A-2P LoadShift, 51.6 & 56.1 deg C, Stepped',
#                '1A-5A LoadShift, 51.6 & 56.1 deg C, Stepped',
#                '1A-5A & 8A-4P Load Shift, 51.6 & 56.1 deg C, Stepped',
#                'Erroneous Profile Name Test']
#
#    for profile in profiles:
#        print(profile)
#        output = get_profile(profile)
#        print(output)
#        if output == None:
#            continue
#        plt.plot(list(output.keys()), list(output.values()), label = profile)
#    
#    plt.legend()    
#    plt.xlabel ('Time of Day (hr)')
#    plt.ylabel('Set Temperature (deg C)')
    
    SMALL_SIZE = 12
    MEDIUM_SIZE = 16
    BIGGER_SIZE = 20

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title    
    
    colors = ['tab:green', 'tab:blue', 'tab:purple', 'tab:red', 'tab:orange', 
              'tab:grey']
    linestyles = ['dotted', 'dashed', 'solid',' dashdot', (0, (3, 5, 1, 5)), (0, (3, 5, 1, 5, 1, 5))]
    profiles = ['Static_51.6', 'Static_60', '8A-4P LoadShift, 51.6 & 60 deg C', 
                '8A-4P LoadShift, 51.6 & 60 deg C',
                '8A-4P LoadShift, 51.6 & 60 deg C, Stepped',
                '1A-5A & 8A-4P Load Shift, 51.6 & 56.1 deg C, Stepped']

    for profile in profiles:
        print(profile)
        output = get_profile(profile)
        print(output)
        if output == None:
            continue
        plt.plot(list(output.keys()), list(output.values()), label = profile,
                 color = colors[profiles.index(profile)], linewidth = 3,
                 linestyle = linestyles[profiles.index(profile)])
    
    plt.legend(ncol = 2, loc = 'lower center', bbox_to_anchor = [0.5, -0.4])    
    plt.xlabel ('Time of Day (hr)')
    plt.ylabel('Set Temperature (deg C)')
#    plt.title('Set Temperature Profiles', fontsize = BIGGER_SIZE)