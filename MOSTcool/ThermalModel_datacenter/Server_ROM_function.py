import numpy as np
import pandas as pd
import h5py
from scipy.interpolate import interp1d

# Read modes and coefficients from CSV files outside the function
Modes = pd.read_csv('Modes.csv')
modes = Modes.to_numpy()

Coeff = pd.read_csv('Coeff.csv')
coeff = Coeff.to_numpy()

# Define the velocity range for which the coefficients are known
vel = np.arange(6, 16)

def predict_temperature(new_velocity, modes, coeff, vel, solution_path):
    # Interpolate coefficients for each POD mode
    interp_funcs = [interp1d(vel, coeff[i, :], kind='linear') for i in range(coeff.shape[0])]
    
    # Predict coefficients for the new velocity
    new_coeff = np.array([f(new_velocity) for f in interp_funcs])
    
    # Calculate the predicted temperature field
    T_pred = sum(new_coeff[i] * modes[:, i] for i in range(coeff.shape[0]))
    
    # Update the temperature data in the solution file
    with h5py.File(solution_path, 'r+') as f:
        temperature_path = 'Base/Zone/FlowSolution.N:1/Temperature/ data'
        if temperature_path in f:
            f[temperature_path][:] = T_pred
        else:
            raise KeyError(f"Path {temperature_path} not found in the file.")
    
    # Extract the temperature at points of interest
    with h5py.File(solution_path, 'r') as f:
        pointlist_path = 'Base/Zone/ZoneBC/cpu-pcb-1-wall/PointList/ data'
        pointlist = f[pointlist_path][:]
        pointlist_flat = np.ravel(pointlist)
        
        # Paths to the X, Y, Z coordinates and temperature in the CGNS file
        x_path = 'Base/Zone/GridCoordinates/CoordinateX/ data'
        y_path = 'Base/Zone/GridCoordinates/CoordinateY/ data'
        z_path = 'Base/Zone/GridCoordinates/CoordinateZ/ data'
        temperature_path = 'Base/Zone/FlowSolution.N:1/Temperature/ data'
        
        # Retrieve the coordinate and temperature data
        x = f[x_path][:]
        y = f[y_path][:]
        z = f[z_path][:]
        temperature = f[temperature_path][:]
        
        # Create a DataFrame and map the temperature to the points of interest
        df_temp = pd.DataFrame({'X': x, 'Y': y, 'Z': z, 'Temperature': temperature})
        df_mapped = df_temp.iloc[pointlist_flat]
        
    # Calculate the average temperature
    average_temperature = df_mapped['Temperature'].mean()
    return average_temperature

# Define the variables
new_velocity = 14  # New velocity to predict
solution_path = "solution_PythonPOD_Solid.cgns"

# Call the function
average_temp = predict_temperature(new_velocity, modes, coeff, vel, solution_path)
print(f"Average Temperature at velocity {new_velocity}: {average_temp}")
