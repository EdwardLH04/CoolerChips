# from typing import ItemsView
# importing the required module
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import definitions

#import CSV file of E+ Data
#This code is setup to read the E+ data through a google drive.
#When importing this file into your own google drive ensure that
#your file is linked properly by creating the correct path.
#If the E+ data has additional columns or changes the order in the csv file then column numbers will need to be changed.
data=pd.read_csv(os.path.join(definitions.RESOURCES_DIR, '2ZoneDataCenterCRAHandplant_fixCPU_varyLoadprofile_sample.csv'), 
                 low_memory=False)

data_array = data.to_numpy()

SimulationDuration = 20 #in years/how long simulation runs for

#IT Total Heat Release
ITTotalHeatReleaseArray = data.iloc[:, 6]
ITTotalHeatRelease = 0
ITHeatlength = len(ITTotalHeatReleaseArray)
x = 0
while x<ITHeatlength:
  ITTotalHeatRelease = ITTotalHeatRelease + ITTotalHeatReleaseArray[x]
  x = x + 1

AverageITTotalHeatRelease = ITTotalHeatRelease/ITHeatlength

#Total Cooling System Energy
TotalCoolingSystemEnergyArray = data.iloc[:, 124]
TotalCoolingSystemEnergy = 0
CoolingSystemlength = len(TotalCoolingSystemEnergyArray)
x = 0
while x<CoolingSystemlength:
  TotalCoolingSystemEnergy = TotalCoolingSystemEnergy + TotalCoolingSystemEnergyArray[x]
  x = x+1

#Default Inputs
ElectricityCost = 0.145
CoolingMaintenanceCost = 50000
EnergyInflation = .0224
Inflation = .15
DiscountRate = .06
ITMaintenanceCost = 250000.0
RecoveredHeatValue = .1

#Inputs for Baseline
B_CapitolCost = 1.5 #million dollars
B_Life = 9
B_MTBF = 2000
B_EnergyUsage = 250 #million kWh
B_AvoidedITFailures = 0
B_AnnualRecoveredHeat = 1200 #million kWh Needs to calculated from E+ data

#Inputs for New
N_CapitolCost = 1.7 #million dollars
N_Life = 12
N_MTBF = 2000
N_EnergyUsage = 262.8 #million kWh
N_AvoidedITFailures = .5
N_AnnualRecoveredHeat = 1314 #million kWh Needs to calculated from E+ data

#Individual Expenses and Revenue Calculations for baseline
B_Time = []
B_Capitol = []
B_EnergyCost = []
B_CoolingMaintenance = []
B_ITMaintenance = []
B_HeatRevenue = []
B_Net = []
B_NPV = []
B_CumNPV = []

i = 0;
while i <= SimulationDuration:
  B_Time.append(i)

  #Capitol Costs
  if i%B_Life == 0:
    B_Capitol.append(B_CapitolCost*(1+Inflation)**i)
  else:
    B_Capitol.append(0)

  #Energy Costs
  if i > 0:
    B_EnergyCost.append(ElectricityCost*B_EnergyUsage*(1+EnergyInflation)**(i-1))
  else:
    B_EnergyCost.append(0)

  #Cooling Maintenance
  if i>0:
    B_CoolingMaintenance.append(((B_MTBF/8760)*CoolingMaintenanceCost*(1+Inflation)**i)/1000000)
  else:
    B_CoolingMaintenance.append(0)

  #IT Maintenance
  if i>0:
    B_ITMaintenance.append((-B_AvoidedITFailures*ITMaintenanceCost*(1+Inflation)**i)/1000000)
  else:
    B_ITMaintenance.append(0)

  #Heat Revenue
  if i>0:
    B_HeatRevenue.append(-B_AnnualRecoveredHeat*RecoveredHeatValue*ElectricityCost*(1+EnergyInflation)**(i-1))
  else:
    B_HeatRevenue.append(0)

  #Net
  B_Net.append(B_Capitol[i]+B_EnergyCost[i]+B_CoolingMaintenance[i]+B_ITMaintenance[i]+B_HeatRevenue[i])

  #NPV
  B_NPV.append(B_Capitol[i]/(1+DiscountRate)**i+B_EnergyCost[i]/(1+DiscountRate)**i+B_CoolingMaintenance[i]/(1+DiscountRate)**i+B_ITMaintenance[i]/(1+DiscountRate)**i+B_HeatRevenue[i]/(1+DiscountRate)**i)

  #Cum NPV
  B_CumNPV = np.cumsum(B_NPV)

  #IO (PV)
  IO = B_CapitolCost

  i = i + 1

#Individual Expenses and Revenue Calculations for New
SimulationDuration = 20 #in years/how long simulation runs for
N_Time = []
N_Capitol = []
N_EnergyCost = []
N_CoolingMaintenance = []
N_ITMaintenance = []
N_HeatRevenue = []
N_Net = []
N_NPV = []
N_CumNPV = []

i = 0;
while i <= SimulationDuration:
  N_Time.append(i)

  #Capitol Costs
  if i%N_Life == 0:
    N_Capitol.append(N_CapitolCost*(1+Inflation)**i)
  else:
    N_Capitol.append(0)

  #Energy Costs
  if i > 0:
    N_EnergyCost.append(ElectricityCost*N_EnergyUsage*(1+EnergyInflation)**(i-1))
  else:
    N_EnergyCost.append(0)

  #Cooling Maintenance
  if i>0:
    N_CoolingMaintenance.append(((N_MTBF/8760)*CoolingMaintenanceCost*(1+Inflation)**i)/1000000)
  else:
    N_CoolingMaintenance.append(0)

  #IT Maintenance
  if i>0:
    N_ITMaintenance.append((-N_AvoidedITFailures*ITMaintenanceCost*(1+Inflation)**i)/1000000)
  else:
    N_ITMaintenance.append(0)

  #Heat Revenue
  if i>0:
    N_HeatRevenue.append(-N_AnnualRecoveredHeat*RecoveredHeatValue*ElectricityCost*(1+EnergyInflation)**(i-1))
  else:
    N_HeatRevenue.append(0)

  #Net
  N_Net.append(N_Capitol[i]+N_EnergyCost[i]+N_CoolingMaintenance[i]+N_ITMaintenance[i]+N_HeatRevenue[i])

  #NPV
  N_NPV.append(N_Capitol[i]/(1+DiscountRate)**i+N_EnergyCost[i]/(1+DiscountRate)**i+N_CoolingMaintenance[i]/(1+DiscountRate)**i+N_ITMaintenance[i]/(1+DiscountRate)**i+N_HeatRevenue[i]/(1+DiscountRate)**i)

  #Cum NPV
  N_CumNPV = np.cumsum(N_NPV)

  #Inew (PV)
  Inew = N_CapitolCost

  i = i + 1

#ROI and IRR Calculations
i = 0
ROI = []
IRR = []

while i<=SimulationDuration:
  #ROI Calc
  if Inew-IO>0:
    ROI.append((B_CumNPV[i]-N_CumNPV[i])/(Inew-IO))
  else:
    ROI.append(0)
  #IRR Calc
  if i>0:
    IRR.append((1+ROI[i])**(1/i)-1)
  else:
    IRR.append(0)

  i=i+1

#Graphing
# plotting the points
plt.scatter(N_Time, ROI)
plt.plot([0, 20], [0, 0], 'r-')
plt.grid()
# naming the x axis
plt.xlabel('Year')
# naming the y axis
plt.ylabel('ROI')
plt.title('ROI')
plt.savefig(os.path.join(definitions.OUTPUT_DIR, "graphs", "cost_model_output_ROI"), 
            bbox_inches="tight")
plt.close()

# plotting the points
plt.scatter(N_Time, IRR)
plt.plot([0, 20], [0, 0], 'r-')
plt.grid()
# naming the x axis
plt.xlabel('Year')
# naming the y axis
plt.ylabel('IRR')
plt.title('IRR')
plt.savefig(os.path.join(definitions.OUTPUT_DIR, "graphs", "cost_model_output_IRR"), 
            bbox_inches="tight")
# plt.show()

#Finding the breakeven year
i = 1
while i<SimulationDuration:
  if(IRR[i]>0):
    BreakevenYear=i
    break
  i = i+1

print('The first breakeven year is at ' + str(BreakevenYear))

#Testing
#print(B_Time)
#print(B_Capitol)
#print(B_EnergyCost)
#print(B_CoolingMaintenance)
#print(B_ITMaintenance)
#print(B_HeatRevenue)
#print(B_Net)
#print(B_NPV)
#print(B_CumNPV)
#print(Inew)
#print(N_Capitol)
#print(N_EnergyCost)
#print(N_CoolingMaintenance)
#print(N_ITMaintenance)
#print(N_HeatRevenue)
#print(N_Net)
#print(N_NPV)
#print(N_CumNPV)
#print(IO)
#print(ROI)
#print(IRR)