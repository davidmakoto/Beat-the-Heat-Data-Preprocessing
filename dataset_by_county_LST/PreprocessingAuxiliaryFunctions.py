import geopandas as gpd
import rasterio
from rasterio import mask
import datetime as dt
from osgeo import gdal
import numpy as np
import scipy.ndimage
import pandas as pd
import os

class PreprocessingAuxiliaryFunctions:


    def __init__(self):
        # Setting up input directories
        self.out_dir = self.create_abs_path_from_relative('burn_area_files\\output')
        self.Support = self.create_abs_path_from_relative('input_data_files\\supp_files')
        self.img_files_dir = self.create_abs_path_from_relative('input_data_files\\day')
        self.img_QA_dir = self.create_abs_path_from_relative('input_data_files\\QC_day')
        self.BA_burn_date_dir = self.create_abs_path_from_relative('burn_area_files\\burn_date')
        self.BA_QA_dir = self.create_abs_path_from_relative('burn_area_files\\QA')
        self.LST_temp    = "LST_temp.tif"
        self.LSTQA_temp  = "LSTQA_temp.tif"
        self.BA_temp     = "BA_temp.tif"
        self.BAQA_temp   = "BAQA_temp.tif"

    def create_abs_path_from_relative(self,relative_dir_path):
        """ Creates relative path from current directory to input file: 'input_data_files' in project dir """
        absolutepath = os.path.abspath(__file__)
        fileDirectory = os.path.dirname(absolutepath)
        return os.path.join(fileDirectory, relative_dir_path)  #Navigate to relative_dir_path directory

    def create_paths(self):
        pass

    def read_geojson(self):
        """ Loading county boundaries via geojson - returns arr of county geometry shapes """
        # source: https://gis.data.ca.gov/datasets/8713ced9b78a4abb97dc130a691a8695_0?geometry=-146.754%2C31.049%2C-91.251%2C43.258&page=7
        CA_cnty_geojson_link = 'https://opendata.arcgis.com/datasets/8713ced9b78a4abb97dc130a691a8695_0.geojson'
        CA_county_boundaries_gdf = gpd.read_file(CA_cnty_geojson_link)

        # * storing all boundaries in list var shapes
        shapes = [x for x in CA_county_boundaries_gdf['geometry']]
        county_shapes = []
        for i in range(58):
            county_shapes.append(shapes[i])
        return county_shapes

    def read_geojson_geodf(self):
        """ Loading county boundaries via geojson - returns arr of county geometry shapes """
        # source: https://gis.data.ca.gov/datasets/8713ced9b78a4abb97dc130a691a8695_0?geometry=-146.754%2C31.049%2C-91.251%2C43.258&page=7
        CA_cnty_geojson_link = 'https://opendata.arcgis.com/datasets/8713ced9b78a4abb97dc130a691a8695_0.geojson'
        return gpd.read_file(CA_cnty_geojson_link)
    
    def extract_shapes_from_county_geometry(self, county_geodf):
        # * storing all boundaries in list var shapes
        # return [x for x in county_geodf['geometry']]

        shapes = [x for x in county_geodf['geometry']]
        county_shapes = []
        for i in range(58):
            county_shapes.append(shapes[i])
        return county_shapes

    def extracting_good_quality_vals_from_LST_lut(self, lut):
        """ Returns good quality values via look up table (LUT) """
        # Include good quality based on MODLAND
        lut = lut[lut['MODLAND'].isin(['VI produced with good quality', 'VI produced, but check other QA'])]

        # Exclude lower quality VI usefulness
        VIU =["Lowest quality","Quality so low that it is not useful","L1B data faulty","Not useful for any other reason/not processed"]
        lut = lut[~lut['VI Usefulness'].isin(VIU)]

        lut = lut[lut['Aerosol Quantity'].isin(['Low','Average'])]   # Include low or average aerosol
        lut = lut[lut['Adjacent cloud detected'] == 'No' ]           # Include where adjacent cloud not detected
        lut = lut[lut['Mixed Clouds'] == 'No' ]                      # Include where mixed clouds not detected
        lut = lut[lut['Possible shadow'] == 'No' ]                   # Include where possible shadow not detected

        LSTgoodQuality = list(lut['Value']) # Retrieve list of possible QA values from the quality dataframe
        return LSTgoodQuality

    def extracting_good_quality_vals_from_BA_lut(self, lut):
        """ Returns good quality values via BA look up table (LUT) """
        # Include good quality based on MODLAND
        lut = lut[lut['Valid data'].isin([True])]
        
        # Special circumstances unburned
        SP =["Too few training observations or insufficient spectral separability between burned and unburned classes"]
        lut = lut[~lut['Special circumstances unburned'].isin(SP)]
        BAgoodQuality = list(lut['Value']) # Retrieve list of possible QA values from the quality dataframe

        return BAgoodQuality

    def extracting_good_quality_vals_from_lut_LST(self, lut):

        # Include good quality based on MODLAND
        lut = lut[lut['MODLAND'].isin([
            'LST produced, good quality, not necessary to examine more detailed QA',
            'LST produced, other quality, recommend examination of more detailed QA'])]

        # Exclude lower quality VI usefulness
        VIU = ["LST not produced due to cloud effects, LST not produced primarily due to reasons other than cloud"]
        lut = lut[~lut['MODLAND'].isin(VIU)]
        return list(lut['Value'])  # Retrieve list of possible QA values from the quality dataframe



    def go_to_parent_dir(self):
        path_parent = os.path.dirname(os.getcwd())
        os.chdir(path_parent)


    def getBAFileName(self,BAF, month, year):
        """ Input: List of File Names, int month, int year """
        """ Returns: File Name of the month and year requested  """
        for x in BAF:
            # File name metadata:
            BAproductId = x.split('_')[0]                                               # First: product name
            BAlayerId = x.split(BAproductId + '_')[1].split('_doy')[0]                  # Second: layer name
            BAyeardoy = x.split(BAlayerId+'_doy')[1].split('_aid')[0]                   # Third: date
            file_year = dt.datetime.strptime(BAyeardoy, '%Y%j').year                    # Compares the date of the LST and BA to grab the right file, m and y are for LST tif
            file_month = dt.datetime.strptime(BAyeardoy, '%Y%j').month
            if file_year==year  and file_month == month:
                return(x) 

    def getLST_Date_Year_Month(self,productName, option):
        """ Input: List of File Name, option: Y=year, M=month, D=date """
        """ Returns: int Month or int Year, or String Date format MM/DD/YYYY"""
        LSTproductId = productName.split('_')[0]                                      # First: product name
        LSTlayerId   = productName.split(LSTproductId + '_')[1].split('_doy')[0]      # Second: layer name
        LSTyeardoy   = productName.split(LSTlayerId+'_doy')[1].split('_aid')[0]       # Third: date
        LSTaid       = productName.split(LSTyeardoy+'_')[1].split('.tif')[0]          # Fourth: unique ROI identifier (aid)
        LSTdate      = dt.datetime.strptime(LSTyeardoy, '%Y%j').strftime('%m/%d/%Y')  # Convert YYYYDDD to MM/DD/YYYY
        LST_year     = dt.datetime.strptime(LSTyeardoy, '%Y%j').year
        LST_month    = dt.datetime.strptime(LSTyeardoy, '%Y%j').month 
        if option == "Y":
            return(LST_year) 
        elif option == "M":
            return(LST_month)
        else:
            return(LSTdate)

    #def maskByShapefileAndStore(self, LSTFile, LSTqualityFile, BAFileName, BAQAFileName, county_shape):
    def maskByShapefileAndStore(self, LSTFile, LSTqualityFile, county_shape):
        # Change to LST directory
        os.chdir(self.img_files_dir)                                                            
        LSTFile     = rasterio.open(LSTFile, 'r+')                                              # load LST 
        os.chdir(self.img_QA_dir)                                                               # change to QA directory
        LSTQAFile   = rasterio.open(LSTqualityFile, 'r+')                                       # load LST QA tif file

        # Change to BA directory    
        #os.chdir(self.BA_burn_date_dir)
        #BAFile      = rasterio.open(BAFileName, 'r+')                                           # load BA tif file
        #os.chdir(self.BA_QA_dir)
        #BAQAFile    = rasterio.open(BAQAFileName, 'r+')                                         # load BA QA tif file

        # Mask all 4 tif files by the shapefile
        LST_out_image, LST_out_transform     = rasterio.mask.mask(LSTFile, county_shape, crop=True)     
        LSTQA_out_image, LSTQA_out_transform = rasterio.mask.mask(LSTQAFile, county_shape, crop=True)   
        #BA_out_image, BA_out_transform       = rasterio.mask.mask(BAFile, county_shape, crop=True)      
        #BAQA_out_image, BAQA_out_transform   = rasterio.mask.mask(BAQAFile, county_shape, crop=True)   

        # Get Metadata from source file and prepare for output file
        LST_out_meta    = LSTFile.meta                                                                 
        LSTQA_out_meta  = LSTQAFile.meta                                                               
        #BA_out_meta     = BAFile.meta                                                                  
        #BAQA_out_meta   = BAQAFile.meta                                                                

        # Update output Matedata and send to a temp files.
        self.send_to_file(LST_out_meta, LST_out_transform, LST_out_image, self.LST_temp)               
        self.send_to_file(LSTQA_out_meta, LSTQA_out_transform, LSTQA_out_image, self.LSTQA_temp)       
        #self.send_to_file(BA_out_meta, BA_out_transform, BA_out_image, self.BA_temp)                   
        #self.send_to_file(BAQA_out_meta, BAQA_out_transform, BAQA_out_image, self.BAQA_temp)           

    def send_to_file(self, out_metadata, out_transform, output_image, out_file_name):
        #update metadata
        out_metadata.update({"driver": "GTiff",         
                "height": output_image.shape[1],
                "width": output_image.shape[2],
                "transform": out_transform})
        #change to output directory
        os.chdir(self.out_dir)
        #write to file
        with rasterio.open(out_file_name, "w", **out_metadata) as dest:
            dest.write(output_image)

    def get_scaled_df(self, df_band, df_data, df_scaled_factor):
        df_fill                        = df_band.GetNoDataValue()                               # Returns fill value
        df_data[df_data == df_fill]    = np.nan                                                 # Set the fill value equal to NaN for the MaskedArray
        return (df_data * df_scaled_factor)                                                     # Return Dataframe Scaled
