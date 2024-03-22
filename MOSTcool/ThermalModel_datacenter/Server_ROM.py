import numpy as np
import pandas as pd
import h5py
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

Modes=pd.read_csv('Modes.csv')
modes=Modes.to_numpy()

Coeff=pd.read_csv('Coeff.csv')
coeff=Coeff.to_numpy()

vel=[]
for i in range(6,16):
    vel.append(i)

vel=np.array(vel)


# Interpolation for each POD mode
interp_funcs = [interp1d(vel, coeff[i, :], kind='linear') for i in range(coeff.shape[0])]

# Predict coefficients for a new velocity
new_velocity = 14  # Example in-between velocity
new_coeff = np.array([f(new_velocity) for f in interp_funcs])

T_pred = np.zeros_like(modes[:, 0])  # Extracts the first column of U_reduced, representing the coefficients associated with the first mode

for i in range(coeff.shape[0]):
    T_pred = T_pred + new_coeff[i] * modes[:, i]


solution_path = r"solution_PythonPOD_Solid.cgns"

with h5py.File(solution_path, 'r+') as f:  # Open the file in read/write mode
    temperature_path = 'Base/Zone/FlowSolution.N:1/Temperature/ data'

    if temperature_path in f:
        # Update the temperature data
        f[temperature_path][:] = T_pred
    else:
        print(f"Path {temperature_path} not found in the file.")
    