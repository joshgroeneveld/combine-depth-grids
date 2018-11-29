# combine-depth-grids
Combine HAZUS-generated depth grids from multiple, small areas into one larger area (e.g., county)

This script takes HAZUS-generated depth grids from two separate study regions
and combines them into one, countywide depth grid for each return period.  This
script assumes that depth grids have been created for multiple areas within a
county, generally two halves.  The depth grids from each half are in separate folders
and the depth grids have slightly different cell sizes.  The script takes depth
grids for each return period and resamples the smaller cell size rasters to match
the larger one, then mosaics to new raster the combined depth grid into a new
folder.
