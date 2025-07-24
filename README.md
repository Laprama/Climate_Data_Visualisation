## Climate Data Visualisation Project
This Repo will store work on my current project regarding visualisation of atmospheric data on map(s) of the Earth.
This README.md file will be updated as the project progresses. 

## Setup
This code has been tested with 'Python 3.1.0'. 
To get started create an environment using the command 'pip install -r requirements.txt'.

## Dowloading Climate Data 
The data used in this project is from the TROPOMI (TROPOspheric Monitoring Instrument) satellite. 
You can download the data that you wish to use from the CEDA data archive and adjust references to data as necessary in the code :  https://catalogue.ceda.ac.uk/uuid/2b8c6a8f1abd40a6b0ce07c40b1c57ff/ 

This project is currently set up to use data from the entire year for 2023.
In the CEDA data archive the processed data files are stored in folders named 01-12 referring to the months January-December. 
There is one file per day. 
These folders 01-12 should be placed in the Data/ folder of this project. 

The entire set of 2023 data can be downloaded using WGET (21.8GB) via the command line with the command: 
 wget -e robots=off --mirror --no-parent -r https://dap.ceda.ac.uk/neodc/esacci/ghg/data/cci_plus/CH4_S5P_WFMD/v1.8_extended_june2024/2023/ 
