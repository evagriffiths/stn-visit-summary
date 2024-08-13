import pandas as pd
import numpy as np

# Sample DataFrame with duplicate column names
df = pd.DataFrame({
    'column_name': [np.array(['a', 'b']), np.array(['c', 'd'])],
    'column_name': [np.array(['e', 'f']), np.array(['g', 'h'])],
    'other_column': [1, 2]
})

# Define a function to combine arrays
def combine_arrays(arrays):
    # Filter out non-ndarray items and ensure there are arrays to concatenate
    arrays = [a for a in arrays if isinstance(a, np.ndarray)]
    if not arrays:
        return np.array([])  # Return empty array if no arrays are present
    return np.concatenate(arrays)

# Combine duplicate columns
def combine_duplicate_columns(df):
    # Create a dictionary to hold combined columns
    combined_columns = {}
    
    # Loop through column names and combine arrays
    for col in df.columns:
        if col not in combined_columns:
            # Get all columns with the same name
            cols_to_combine = [df[col]]
            
            # Check if the column name already exists in combined_columns
            if col in combined_columns:
                cols_to_combine.append(combined_columns[col])
            
            # Combine the arrays
            combined_columns[col] = pd.concat(cols_to_combine, axis=1).apply(lambda row: combine_arrays(row), axis=1)
    
    # Create a new DataFrame from combined columns
    combined_df = pd.DataFrame(combined_columns)
    
    return combined_df

# Apply the function to combine columns
combined_df = combine_duplicate_columns(df_tmp)

print(combined_df)
