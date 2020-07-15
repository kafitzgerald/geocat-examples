"""
NCL_proj_2_lg.py
================

This script illustrates the following concepts:
   - Drawing filled contours over a mercator map
   - Overlaying contours on a map without having lat,lon coordinates
   - Drawing a map using the medium resolution map outlines
   - Turning on map tickmark labels with degree symbols
   - Selecting a different color map
   - Turning off the addition of a longitude cyclic point
   - Zooming in on a particular area on a mercator map
   - Adding a color to an existing color map
   - Using best practices when choosing plot color scheme to accomodate visual impairments

See following URLs to see the reproduced NCL plot & script:
    - Original NCL script: https://www.ncl.ucar.edu/Applications/Scripts/native_2.ncl
    - Original NCL plot: https://www.ncl.ucar.edu/Applications/Images/native_2_lg.png
"""

###############################################################################

# Import packages:
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.feature as cfeature

import geocat.datafiles as gdf
from geocat.viz import util as gvutil
###############################################################################
# Read in data:
# Open a netCDF data file using xarray default engine and
# load the data into xarrays

ds = xr.open_dataset(("1994_256_FSD.nc"), decode_times=False)
t = ds.FSD.isel(time=0)

###############################################################################
# Plot:

# Generate figure (set its size (width, height) in inches)
fig = plt.figure(figsize=(10, 10))

# Generate axes using Cartopy and draw coastlines
ax = plt.axes(projection=ccrs.Mercator())
ax.coastlines(linewidths=0.5)
ax.add_feature(cfeature.LAND, facecolor='lightgray')

# Set extent to include latitudes from 34 to 52 and longitudes from 128
# to 144
ax.set_extent([128, 144, 34, 52], ccrs.PlateCarree())

# Contourf-plot data (for filled contours)
pt = t.plot.contourf(ax=ax, transform=ccrs.PlateCarree(), vmin=0, vmax=70,
                     levels=15, linewidths=0,cmap='inferno',
                     cbar_kwargs={
        "extendrect": True,
        "orientation": "vertical",
        "ticks": np.arange(0,71,5),
        "label": '',
        })



# Contour-plot data (for borderlines)
t.plot.contour(ax=ax, transform=ccrs.PlateCarree(),
                    levels=12, linewidths=0.5, cmap='k')

# Draw gridlines
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, dms=False, x_inline=False, y_inline=False, 
                  linewidth=1, color='k', alpha=0.5)

# Manipulate latitude and longitude gridline numbers and spacing
gl.ylocator = mticker.FixedLocator(np.arange(128, 145, 20))
gl.xlocator = mticker.FixedLocator(np.arange(34, 53, 20))

gl.top_labels = False
gl.right_labels = False
gl.xlines = False
gl.ylines = False
gl.xlocator = mticker.FixedLocator([130,134,138,142])
gl.ylocator = mticker.FixedLocator([36,38,40,42,44,46,48,50])
gl.xlabel_style = {'rotation':0}
gl.ylabel_style = {'rotation':0}

# Use geocat.viz.util convenience function to add titles to left and right
# of the plot axis.
gvutil.set_titles_and_labels(ax, maintitle="Native Mercator Projection",
                             lefttitle="Sfree surface deviation", righttitle="m")

# Show the plot
plt.show()
