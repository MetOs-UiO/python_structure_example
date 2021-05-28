import pandas as pd
import numpy as np
import sys,os,glob
import xarray as xr
import warnings
warnings.simplefilter("ignore")
# needed for betzy
os.environ['HDF5_USE_FILE_LOCKING']='FALSE'

NEG_LON2_POS_LON = 360. # xarray is dumb and doesnt understand negative longitude values - exception function should be used in case of other ice cores
SECONDS_IN_YEAR = 365.*24.*60.*60.
DATA_FOLDER = 'data'


def icecore_info(project_root):
    #### ICE CORE = UPPER FREEMONT GLACIER ####
    obs = pd.read_csv(f"{project_root}/{DATA_FOLDER}/Upper_freemont_glacier.csv")
    
    iceyear = obs['Mid_Year'][::-1]
    icedata = obs['BC_ng/g'][::-1].to_numpy()
    
    icelat= obs['lat'].iloc[0]
    icelon= obs['lon'].iloc[0]+NEG_LON2_POS_LON  
    
    return icedata, iceyear, icelat, icelon


def extract_relevant_data(project_root, var):
    # This function finds the model data based on path and variable and concatenates
    # it together if needed, then returns one dataarray with the sorted timeseries of the desired variable
    # ----------------------------------
    
    list_of_data = []
    for file in glob.glob(f"{project_root}/{DATA_FOLDER}/{var}*.nc"):
        opendata = xr.open_dataset(file)[var]
        list_of_data.append(opendata)

    if len(list_of_data) > 1:
        concatted = xr.concat(list_of_data,dim='time')
        opendata = concatted.sortby('time')
    elif len(list_of_data)==0:
        print('NO MATCHES FOR THIS PATH', project_root)
        sys.exit()
    else:
        opendata = list_of_data[0]
    return opendata

def make_concentration(project_root, icelat,icelon):
    wetbc_tot = extract_relevant_data(project_root,'wetbc')         # kg/m2/s
    drybc_tot = extract_relevant_data(project_root,'drybc')         # kg/m2/s
    prect_tot = extract_relevant_data(project_root,'pr')            # kg/m2/s
    area_tot  = xr.open_dataset(f"{project_root}/{DATA_FOLDER}/areacella_fx_CanESM5_historical_r1i1p1f1_gn.nc")['areacella']  # m2


    wetbc = wetbc_tot.sel(lat=icelat,lon=icelon,method='nearest').groupby('time.year').mean()  # kg/m2/s
    drybc = drybc_tot.sel(lat=icelat,lon=icelon,method='nearest').groupby('time.year').mean()  # kg/m2/s
    prect = prect_tot.sel(lat=icelat,lon=icelon,method='nearest').groupby('time.year').mean()  # kg/m2/s
    area  = area_tot.sel(lat=icelat,lon=icelon,method='nearest')                               # m2

    # Fine - I don't really need to do this but I often look at prec or dep alone so why not just have it there
    depbc = (np.absolute(wetbc) + np.absolute(drybc))*area.values*(SECONDS_IN_YEAR)               # kg
    prec  = prect*area.values*(SECONDS_IN_YEAR)                                                   # kg

    conc = (depbc/prec)*(1E12/1E3)                                                             # kg/kg --> ng/g

    return conc


print('working directory',os.getcwd())
project_path = os.getcwd()
ice_conc, iceyear, icelat, icelon = icecore_info(project_path)
print('path',type(ice_conc),type(iceyear))
model_conc = make_concentration(project_path,icelat,icelon)
print('Model concat',model_conc)
print('ice_conc',ice_conc)