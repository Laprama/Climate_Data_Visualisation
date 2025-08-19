import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import glob
import pandas as pd
import os

# ================= SCRIPT PARAMETERS =================

# --- Data and Output ---
# Define the root folder where the monthly data folders ('01', '02', etc.) are located.
DATA_ROOT_FOLDER = 'Data/'
# Set the folder to save figures in. The folder will be created inside a 'Figures/' directory.
SAVE_FOLDER = 'cumulative_data_density/'
# Define the resolution for binning data points. 0 rounds to the nearest whole number (e.g., 1-degree grid).
# Use 1 for 0.1-degree resolution, 2 for 0.01-degree, etc.
GRID_RESOLUTION = 1

# --- Time Increments ---
# Define the cumulative number of days for each plot you want to generate.
# The script will create a plot for 1 day, then 2 days, ..., up to 365.
# Example for first 5 days, then jumping: [1, 2, 3, 4, 5, 10, 30, 60, 90, 180, 365]
# DAY_INCREMENTS = list(range(1, 31)) + [60, 90, 180, 365]
DAY_INCREMENTS = list(range(1, 31)) + [60, 90, 180, 365]


# --- Plotting Style ---
COLOURED_LAND_AND_SEA = False
PLOT_SEA_DATA = True # If True, plots all data points. If False, plots only points over land.
SHOW_COLOR_BAR_AND_TITLE = False

# Define colors for the plot
if COLOURED_LAND_AND_SEA:
    SEA_COLOR = "lightblue"
    LAND_COLOR = "lightgrey"
else:
    SEA_COLOR = "white"
    LAND_COLOR = "white"

BORDER_COLOR = "black"
COASTLINE_COLOR = "black"


# ================= SCRIPT EXECUTION =================

def create_cumulative_density_plots():
    """
    Main function to find data files, process them in cumulative increments,
    and generate density plots.
    """
    # Create the output directory if it doesn't exist
    output_path = os.path.join('Figures', SAVE_FOLDER)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Created directory: {output_path}")

    # Find all NetCDF files recursively in the data directory and sort them.
    # This assumes filenames are sortable chronologically (e.g., S5P_...__20230101_...).
    all_files = sorted(glob.glob(os.path.join(DATA_ROOT_FOLDER, '**', '*.nc'), recursive=True))

    if not all_files:
        print(f"Error: No .nc files found in '{DATA_ROOT_FOLDER}'. Please check the path.")
        return

    print(f"Found {len(all_files)} total data files.")

    # Main loop to process data for each specified day increment
    for num_days in DAY_INCREMENTS:
        if num_days > len(all_files):
            print(f"Warning: Requested {num_days} days, but only {len(all_files)} files are available. Skipping.")
            continue

        print(f"\nProcessing data for the first {num_days} day(s)...")
        files_to_process = all_files[:num_days]

        # Read and combine lat/lon data from the selected files
        df_list = []
        for f_name in files_to_process:
            try:
                with xr.open_dataset(f_name) as ds:
                    # Extract latitude and longitude, flatten to 1D arrays
                    lat = ds['latitude'].values.flatten()
                    lon = ds['longitude'].values.flatten()

                    # Create a temporary DataFrame
                    temp_df = pd.DataFrame({'lat': lat, 'lon': lon})
                    df_list.append(temp_df)
            except Exception as e:
                print(f"Could not process file {f_name}. Error: {e}")

        if not df_list:
            print("No data could be processed for this increment. Skipping plot.")
            continue

        # Concatenate all data into a single DataFrame
        cumulative_data = pd.concat(df_list, ignore_index=True).dropna()

        # Bin the data by rounding coordinates
        cumulative_data['lat'] = cumulative_data['lat'].round(GRID_RESOLUTION)
        cumulative_data['lon'] = cumulative_data['lon'].round(GRID_RESOLUTION)

        # Calculate the density by counting occurrences of each lat/lon pair
        density_df = cumulative_data.groupby(['lat', 'lon']).size().reset_index(name='count')

        # Generate and save the plot
        plot_data_density(density_df, num_days, output_path)

    print("\nScript finished.")


def plot_data_density(data_df, num_days, output_path):
    """
    Generates and saves a single density plot for a given dataset.
    """
    print(f"Plotting density for {num_days} day(s)...")

    # --- Plot Setup ---
    dpi = 500
    fig = plt.figure(figsize=(20, 10), dpi=dpi)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.set_facecolor(SEA_COLOR)

    # Add land and ocean features
    ax.add_feature(cfeature.LAND.with_scale('110m'), facecolor=LAND_COLOR, edgecolor='none')
    ax.add_feature(cfeature.OCEAN, facecolor=SEA_COLOR, edgecolor='none')

    # --- Data Plotting ---
    lat = data_df['lat'].values
    lon = data_df['lon'].values
    count = data_df['count'].values

    # Use a sequential colormap which is good for representing counts
    cmap = 'viridis_r'

    sc = ax.scatter(
        lon, lat, c=count, s=1,
        marker='.',
        edgecolors='none',
        cmap=cmap, transform=ccrs.PlateCarree(),
        vmin=1,
        vmax=10
    )

    # Add borders and coastlines for context
    ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor=BORDER_COLOR, linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE, edgecolor=COASTLINE_COLOR, linewidth=0.5)

    # --- Labels and Titles ---
    if SHOW_COLOR_BAR_AND_TITLE:
        cbar = plt.colorbar(sc, ax=ax, orientation='vertical', pad=0.02, shrink=0.8)
        cbar.set_label(f'Cumulative Data Point Count', fontsize=12, labelpad=10)
        ax.set_title(f'TROPOMI Data Point Density (First {num_days} Day(s))', size=16, pad=20)

    # Remove the rectangle around the map
    ax.set_frame_on(False)

    # --- Final Touches and Save ---
    # Use a filename with padded zeros to ensure correct sorting
    filename = f'density_{num_days:04d}_days.png'
    save_path = os.path.join(output_path, filename)
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.close(fig) # Close the figure to free up memory
    print(f"Saved plot: {save_path}")


# ================= RUN SCRIPT =================
if __name__ == '__main__':
    create_cumulative_density_plots()
