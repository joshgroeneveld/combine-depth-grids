'''This script takes HAZUS-generated depth grids from two separate study regions
and combines them into one, countywide depth grid for each return period.  This
script assumes that depth grids have been created for multiple areas within a
county, generally two halves.  The depth grids from each half are in separate folders
and the depth grids have slightly different cell sizes.  The script takes depth
grids for each return period and resamples the smaller cell size rasters to match
the larger one, then mosaics to new raster the combined depth grid into a new
folder.'''

# Author: Josh Groeneveld
# Created On: 10.31.2018
# Updated On: 11.27.2018
# Copyright: 2018

import arcpy
import os
import sys
from docopt import docopt

# Get the county folder, the larger cell size depth grid folder and the small
# depth grid folder
county_folder = r"C:\Scripts\Combine_Depth_Grids\Testing\Kane"
large_cell_rasters = ""
small_cell_rasters = []
if os.path.isdir(os.path.join(county_folder, "Combined")) == False:
    os.mkdir(os.path.join(county_folder, "Combined"))
mosaic_output_folder = os.path.join(county_folder, "Combined")
# arcpy.env.workspace = small_cell_rasters
large_cell_size = 0.0

rpd_10_rasters = []
rpd_25_rasters = []
rpd_50_rasters = []
rpd_100_rasters = []
rpd_500_rasters = []
# # For raster in small cell size folder
# # Get the size of the large raster and small raster
# small_raster_size = arcpy.management.GetRasterProperties(small_cell_rasters + "\\rpd500", "CELLSIZEX")
# small_raster_size_output = small_raster_size.getOutput(0)
# print("Small raster size is: " + str(small_raster_size_output))
#
# large_raster_size = arcpy.management.GetRasterProperties(large_cell_rasters + "\\rpd500", "CELLSIZEX")
# large_raster_size_output = large_raster_size.getOutput(0)
# print("Large raster size is: " + str(large_raster_size_output))
# # resample (large cell size, nearest neighbor)
# raster_list = arcpy.ListDatasets('*', "Raster")
# print(raster_list)

# For all of the subfolders in the county folder, find the folder with the largest
# raster cell size
subfolders = []
for name in os.listdir(county_folder):
    if os.path.isdir(os.path.join(county_folder, name)):
        subfolders.append(name)
        small_cell_rasters.append(name)

# Remove subfolder Combined from list (if it exists) because this is where the output is stored
if 'Combined' in subfolders:
    subfolders.remove('Combined')
    small_cell_rasters.remove('Combined')

# Get the cell size of one raster in each folder
def get_raster_cell_size(subfolder):
    temp_raster_cell_size = arcpy.management.GetRasterProperties(os.path.join(county_folder, subfolder + "\\rpd500"), "CELLSIZEX")
    temp_raster_cell_size_output = temp_raster_cell_size.getOutput(0)
    raster_cell_size[subfolder] = temp_raster_cell_size_output

raster_cell_size = {}
for sub in subfolders:
    raster_cell_size[sub] = 0.0
    get_raster_cell_size(sub)

# Determine the subfolder with the largest cell size
def raster_with_max_cell_size(raster_cell_size_dictionary):
    v = list(raster_cell_size_dictionary.values())
    k = list(raster_cell_size_dictionary.keys())
    large_cell_subfolder = k[v.index(max(v))]
    large_cell_rasters = os.path.join(county_folder, large_cell_subfolder)
    global large_cell_size
    large_cell_size = max(v)
    small_cell_rasters.remove(large_cell_subfolder)
    print("Large cell size: " + str(large_cell_size))
    return large_cell_size

raster_with_max_cell_size(raster_cell_size)

# Resmaple all of the rasters in each subfolder that are smaller than the largest cell size
def resample_rasters(raster, cell_size, direction, return_period, out_folder):
    print("Large cell size: " + str(cell_size))
    resample_name = os.path.join(out_folder, raster + direction + "re")
    arcpy.management.Resample(in_raster=raster, out_raster=resample_name, cell_size=large_cell_size, resampling_type="NEAREST")
    if return_period == 'rpd10':
        rpd_10_rasters.append(resample_name)
    elif return_period == 'rpd25':
        rpd_25_rasters.append(resample_name)
    elif return_period == 'rpd50':
        rpd_50_rasters.append(resample_name)
    elif return_period == 'rpd100':
        rpd_100_rasters.append(resample_name)
    else:
        # return period must be 500
        rpd_500_rasters.append(resample_name)
    print("Resampled " + str(raster))

# mosaic to new raster (resampled dg + existing dg from large cell size folder,
# MAXIMUM, 32-bit float)
def mosaic_rasters(list_of_rasters_to_mosaic, return_period):
    print("Mosaicking: " + str(return_period))
    mosaic_name = (return_period + "mosaic")
    arcpy.management.MosaicToNewRaster(input_rasters=list_of_rasters_to_mosaic, output_location=mosaic_output_folder,
        raster_dataset_name_with_extension=mosaic_name, pixel_type="32_BIT_FLOAT", cellsize=large_cell_size,
        number_of_bands=1, mosaic_method="MAXIMUM")
    print("Mosaicked: " + str(return_period))

for small_raster_folder in small_cell_rasters:
    folder_path = os.path.join(county_folder, small_raster_folder)
    arcpy.env.workspace = folder_path
    direction = small_raster_folder[:2]
    raster_list = arcpy.ListDatasets('*', "Raster")
    for small_raster in raster_list:
        return_period = str(small_raster)
        resample_rasters(small_raster, large_cell_size, direction, return_period, folder_path)

return_periods = ['rpd10', 'rpd25', 'rpd50', 'rpd100', 'rpd500']
arcpy.env.workspace = mosaic_output_folder
for return_period in return_periods:
    rasters_to_mosaic = []
    if return_period == 'rpd10':
        rasters_to_mosaic = rpd_10_rasters
    elif return_period == 'rpd25':
        rasters_to_mosaic = rpd_25_rasters
    elif return_period == 'rpd50':
        rasters_to_mosaic = rpd_50_rasters
    elif return_period == 'rpd100':
        rasters_to_mosaic = rpd_100_rasters
    else:
        # Return period must be rpd 500
        rasters_to_mosaic = rpd_500_rasters
    mosaic_rasters(rasters_to_mosaic, return_period)

print("Done")
