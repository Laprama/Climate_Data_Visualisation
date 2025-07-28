import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely.geometry import Point
import geopandas as gpd
from cartopy.io import shapereader
import glob
import pandas as pd
import os


# This script is written to create custom monthly plots of methane levels on earth in 4k resolution

# User Input Script Parameters________________________________________________________________________
# Here the user inputs parameters to customise their plots
coloured_land_and_sea = False # If True sea is coloured blue and land green, else they are left white 
plot_sea = True # If True, methane levels are plotted on the Sea  - if false then only on land
colour_bar_and_title = True # If True then colour bar and plot title are include in the plots
variable = 'xch4' # The variable to plot is currently hardcoded in script to xch4, in future will update to choose from --> 'xch4', 'xch4_uncertainty', 'xco', 'xco_uncertainty' which correspond to methane, methane uncertainty, carbon monoxide and carbon monoxide uncertainty

save_folder = 'new_folder/' # Set the folder to save in , folder will be created within the Figures/ directory if it does not alredy exist there

# End of User Input parameters __________________________________________________________________________

# Create save folder if it doesn't exist
if not os.path.exists('Figures/' + save_folder):
    os.makedirs('Figures/' + save_folder)

# Define Land and Sea Colours based on script input
if coloured_land_and_sea == True:
    SEA_COLOR = "mediumblue"  
    LAND_COLOR = "lightgreen" 
else:
    SEA_COLOR = "white"  
    LAND_COLOR = "white" 
    
BORDER_COLOR = "black"      # Country border color
COASTLINE_COLOR = "black"   # Coastline color


# The folders storing satellite data are numbered with numbers corresponding to months
month_list = ['January','February','March', 'April', 'May', 'June' , 'July', 'August', 'September', 'October', 'November', 'December']
folder_list = ['01','02', '03', '04', '05', '06', '07', '08', '09','10','11','12']

folder_to_month_dict = {}
for folder, month in zip(folder_list, month_list):
    folder_to_month_dict[folder] = month

#Create and save plots ________________________________________
# Colour bar plot has custom min / max values
min_val = 1750 
max_val = 1950

for folder in folder_list:

    # Find all NetCDF files in the folder
    file_list = sorted(glob.glob('Data/' + folder + '/*.nc'))
    
    # Initialize empty list to collect DataFrames
    df_list = []
    
    # Loop over each file
    for f_name in file_list:
        ds = xr.open_dataset(f_name)
    
        # Extract variables
        lat = ds['latitude']
        lon = ds['longitude']
        xch4 = ds['xch4']
    
        # Mask invalid values
        valid = (xch4 > 0) & (~xch4.isnull())
        lat_valid = lat.where(valid, drop=True)
        lon_valid = lon.where(valid, drop=True)
        xch4_valid = xch4.where(valid, drop=True)
    
        # Round lat/lon to 2 decimal places to bin similar points
        lat_rounded = lat_valid.round(0)   # use 0 if coarse binning is okay; 2 if you want finer grouping
        lon_rounded = lon_valid.round(0)
    
        # Create DataFrame
        df = pd.DataFrame({
            'lat': lat_rounded.values,
            'lon': lon_rounded.values,
            'xch4': xch4_valid.values
        }).dropna()
    
        df_list.append(df)
    
    # Concatenate all DataFrames
    all_data = pd.concat(df_list, ignore_index=True)
    
    # Group by (lat, lon) and calculate mean
    mean_df = all_data.groupby(['lat', 'lon'], as_index=False).mean()

    #Plot the mean dataframe __________________________________________________________
    dpi = 96
    width_in = 4096 / dpi
    height_in = 2048 / dpi

    # Extract data from mean_df
    lat = mean_df['lat'].values
    lon = mean_df['lon'].values
    xch4 = mean_df['xch4'].values
    
    # Load land polygons for masking
    land = gpd.read_file("shapefiles/ne_10m_admin_0_countries.shp")  # Adjust path if needed
    
    # Convert lat/lon to Point geometries
    points = gpd.GeoSeries([Point(lon[i], lat[i]) for i in range(len(lat))], crs="EPSG:4326")
    
    # Create GeoDataFrame
    points_gdf = gpd.GeoDataFrame(geometry=points)
    
    # Spatial join to keep only land points
    land_points = gpd.sjoin(points_gdf, land, how="inner", predicate="within")
    
    # Extract only valid land indices
    valid_indices = land_points.index
    lat_land = lat[valid_indices]
    lon_land = lon[valid_indices]
    xch4_land = xch4[valid_indices]
    
    # Plot
    fig = plt.figure(figsize=(width_in, height_in), dpi=dpi)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.set_facecolor(SEA_COLOR)  # Define SEA_COLOR as needed
    
    # Add land layer
    ax.add_feature(cfeature.LAND.with_scale('110m'), facecolor=LAND_COLOR, edgecolor='none')  # Define LAND_COLOR
    
    if plot_sea:
        #test
         sc = ax.scatter(
            lon, lat, c=xch4, s=62,
            cmap="magma", transform=ccrs.PlateCarree(),
            vmin=min_val,  # Sets the minimum of the color scale
            vmax=max_val   # Sets the maximum of the color scale
        )
        
    
    else:
        # Scatter plot
        sc = ax.scatter(
            lon_land, lat_land, c=xch4_land, s=62,
            cmap="magma", transform=ccrs.PlateCarree(),
            vmin=min_val,  # Sets the minimum of the color scale
            vmax=max_val   # Sets the maximum of the color scale
        )
    
    # Add borders and coastlines
    ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor=BORDER_COLOR)  # Define BORDER_COLOR
    ax.add_feature(cfeature.COASTLINE, edgecolor=BORDER_COLOR)
    
    if colour_bar_and_title:
        # Add colorbar
        cbar = plt.colorbar(sc, pad=0.05)
        cbar.ax.tick_params(labelsize=20)  # Change tick label font size
        cbar.set_label('Methane Concentration (xch4 ppb)', fontsize=30 , labelpad = 30)
        
        #Custom positioning - this code changes the positioning  & size of the colour bar slightly for a better looking figure
        orig_pos = cbar.ax.get_position()
        cbar.ax.set_position([orig_pos.x0 - 0.02 , orig_pos.y0 + 0.05, orig_pos.x1, orig_pos.y1*0.75])

        month = folder_to_month_dict[folder]  
        plt.title(month + ' 2023 TROPOMI CH₄ (Averaged by ° Grid)', size = 30 , pad = 40)
        
    ax.set_xticks([])
    ax.set_yticks([])
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.savefig('Figures/' + save_folder + folder + '_xch4.png', dpi = 96, bbox_inches='tight', pad_inches=0)
    plt.show()
