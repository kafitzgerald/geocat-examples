"""
NCL_sat_1.py
===============
This script illustrates the following concepts:
   - Creating an orthographic projection
   - Drawing line contours over a satellite map
   - Manually labeling contours
   - Transforming coordinates

See following URLs to see the reproduced NCL plot & script:
    - Original NCL script: https://www.ncl.ucar.edu/Applications/Scripts/sat_1.ncl
    - Original NCL plot: https://www.ncl.ucar.edu/Applications/Images/sat_1_lg.png
"""

###############################################################################
# Import packages:
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

import geocat.datafiles as gdf
import geocat.viz.util as gvutil

###############################################################################
# Read in data:

# Open a netCDF data file using xarray default engine and load the data into xarrays
ds = xr.open_dataset(gdf.get("netcdf_files/slp.1963.nc"), decode_times=False)

# Get data from the 24th timestep
U = ds.slp[24, :, :]

# Translate short values to float values
U = U.astype('float64')

# Convert Pa to hPa data
U = U*0.01

# Fix the artifact of not-shown-data around 0 and 360-degree longitudes
wrap_U = gvutil.xr_add_cyclic_longitudes(U, "lon")

###############################################################################

def findCoordPressureData(coordarr, lat, lon):
    # Finds pressure at coordinate given lat, lon, and an array of all the coordinates with data
    # Lat/lon is not *real* lat/lon.... based on scale given by xarray data [90, -90] and [0, 360]
    # rather than [-90, 90] and [-180, 180]
    for x in range(len(coordarr)):
        for y in range(len(coordarr[x])):
            if coordarr[x][y][0] == lat and coordarr[x][y][1] == lon:
                return U.data[x][y]

def makeCoordArr():
    # Returns an array of (lat, lon) coord tuples with the same dimensions as the pressure data
    coordarr = []
    for x in np.array(U.lat):
        temparr = []
        for y in np.array(U.lon):
            temparr.append((x,y))
        coordarr.append(temparr)
    return np.array(coordarr)

def findLocalMinima(minPressure=980):

    # Create a 2D array of all the coordinates with pressure data 
    coordarr = makeCoordArr()

    # Set number that a derivative must be less than in order to classify as a "zero"
    bound = 0.1

    # Get global gradient of U.data
    grad = np.absolute(np.gradient(wrap_U.data))
    arr1 = grad[0]
    arr2 = grad[1]

    firstzeroes = np.argwhere(arr1<=bound)
    secondzeroes = np.argwhere(arr2<=bound)

    commonzeroes = []

    # Find zeroes of both gradient arrays
    for x in secondzeroes:
        if x in firstzeroes:
            commonzeroes.append(x)

    minimacoords = []

    # For every common zero in both gradient arrays 
    for x in commonzeroes:

        xval = x[0]
        yval = x[1]-1

        # If the gradient value is a "zero", and if the U.data value is less than minPressure
        if U.data[xval][yval] < minPressure:

            coordonmap = coordarr[xval][yval]

            # Transform data points to match globe coordinate scale
            xcoord = -1*coordonmap[0]
            ycoord = coordonmap[1]-180

            minimacoords.append((xcoord, ycoord))

    return minimacoords

###############################################################################
# Create plot

# Set figure size
fig = plt.figure(figsize=(8, 8))

# Set global axes with an orthographic projection
proj = ccrs.Orthographic(central_longitude=270, central_latitude=45)
ax = plt.axes(projection=proj)
ax.set_global()

# Add land, coastlines, and ocean features
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.COASTLINE, linewidth=.5)
ax.add_feature(cfeature.OCEAN, facecolor='lightcyan')
ax.add_feature(cfeature.BORDERS, linewidth=.5)
ax.add_feature(cfeature.LAKES, facecolor='lightcyan', edgecolor='k', linewidth=.5)

# Make array of the contour levels that will be plotted
contours = np.arange(948, 1060, 4)
contours = np.append(contours, 975)
contours = np.sort(contours)

# Plot contour data
p = wrap_U.plot.contour(ax=ax,
                        transform=ccrs.PlateCarree(),
                        linewidths=0.5,
                        levels=contours,
                        cmap='black',
                        add_labels=False)

# Specify array of contour levels to be labeled- These values were found by setting 'manual'
# argument in ax.clabel call to 'True' and then hovering mouse over desired location of
# countour label to find coordinate (which can be found in bottom left of figure window)

# low pressure contour levels- these will be plotted as a subscript to an 'L' symbol
#lowClevels = [(51.54, 169.59), (74.78, 4.54), (60.12, -57.0)]
lowClevels = findLocalMinima()

# regular pressure contour levels
clevels = [(34.63, 176.4), (42.44, -150.46), (28.5, -142.16),
           (16.32, -134.12), (17.08, -108.90), (15.60, -98.17),
           (42.19, -108.73), (49.66, -111.25), (41.93, -127.83),
           (25.64, -92.49), (29.08, -77.29), (16.42, -77.04),
           (57.59, -95.93), (84.47, -156.05), (82.52, -17.83),
           (41.99, -76.3), (41.45, -48.89), (37.55, -33.43),
           (17.17, -46.98), (63.67, 1.79), (67.05, -58.78),
           (53.68, -44.78), (53.71, -69.69), (52.22, -78.02),
           (44.33, -16.91), (35.17, -95.72), (73.62, -102.69)]

# Transform the low pressure contour coordinates from geographic to projected
lowclevelpoints = proj.transform_points(ccrs.Geodetic(), np.array([x[1] for x in lowClevels]), np.array([x[0] for x in lowClevels]))
lowClevels = [(x[0], x[1]) for x in lowclevelpoints]

# Transform the regular pressure contour coordinates from geographic to projected
clevelpoints = proj.transform_points(ccrs.Geodetic(), np.array([x[1] for x in clevels]), np.array([x[0] for x in clevels]))
clevels = [(x[0], x[1]) for x in clevelpoints]

# Label contours with Low pressure
for x in lowClevels:
    try:
        ax.clabel(p, manual=[x], inline=True, fontsize=14, colors='k', fmt="L" + "$_{%.0f}$", rightside_up=True)
    except:
        continue

# Label rest of the contours
#ax.clabel(p, manual=clevels, inline=True, fontsize=14, colors='k', fmt="%.0f")
#ax.clabel(p, manual=True, inline=True, fontsize=14, colors='k', fmt="%.2f")

# Use gvutil function to set title and subtitles
gvutil.set_titles_and_labels(ax, maintitle=r"$\bf{SLP}$"+" "+r"$\bf{1963,}$"+" "+r"$\bf{January}$"+" "+r"$\bf{24th}$", maintitlefontsize=20,
                             lefttitle="mean Daily Sea Level Pressure", lefttitlefontsize=16, righttitle="hPa", righttitlefontsize=16)

# Set characteristics of text box
props = dict(facecolor='white', edgecolor='black', alpha=0.5)

# Place text box
ax.text(0.40, -0.1, 'CONTOUR FROM 948 TO 1064 BY 4', transform=ax.transAxes, fontsize=16, bbox=props)

# Make layout tight
plt.tight_layout()

plt.show()
