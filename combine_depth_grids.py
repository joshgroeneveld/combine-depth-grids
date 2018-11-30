"""
combine-depth-grids

Usage:
    combine_depth_grids.py <county_folder>
    combine_depth_grids.py -h | --help
    combine_depth_grids.py --version

Options:
    -h, --help          Show this screen
    -- version          Show version

"""

import arcpy
import os
import sys
from docopt import docopt

# Get the county folder, the larger cell size depth grid folder and the small
# depth grid folder
county_folder = sys.argv[1]
large_cell_rasters = ""
small_cell_rasters = []
if os.path.isdir(os.path.join(county_folder, "Combined")) == False:
    os.mkdir(os.path.join(county_folder, "Combined"))
mosaic_output_folder = os.path.join(county_folder, "Combined")

large_cell_size = 0.0

rpd_10_rasters = []
rpd_25_rasters = []
rpd_50_rasters = []
rpd_100_rasters = []
rpd_500_rasters = []

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
    # add the large rasters to the lists of rasters to mosaic in the end
    arcpy.env.workspace = large_cell_rasters
    large_raster_list = arcpy.ListDatasets('*', "Raster")
    for large_raster in large_raster_list:
        return_period = str(large_raster)
        large_raster_name = os.path.join(large_cell_rasters, large_raster)
        if return_period == 'rpd10':
            rpd_10_rasters.append(large_raster_name)
        elif return_period == 'rpd25':
            rpd_25_rasters.append(large_raster_name)
        elif return_period == 'rpd50':
            rpd_50_rasters.append(large_raster_name)
        elif return_period == 'rpd100':
            rpd_100_rasters.append(large_raster_name)
        else:
            # return period must be 500
            rpd_500_rasters.append(large_raster_name)
    global large_cell_size
    large_cell_size = max(v)
    small_cell_rasters.remove(large_cell_subfolder)
    print("Large cell size: " + str(large_cell_size))
    return large_cell_size

raster_with_max_cell_size(raster_cell_size)

# Resmaple all of the rasters in each subfolder that are smaller than the largest cell size
def resample_rasters(raster, cell_size, direction, return_period, out_folder):
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

if __name__ == '__main__':
    arguments = docopt(__doc__, argv=None, help=True, version="Combine Depth Grids 0.2.0", options_first=False)
    print(arguments)
