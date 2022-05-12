# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 09:51:40 2019

This module contains the actual model for a HPWH. It was pulled into this separate file to make it easier to maintain. This way it can
be referenced in both the simulation and validation scripts as needed.

Currently this module holds only Model_HPWH_MixedTank, representing a 1-node model with a fully mixed tank. The plan is to later add additional functions
for different assumptions as needed, creating a library of relevant simulation models.

This model has now been modified to include an occupant behavior learning algorithm. As currently implemented it tracks the electricity consumption
of the HPWH during the full day, peak period, and off peak period. It gradually builds an understanding of how the water heater consumes electricity
enabling the development of load shifting controls tailored to each specific site. To use this algorithm the input data must have timesteps
at midnight (Not close to midnight, AT midnight)

@author: Peter Grant
"""

import numpy as np
import pandas as pd

Minutes_In_Hour = 60 #Conversion between hours and minutes
Seconds_In_Minute = 60 #Conversion between minutes and seconds
Watts_In_kiloWatt = 1000 #Conversion between W and kW
SpecificHeat_Water = 4.190 #J/g-C
Density_Water = 1000 #g/L
kWh_In_Wh = 1/1000 #Conversion from Wh to kWh
kWh_In_J = 2.7777777777e-7 #kWh per J

def Model_HPWH_MixedTank(Model, Parameters, Regression_COP, Regression_COP_Derate_Tamb):
    Coefficient_JacketLoss = Parameters[0]
    Power_Backup = Parameters[1]
    HeatAddition_HeatPump = Parameters[2]
    Temperature_Tank_Set_Deadband = Parameters[3]
    ThermalMass_Tank = Parameters[4]
    CO2_Production_Rate_Electricity = Parameters[5] #Temporarily not used. Keep as placeholder for adding CO2 calculations
    COP_Adjust_Reference_Temperature = Parameters[6]
    Cutoff_Temperature = Parameters[7]
#    Temperature_MixingValve_Set = Parameters[8]

    data = Model.to_numpy() #convert the dataframe to a numpy array for EXTREME SPEED!!!! (numpy opperates in C)
    col_indx = dict(zip(Model.columns, list(range(0,len(Model.columns))))) #create a dictionary to provide column index references while using numpy in following loop

    for i  in range(1, len(data)): #Perform the modeling calculations for each row in the index
        #THESE TWO LINES OF CODE ARE ONLY APPROPRIATE WHEN SIMULATING MONITORED DATA IN THE CREEKSIDE PROJECT
        #The monitoring setup sometimes experiences data outages. We don't know the ambient temperature or hot water conusmption
        #during those outages. As a result, the model can't correctly predict what happens during those outages. To get the model
        #back on track we re-initialize the model to match the average of the tank thermostat measurements when data collection
        #returns
#        if data[i, col_indx['Timestep (min)']] > 5: #If the time since the last recording is > 5 minutes we assume there was a data collection outage
#            data[i, col_indx['Tank Temperature (deg C)']] = 0.5 * (data[i, col_indx['T_Tank_Upper_C']] + data[i, col_indx['T_Tank_Lower_C']]) #When data collection resumes we re-initialize the tank at current conditions by setting the water temperature equal to the average of the thermostat measurements
#        data[i, col_indx['Hot Water Draw Volume (L)']] = (data[i, col_indx['Water Draw Volume (L)']] * data[i, col_indx['Water_RemoteTemp_C']] - \
#            data[i, col_indx['Water Draw Volume (L)']] * Temperature_MixingValve_Set) / (data[i, col_indx['Water_RemoteTemp_C']] - \
#            data[i, col_indx['Tank Temperature (deg C)']])
        # 1 - Calculate the jacket losses from the water in the tank to the ambient air
        data[i, col_indx['Jacket Losses (J)']] = -Coefficient_JacketLoss * (data[i,col_indx['Tank Temperature (deg C)']] 
            - data[i,col_indx['Ambient Temperature (deg C)']]) * (data[i, col_indx['Timestep (min)']] * 
            Seconds_In_Minute)
        # 2- Calculate the energy added to the tank using the backup electric resistance element, if any:
        # If the ambient temperature is below the cutoff temperature, use the heat pump set temperature
        # instead of the resistance element temperature
        if data[i, col_indx['Evaporator Air Inlet Temperature (deg C)']] < Cutoff_Temperature:
            data[i, col_indx['Temperature Activation Backup (deg C)']] = \
            data[i, col_indx['Set Temperature (deg C)']] - Temperature_Tank_Set_Deadband
        if data[i-1, col_indx['Energy Added Backup (J)']] == 0:  #If the backup heating element was NOT active during the last time step, Calculate the energy added to the tank using the backup electric resistance elements
            data[i, col_indx['Energy Added Backup (J)']] = Power_Backup * \
                int(data[i, col_indx['Tank Temperature (deg C)']] < \
                data[i, col_indx['Temperature Activation Backup (deg C)']]) * \
                (data[i, col_indx['Timestep (min)']] * Seconds_In_Minute)
        else: #If it WAS active during the last time step, Calculate the energy added to the tank using the backup electric resistance elements
            data[i, col_indx['Energy Added Backup (J)']] = Power_Backup * int(data[i, 
                col_indx['Tank Temperature (deg C)']] < int(data[i, col_indx['Set Temperature (deg C)']])) * \
                (data[i, col_indx['Timestep (min)']] * Seconds_In_Minute)
        # 3- Calculate the energy withdrawn by the occupants using hot water:
        data[i, col_indx['Energy Withdrawn (J)']] = -data[i, col_indx['Hot Water Draw Volume (L)']] * \
            Density_Water * SpecificHeat_Water * (data[i, col_indx['Tank Temperature (deg C)']] - \
            data[i, col_indx['Inlet Water Temperature (deg C)']])
        # 4 - Calculate the energy added by the heat pump during the previous timestep
        if data[i, col_indx['Evaporator Air Inlet Temperature (deg C)']] < Cutoff_Temperature:
            data[i, col_indx['Energy Added Heat Pump (J)']] = 0
        else:
            data[i, col_indx['Energy Added Heat Pump (J)']] = (HeatAddition_HeatPump * \
                int(data[i, col_indx['Tank Temperature (deg C)']] < (data[i, \
                col_indx['Set Temperature (deg C)']] - Temperature_Tank_Set_Deadband) or data[i-1, \
                col_indx['Energy Added Heat Pump (J)']] > 0 and data[i, col_indx['Tank Temperature (deg C)']] \
                < data[i, col_indx['Set Temperature (deg C)']]) * (data[i, col_indx['Timestep (min)']] * \
                Seconds_In_Minute))
        # 5 - Calculate the energy change in the tank during the previous timestep
        data[i, col_indx['Total Energy Change (J)']] = data[i, col_indx['Jacket Losses (J)']] + \
            data[i, col_indx['Energy Withdrawn (J)']] + data[i, col_indx['Energy Added Backup (J)']] + \
            data[i, col_indx['Energy Added Heat Pump (J)']]        
#        data[i, col_indx['Electricity CO2 Multiplier (lb/kWh)']] = Parameters[10][data[i, col_indx['Hour of Year (hr)']]]
        # 6 - #Calculate the tank temperature during the final time step
        if i < len(data) - 1:
            data[i + 1, col_indx['Tank Temperature (deg C)']] = data[i, col_indx['Total Energy Change (J)']] / \
                ThermalMass_Tank + data[i, col_indx['Tank Temperature (deg C)']]
            
    Model = pd.DataFrame(data=data[0:,0:],index=Model.index,columns=Model.columns) #convert Numpy Array back to a Dataframe to make it more user friendly
    
    Model['COP Adjust Tamb'] = Regression_COP_Derate_Tamb(Model['Tank Temperature (deg C)']) * \
        (Model['Evaporator Air Inlet Temperature (deg C)'] - COP_Adjust_Reference_Temperature)
    Model['COP'] = Regression_COP(1.8 * Model['Tank Temperature (deg C)'] + 32) + Model['COP Adjust Tamb']
    Model['Electric Power (W)'] = np.where(Model['Timestep (min)'] > 0, (Model['Energy Added Heat Pump (J)']) / \
         (Model['Timestep (min)'] * Seconds_In_Minute), 0)/Model['COP'] + np.where(Model['Timestep (min)'] > 0, \
         Model['Energy Added Backup (J)']/(Model['Timestep (min)'] * Seconds_In_Minute), 0)
    Model['Electricity Consumed (kWh)'] = (Model['Electric Power (W)'] * Model['Timestep (min)']) / \
        (Watts_In_kiloWatt * Minutes_In_Hour)
        
    Model['Energy Added Total (J)'] = Model['Energy Added Heat Pump (J)'] + Model['Energy Added Backup (J)'] #Calculate the total energy added to the tank during this timestep
    Model['Jacket Losses (J)'] = Model['Jacket Losses (J)'] * kWh_In_J
    Model['Energy Added Backup (J)'] = Model['Energy Added Backup (J)'] * kWh_In_J
    Model['Energy Added Heat Pump (J)'] = Model['Energy Added Heat Pump (J)'] * kWh_In_J
    Model['Energy Added Total (J)'] = Model['Energy Added Total (J)'] * kWh_In_J
    Model['Energy Withdrawn (J)'] = Model['Energy Withdrawn (J)'] * kWh_In_J
    Model['Total Energy Change (J)'] = Model['Total Energy Change (J)'] * kWh_In_J
    Model = Model.rename(columns={'Energy Added Total (J)': 'Energy Added Total (kWh)',
                                  'Jacket Losses (J)': 'Jacket Losses (kWh)',
                                  'Energy Added Backup (J)': 'Energy Added Backup (kWh)',
                                  'Energy Added Heat Pump (J)': 'Energy Added Heat Pump (kWh)',
                                  'Energy Withdrawn (J)': 'Energy Withdrawn (kWh)',
                                  'Total Energy Change (J)': 'Total Energy Change (kWh)'})
    Model['Electricity Consumed Heat Pump (kWh)'] = Model['Energy Added Heat Pump (kWh)'] / Model['COP']    
    
    return Model

class HPWH_MultipleNodes():
    '''
    This tool represents a multi node model of electric HPWHs. It uses an 
    external configuration file to read the parameters describing the
    performance of the unit. As of Dec 5, 2021 the model contains control logic
    for Rheem PROPH80 HPWHs and the configuration files provides the 
    coresponding parameters. This model uses a few assumptions which have not
    yet been validated due to not having the correct data.
    
    1. The water flows through each node without mixing between nodes. Cold
    water entering the bottom of the tank enters the bottom node, then flows
    sequentially through the other nodes. This may or may not be true. Water
    flowing into the bottom of the tank likely mixes into several of the lower
    nodes, but this evaluated using the current available data sets. This 
    assumption should be checked using laboratory data when possible.
    2. All heat added by the heat pump is added to nodes to the coldest nodes.
    This attempts to emulate buoyancy effects, where heated water will rise to
    the level of other nodes at the same temperature. Similar behavior has
    been seen in other water heater simulation models, but the available data
    does not allow validating this assumption. It also raises a concern, 
    because the heat pump likely adds heat to nodes above the stratification
    layer, which cannot be tracked in the current model. This assumption
    should be checked using laboratory data when possible.
    3. The heat pump COP curves are second order regressions with the parameters
    pulled from the data set. While they fit the Creekside data well, it is 
    possible that this approach yielded some unrealistic performance curves.
    Verifying the COP curves using lab data when possible would be
    beneficial.
    4. The model assumes that the low temperature heat pump cutoff decision is 
    made using the evaporator air inlet temperature, which decreases when the
    unit is installed in a ducted configuration. This assumption appears to
    be correct, but verifying it using lab data would be wise.
    
    There are also some control logic aspects which are not well understood.
    
    1. The HPWH typically uses the resistance elements and heat pump
    simultaneously when 2nd stage triggers, unless the air temperature is below
    the cutoff temperature. When the air temperature is below the outlet it 
    uses exclusively the resistance elements. Sometimes it uses only the
    resistance elements even when the air temperature is above he cutoff. Rheem
    patent information implies this is a 'pre-heat' mode, but we have not been
    able to determine the cause at this time. Further lab testing to evaluate
    the control logic directly would help improve the representation of the
    control logic.
    2. Rheem patent information claims that the resistance elements have a 
    lockout period, preventing the resistance elements from activating if the 
    heat pump is active but has not been active for that long. At this time
    the lockout control has not been implemented, as we have not been able to
    1) verify its existence, and 2) identify the lockout time from the 
    monitoring data. Code related to this has been commented out until we can
    more accurately verify operation.
    '''
    
    def __init__(self, config):
        '''
        Initializes the model and sets performance parameters as needed for
        for simulation.
        
        inputs:
        config: A configuration file providing the parameters describing the 
                performance of the HPWH.
                Jacket Loss Coefficient (W/K): The rate at which the tank
                    loses heat based on the temperature difference between
                    the water temperature and air temperature. Expressed in
                    W/K. This heat loss is applied evenly to each node.
                Backup Element Power (W): The electricity consumption rate of 
                    the backup resistance elements. Expresed in W.
                Resistance Deadband (deg C): The deadband used by the 
                    resistance elements when the heat pump is not active. Will
                    activate 2nd stage heating when the upper thermostat temp
                    is below the set temp - this deadband. Expressed in deg C.
                Resistance Deadband, HP Active (deg C): The same as above, but
                    used when the heat pump is active.
                Heat Pump Heat Addition Rate (W): The rated heat addition of 
                    the heat pump when active. Expressed in W.
                Heat Rate Coefficients: The heat added by the heat pump varies
                    with ambient air and tank water temperatures. These 
                    coefficients define a 2nd order regression definin how the
                    heat rate is adjusted to match the current conditions.
                Heat Pump Activation Deadband (deg C): The deadband used for
                    the heat pump. The HPWH will activate the heat pump if the
                    water temperature is below the set temperature minus this
                    deadband.
                Heat Pump Activation Deadband, Recent Set Temperature Change 
                    (deg C): The deadband used by the heat pump if the set
                    temperatureh as recently changed. Monitoring data has shown
                    that the value for Rheem HPWHs is 0.
                Heat Pump Deadband Time Period (s): The period of time for
                    which the recent set temperature deadband applies.
                Volume Tank (L): The volume of the tank expressed in liters.
                    Typically this value is 90% of the rated value.
                Power Coefficients: The power consumed by the heat pump is a
                    function of the air and water temperatures. These 
                    coefficients define a 2nd order regression that modifies
                    the heat addition rate to find the current power 
                    consumption.
                Set Temperature (deg C): The set temperature of the HPWH.
                Varying Set Temperature: States whether the set temperature
                    in the simulation varies or not. Used for load shifting
                    simulations. 1 indicates that the set temperature changes,
                    0 indicates that it does not.
                Cutoff Temperature (deg C): The low temperature limit for
                    operation of the heat pump. If the ambient air temperature
                    is below this value the heat pump will not engage, and the
                    HPWH will use the resistance elements instead.
                Node Temperatures (deg C): The initial temperature of the 
                    water in each node of the HPWH.
                Upper Thermostat Node: The node in the tank in which the upper
                    thermostat is located.
                Lower Thermostat Node: The node in the tank in which the lower
                    thermostat is located.
                Number of Nodes: The number of nodes representing different 
                    sections of the water in the tank used i nthe simulation.
        '''
        
        self.Coefficient_JacketLoss = config['Jacket Loss Coefficient (W/K)'] / 1000
        self.Power_Backup = config['Backup Element Power (W)'] / 1000
        self.Upper_Resistance_Deadband = config['Resistance Deadband (deg C)']
        self.Upper_Resistance_Deadband_HPActive = config['Resistance Deadband, HP Active (deg C)']
        self.HeatAddition_HeatPump = config['Heat Pump Heat Addition Rate (W)'] / 1000
        self.HeatRate_HP_Coefficients = config['Heat Rate Coefficients']
        self.HeatPump_Activation_Deadband = config['Heat Pump Activation Deadband (deg C)']
        self.HeatPump_ActivationDeadband_RecentSetChange = config['Heat Pump Activation Deadband, Recent Set Temperature Change (deg C)']
        self.HeatPump_ActivationDeadband_LowStratification = config['Heat Pump Activation Deadband, Low Stratification (deg C)']
        self.HeatPump_SetChange_TimeWindow = config['Heat Pump Deadband Time Period (s)']
        self.ThermalMass_Tank = config['Volume Tank (L)'] * SpecificHeat_Water * Density_Water * kWh_In_J
        self.Power_Coefficients = config['Power Coefficients']
        self.Set_Temperature_HeatPump = config['Set Temperature, Heat Pump (deg C)']
        self.Set_Temperature_Resistance = config['Set Temperature, Resistance (deg C)']
        self.Varying_Set_Temperature = config['Varying Set Temperature']
        self.Cutoff_Temperature = config['Cutoff Temperature (deg C)']
        self.Node_Temperatures = config['Node Temperatures (deg C)']
        self.Upper_Thermostat_Node = config['Upper Thermostat Node']
        self.Lower_Thermostat_Node = config['Lower Thermostat Node']
        self.Number_Nodes = config['Number of Nodes']
        self.Time_Since_Set_Change = self.HeatPump_SetChange_TimeWindow + 1
        self.Control_Logic_Model = config['Control Logic Model']
#        self.Tank_Model = config['Tank Model'] # Commented out b/c this capability is not yet implemented
#        self.Resistance_Lockout_Time = config['Resistance Lockout Time (min)']
#        self.Time_Since_HeatPump_Activation = 0

        self.Resistance_Active = False
        self.HeatPump_Active = False
        self.col_indx = config['Column Index']
        
        self.ThermalMass_Node = self.ThermalMass_Tank / self.Number_Nodes
        self.JacketLoss_Node = self.Coefficient_JacketLoss / self.Number_Nodes
    
    def calculate_HP_power(self, T_Tank_Lower, T_Ambient):
        '''
        Calculates the power multiplier used to determine the power consumed by
        heat heat pump at the current air and water conditions.
        
        inputs:
            T_Tank_Lower: The temperature of the water at the lower thermostat.
                          Expressed in deg C.
            T_Ambient: The temperature of the air surrounding the HPWH.
                       Expressed in deg C.
                       
        outputs:
            Returns the multiplier to be applied to the heat pump rated heat
            addition.
        '''
        
        return self.Power_Coefficients[0] + self.Power_Coefficients[1] * T_Tank_Lower + self.Power_Coefficients[2] * T_Ambient + self.Power_Coefficients[3] * T_Tank_Lower ** 2 + self.Power_Coefficients[4] * T_Ambient ** 2
    
    def calculate_HP_HeatAddition(self, T_Tank_Lower, T_Ambient):
        '''
        Calculates the multiplier used to determine the heat added to the water
        by the heat heat pump at the current air and water conditions.
        
        inputs:
            T_Tank_Lower: The temperature of the water at the lower thermostat.
                          Expressed in deg C.
            T_Ambient: The temperature of the air surrounding the HPWH.
                       Expressed in deg C.
                       
        outputs:
            Returns the multiplier to be applied to the heat pump rated heat
            addition.
        '''        
        
        return self.HeatRate_HP_Coefficients[0] + self.HeatRate_HP_Coefficients[1] * T_Tank_Lower + self.HeatRate_HP_Coefficients[2] * T_Ambient + self.HeatRate_HP_Coefficients[3] * T_Tank_Lower ** 2 + self.HeatRate_HP_Coefficients[4] * T_Ambient ** 2

    def control_logic(self, control_logic_model, data):
        '''
        Determines heat pump and ER element control logic decisions depending on the current operating
        conditions and the selected control logic model.
        
        inputs:
            control_logic_model: The name of the model to be used. Typically this matches control
                                 logic of a specific manufacturer & model HPWH.
                            
        ouotputs:
            Updates attributes of the HPWH
            self.Time_Since_Set_Change: s. The time since the set temperature was last changed
            self.Set_Temperature: deg C. The set temperature of the HPWH during this timestep
            self.HeatPump_Deadband: deg C. The deadband of the HP used during this timestep.
            self.HeatPump_Active: Boolean. States whether the HP is currently heating or not.
            self.Resistance_Deadband: deg C. The deadband of the HP used during this timestep.
            self.Resistance_Active: Boolean. States whether or not the ER are currently heating.
        '''
        
        if control_logic_model == 'Rheem PROPH80':
            # Start Rheem control logic
            # When updating to add control logic from other manufacturers:
            # -Remove this code to an external library of contro logic functions
            # -Include a function to choose manufacturer control logic based on config file
            # -Have that function call another function for control logic of that manufacturer
            # -Update config files to state which manufacturer's control logic to use
            # -It's possible each manufacturer will have multiple sets of control logic
            # --Consider specifying a specific type of logic, not just a manufacturer
            # Determine the deadband for the heat pump based on current conditions
            # and simulation style
            if self.Varying_Set_Temperature == True:
                if abs(self.Set_Temperature_HeatPump - data[self.col_indx['Set Temperature, Heat Pump (deg C)']]) > 0:
                    self.Time_Since_Set_Change = 0
                else:
                    self.Time_Since_Set_Change += data[self.col_indx['Timestep (min)']] * Seconds_In_Minute
                self.Set_Temperature_HeatPump = data[self.col_indx['Set Temperature, Heat Pump (deg C)']]
                self.Set_Temperature_Resistance = data[self.col_indx['Set Temperature, Resistance (deg C)']]
            
            if self.Time_Since_Set_Change < self.HeatPump_SetChange_TimeWindow:
                self.HeatPump_Deadband = self.HeatPump_ActivationDeadband_RecentSetChange
            else:
                self.HeatPump_Deadband = self.HeatPump_Activation_Deadband

            # Heat pump control logic. Determines whether the heat pump is on
            # or off
            # If the surrounding air is too cold for the heat pump to operate
            if data[self.col_indx['Evaporator Air Inlet Temperature (deg C)']] < self.Cutoff_Temperature:
                self.HeatPump_Active = False
            
            elif self.HeatPump_Active == True:
                # If the upper thermostat node temperature is above the set
                # temperature Rheem HPs will not engage
                # Can I delete the first part talking about the lower thermostat?
                if (self.Node_Temperatures[self.Lower_Thermostat_Node] < self.Set_Temperature_HeatPump) & (self.Node_Temperatures[self.Upper_Thermostat_Node] < self.Set_Temperature_HeatPump + 1):
                    self.HeatPump_Active = True
                else:
                    self.HeatPump_Active = False
            elif self.HeatPump_Active == False:
                # If the lower thermostat water temperature is cold enough to
                # activate the heat pump
                if self.Node_Temperatures[self.Lower_Thermostat_Node] <= self.Set_Temperature_HeatPump - self.HeatPump_Deadband:
                    if self.Node_Temperatures[self.Upper_Thermostat_Node] > self.Set_Temperature_HeatPump:
                        self.HeatPump_Active = False
                    else:
                        self.HeatPump_Active = True
                # If the upper thermostat calls for heating, but the lower thermostat is warm
                elif self.Node_Temperatures[self.Upper_Thermostat_Node] <= self.Set_Temperature_HeatPump - self.HeatPump_ActivationDeadband_LowStratification:
                    if (self.Node_Temperatures[self.Upper_Thermostat_Node] - self.Node_Temperatures[self.Lower_Thermostat_Node]) < 5:
                        self.HeatPump_Active = True
                    else:
                        self.HeatPump_Active = False
                else:
                    self.HeatPump_Active = False
            else:
                self.HeatPump_Active = False
        
            # Set resistance element deadband based on HP status
            if self.HeatPump_Active == True:
                self.Resistance_Deadband = self.Upper_Resistance_Deadband_HPActive
#                self.Time_Since_HeatPump_Activation += data[self.col_indx['Timestep (min)']]
            else:
                self.Resistance_Deadband = self.Upper_Resistance_Deadband
#                self.Time_Since_HeatPump_Activation = 0

             
            # Resistance element control logic
            # If it is too cold for the heat pump to operate
            if data[self.col_indx['Evaporator Air Inlet Temperature (deg C)']] < self.Cutoff_Temperature:
                if self.Resistance_Active == True:
                    # If the water in the tank is still cold
                    # The resistance elements tend to cut off 2.3 deg C below the
                    # set temperature
                    if self.Node_Temperatures[self.Lower_Thermostat_Node] < self.Set_Temperature_HeatPump - 0.5: # -0.5 to avoid accidentally surpassing set temperature
                        self.Resistance_Active = True
                    elif self.Node_Temperatures[self.Upper_Thermostat_Node] < self.Set_Temperature_HeatPump - 0.5:
                        self.Resistance_Active = True
                    else:
                        self.Resistance_Active = False
            
                # If the lower thermostat temperature is cold enough to use the HP
                elif self.Node_Temperatures[self.Lower_Thermostat_Node] <= self.Set_Temperature_HeatPump - self.HeatPump_Deadband:
                    self.Resistance_Active = True

                # If the upper thermostat temperature is cold enough to use 2nd stage
                elif self.Node_Temperatures[self.Upper_Thermostat_Node] <= self.Set_Temperature_Resistance - self.Resistance_Deadband:
                    self.Resistance_Active = True
                else:
                    self.Resistance_Active = False
                
            # If the upper thermostat temperature is cold enough to use 2nd stage
            elif self.Node_Temperatures[self.Upper_Thermostat_Node] < self.Set_Temperature_Resistance - self.Resistance_Deadband:
                self.Resistance_Active = True

            # If 2nd stage is currently active
            elif self.Resistance_Active == True:
                # If 2nd stage has not yet finished heating the water
                if self.Node_Temperatures[self.Upper_Thermostat_Node] < self.Set_Temperature_Resistance - 1:
                    self.Resistance_Active = True

                # If 2nd stage has not yet finished heating the water
                elif self.Node_Temperatures[self.Lower_Thermostat_Node] < self.Set_Temperature_Resistance - 1:
                    # If the upper thermostat temperature is not above the set temperature
                    if self.Node_Temperatures[self.Upper_Thermostat_Node] < self.Set_Temperature_Resistance + 1:
                        self.Resistance_Active = True
                    else:
                        self.Resistance_Active = False
                else:
                    self.Resistance_Active = False
            else:
                self.Resistance_Active = False
            
            # Logic implementing the 2nd stage lockout when the heat pump has
            # been active for less time than specified
#            if self.Time_Since_HeatPump_Activation < self.Resistance_Lockout_Time:
#                if self.Node_Temperatures[self.Upper_Thermostat_Node] > 40.5:
#                    self.Resistance_Active = False
        
            # Implement second stage control logic. If the resistance elements are
            # active the heat pump is active unless it's too cold out
            if self.Resistance_Active == True:
                if data[self.col_indx['Evaporator Air Inlet Temperature (deg C)']] > self.Cutoff_Temperature:
                    self.HeatPump_Active == True
                
            # End Rheem control logic
    
    def calculate_timestep(self, data):
        '''
        Performs the calculations for one time step in the simulation. Must be 
        called by an external script each time step. data provides the operating
        conditions for the current time step which the model uses to determine
        the operation of the HPWH. Data must meet the following requirements:
            
            1. Be a numpy array containing the data for the current timestep.
            2. Be in the order specified by col_index. The best way to do this
               is to create the input data frame, then create and set col_index
               after.
            3. Contain the following data points:
                   Set Temperature (deg C): The set temperature, if varying set
                       temperature == True.
                   Timestep (min): The duration of the current timestep.
                   Evaporator Air Inlet Temperature (deg C): The temperature of
                       the air entering the evaporator when the heat pump is
                       active.
                   Ambient Temperature (deg C): The temperature of the air
                       surrounding the HPWH.
                   Inlet Water Temperature (deg C): The temperature of the 
                       water entering the HPWH when how water is consumed.
                   Hot Water Draw Volume (L): The volume of hot water withdrawn
                       from the tank during the current timestep.
        
        This function uses the following steps:
            1. Initialize lists storing data for the active timestep.
            2. Perform control logic checks to determine if heat pump or 
               resistance elements are active.
            3. Calculate the heat added to each node by the heat pump or 
               resistance elements if active.
            4. Iterate through the nodes to determine the energy transfers
               and new temperatures.
            5. Store the output data in the previously created lists, and
               store them in the appropriate columns of data.
               
        This function then returns a modified version of data which contains
        the outputs. This output is expected to overwrite the current row in
        data, storing the outputs in the full simulation input/output data set.
        
        '''
        
        # Initialize lists for storing output data
        JacketLosses = []
        EnergyWithdrawn = []
        EnergyAdded_HP = []
        EnergyAdded_ER = []
        EnergyChange_Total = []
        Node_Temperatures = []
        
        # Set the type of data to ensure that outputs can be stored
        data = data.astype('object')
                
        # Identify the heat addition rate of the heat pump if active under
        # current conditions
        Heat_Addition_HP = self.HeatAddition_HeatPump * self.calculate_HP_HeatAddition(self.Node_Temperatures[self.Lower_Thermostat_Node], data[self.col_indx['Evaporator Air Inlet Temperature (deg C)']])
        data[self.col_indx['Heat Pump Heat Addition (kW)']] = Heat_Addition_HP
        
        self.control_logic(self.Control_Logic_Model, data)

        # Start heating logic
        # Assumptions to emulate observed Rheem operation:
        # -Separate ER elements at upper and lower thermostat locations
        # -5100% to top when upper thermostat below temperature
        # -100% to bottom when upper thermostat at temperature
        # -Lower element heats all nodes below a stratification layer
        # -Heat pump heats all nodes below a stratification layer
        # --Simplification. Really the heat pump will heat some above the
        #       stratification layer if the layer is low in the tank
        # Set resistance element heat rates based on status
        Heating_Resistance = []
        
        if self.Resistance_Active == True:
            if data[self.col_indx['Evaporator Air Inlet Temperature (deg C)']] < self.Cutoff_Temperature:
                Temperature_Resistance_Target = max(self.Set_Temperature_HeatPump, self.Set_Temperature_Resistance)
            else:
                Temperature_Resistance_Target = self.Set_Temperature_Resistance
                
            # If the upper thermostat temperature is cold the heat goes to the
            # upper resistance element
            if self.Node_Temperatures[self.Upper_Thermostat_Node] < Temperature_Resistance_Target - 0.5:
                Number_Heated = 1

#                # Identify the nodes heated by the resistance elements assuming
#                # that all nodes below the stratification layer are heated
#                for node in range(1, self.Number_Nodes):
#                    if self.Node_Temperatures[node] > self.Node_Temperatures[node-1]:
#                        break
#                    else:
#                        Number_Heated += 1

                # Track the heat added to the water by the lower resistance
                # element
#                Heating_Resistance[0:Number_Heated-1] = [(self.Power_Backup/2) / (Number_Heated - 1)] * (Number_Heated - 1)
                # Add no heat to nodes between the stratification layer and the 
                # upper top resistance element
#                Heating_Resistance[Number_Heated-1:] = [0] * (self.Number_Nodes - (Number_Heated - 1))                
                # Add heat where the upper resistance element is located
                Heating_Resistance[0:] = [0] * self.Number_Nodes
                Heating_Resistance[self.Upper_Thermostat_Node] = self.Power_Backup

            # If the top is not cold but the bottom is
            elif self.Node_Temperatures[self.Lower_Thermostat_Node] < Temperature_Resistance_Target:
                # Add heat to all nodes below the stratification layer. Use
                # the full heating power
                Number_Heated = 1
                for node in range(1, self.Number_Nodes-1):
                    if self.Node_Temperatures[node] > self.Node_Temperatures[node-1]:
                        break
                    else:
                        Number_Heated += 1

                Heating_Resistance[0:Number_Heated] = [self.Power_Backup / Number_Heated] * Number_Heated
                Heating_Resistance[Number_Heated:] = [0] * (self.Number_Nodes - Number_Heated)
            else: # Debugging code. Not likely to be called
                print('ERROR: UNEXPECTED ER OPERATION CONDITION')
                print(self.Resistance_Active)
                print(self.Node_Temperatures[self.Upper_Thermostat_Node])
                print(self.Node_Temperatures[self.Lower_Thermostat_Node])
                print(self.Set_Temperature_Resistance)
                print(self.Set_Temperature_HeatPump)
                print(Temperature_Resistance_Target)
                print(data[self.col_indx['Evaporator Air Inlet Temperature (deg C)']])
                print(self.Resistance_Deadband)
        else:
            Heating_Resistance = [0] * self.Number_Nodes
                
        # Set HP heating rates for each node
        Heating_HeatPump = []
        if self.HeatPump_Active == True:
            Number_Heated = 1
            # Identify the number of nodes below the stratification layer
            for node in range(1, self.Number_Nodes):
                if self.Node_Temperatures[node] > self.Node_Temperatures[node-1]:
                    break
                else:
                    Number_Heated += 1
            
            # Add heat to nodes below the stratification layer
            Heating_HeatPump[0:Number_Heated] = [Heat_Addition_HP / Number_Heated] * Number_Heated
            Heating_HeatPump[Number_Heated:] = [0] * (self.Number_Nodes - Number_Heated)
        else:
            Heating_HeatPump = [0] * len(self.Node_Temperatures)
            
        # End heating control logic
            
        # Iterate through all nodes in the tank
        # This section calculates the heat transfer and new temperature of each
        # node in the tank
        for i in range(self.Number_Nodes):
            # Assume plug flow. Water from one node enters the higher node
            # BEFORE cooling off in response to water flows
            # Reverse operation of calculations to assume well mixed flow
            # Prior work indicated that (in pipes) it's between the two, and a
            # mixing coefficient could increase accuracy
            # These calculations assume 0 mixing in the bottom of the tank
            # caused by water flows. Likely not correct
            Node = self.Number_Nodes - (i + 1)
#            Node = i
            # Calculate jacket losses for the node
            # Could do jacket losses as an array to speed up
            dT = self.Node_Temperatures[Node] - data[self.col_indx['Ambient Temperature (deg C)']]
            dt = data[self.col_indx['Timestep (min)']] / Minutes_In_Hour
            Losses = -self.JacketLoss_Node * dT * dt
            JacketLosses.append(Losses)
            
            # Calculate energy transfer caused by water flows and heat addition
            # Could do heat rate as an array to speed up
            if Node == 0:
                T_Water_In = data[self.col_indx['Inlet Water Temperature (deg C)']]
            else:
                T_Water_In = self.Node_Temperatures[Node-1]
                
            # Could do most of these calculations as an array to speed up
            #Energy_Addition = Heating * data[self.col_indx, etc]
            Energy_Addition_HP = max(0, Heating_HeatPump[Node] * data[self.col_indx['Timestep (min)']] / Minutes_In_Hour)
            Energy_Addition_ER = max(0, Heating_Resistance[Node] * data[self.col_indx['Timestep (min)']] / Minutes_In_Hour)
            EnergyAdded_HP.append(Energy_Addition_HP)
            EnergyAdded_ER.append(Energy_Addition_ER)
                
            # Calcualte the energy withdrawn via hot water consumption
            dT = T_Water_In - self.Node_Temperatures[Node]
            ThermalMassRemoved = data[self.col_indx['Hot Water Draw Volume (L)']] * Density_Water * SpecificHeat_Water
            Withdrawn = ThermalMassRemoved * dT * kWh_In_J
            EnergyWithdrawn.append(Withdrawn)
            
            # Calculate the energy change in each node of the tank
            # Could pull this out of the for loop, do as an array to speed up
            EnergyChange = Losses + Energy_Addition_HP + Energy_Addition_ER + Withdrawn
            EnergyChange_Total.append(EnergyChange)
            
            # Calculate the new node temperature
            # Could pull this out of the for loop, do as an array to speed up
            Node_Temperature = EnergyChange / self.ThermalMass_Node + self.Node_Temperatures[Node]
            Node_Temperatures.append(Node_Temperature)
            self.Node_Temperatures[Node] = Node_Temperature
            
        # This could be removed from do_step() and added to a post_process() function    
        # Calculate the power HP power multiplier
        data[self.col_indx['PowerMultiplier']] = max(0, self.calculate_HP_power(self.Node_Temperatures[self.Lower_Thermostat_Node], data[self.col_indx['Evaporator Air Inlet Temperature (deg C)']]))
        
        #Calculate the outputs
        # Need to reverse when assuming plug flow b/c perform calcualtions in
        # opposite order
        JacketLosses.reverse()
        EnergyWithdrawn.reverse()
        EnergyAdded_HP.reverse()
        EnergyAdded_ER.reverse()
        EnergyChange_Total.reverse()
        Node_Temperatures.reverse()
        
        JacketLosses_Total = sum(JacketLosses)
        EnergyWithdrawn_Total = sum(EnergyWithdrawn)
        EnergyAddedHP_Total = sum(EnergyAdded_HP)
        EnergyAddedER_Total = sum(EnergyAdded_ER)
        EnergyChange_Tank = sum(EnergyChange_Total)

        # Add the outputs to data prior to returning
        # This could be removed from do_step() and added to a post_process() function
        data[self.col_indx['Electricity Consumed Heat Pump (kWh)']] = data[self.col_indx['PowerMultiplier']] * self.HeatAddition_HeatPump * data[self.col_indx['Timestep (min)']] / Minutes_In_Hour * self.HeatPump_Active
        data[self.col_indx['Electricity Consumed Resistance (kWh)']] = EnergyAddedER_Total / 0.99
        data[self.col_indx['Electricity Consumed Total (kWh)']] = data[self.col_indx['Electricity Consumed Heat Pump (kWh)']] + data[self.col_indx['Electricity Consumed Resistance (kWh)']]
        
        data[self.col_indx['Jacket Losses (kWh)']] = JacketLosses
        data[self.col_indx['Total Jacket Losses (kWh)']] = JacketLosses_Total
        data[self.col_indx['Energy Withdrawn (kWh)']] = EnergyWithdrawn
        data[self.col_indx['Total Energy Withdrawn (kWh)']] = EnergyWithdrawn_Total
        data[self.col_indx['Heat Added Heat Pump (kWh)']] = EnergyAdded_HP
        data[self.col_indx['Total Heat Added Heat Pump (kWh)']] = EnergyAddedHP_Total
        data[self.col_indx['Heat Added Backup (kWh)']] = EnergyAdded_ER
        data[self.col_indx['Total Heat Added Backup (kWh)']] = EnergyAddedER_Total
        data[self.col_indx['Total Heat Added (kWh)']] = EnergyAddedHP_Total + EnergyAddedER_Total
        data[self.col_indx['Node Energy Change (kWh)']] = EnergyChange_Total
        data[self.col_indx['Total Energy Change (kWh)']] = EnergyChange_Tank
        data[self.col_indx['Node Temperatures (deg C)']] = Node_Temperatures

        return data
            
            