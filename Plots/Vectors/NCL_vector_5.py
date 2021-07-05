"""
NCL_vector_5.py
===============
 A vector pressure/height plot

This script illustrates the following concepts:
   - Using streamplot to resemble curly vectors
   - Drawing pressure/height vectors over filled contours
   - Using inset_axes() to create additional axes for color bars
   - Interpolate to user specified pressure levels
   - Using the geocat-comp method `interp_hybrid_to_pressure <https://geocat-comp.readthedocs.io/en/latest/user_api/generated/geocat.comp.interp_hybrid_to_pressure.html#geocat.comp.interp_hybrid_to_pressure>`_
   - Using a different color scheme to follow `best practices <https://geocat-examples.readthedocs.io/en/latest/gallery/Colors/CB_Temperature.html#sphx-glr-gallery-colors-cb-temperature-py` for visualizations

See following URLs to see the reproduced NCL plot & script:
    - Original NCL script: https://www.ncl.ucar.edu/Applications/Scripts/vector_5.ncl
    - Original NCL plot: https://www.ncl.ucar.edu/Applications/Images/vector_5_lg.png
"""

###############################################################################
# Import packages:

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
from scipy.interpolate import interp2d
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import geocat.datafiles as gdf
from geocat.viz import util as gvutil
from geocat.comp import interp_hybrid_to_pressure

###############################################################################
# Read in data:
ds = xr.open_dataset(gdf.get("netcdf_files/atmos.nc"), decode_times=False)

# Define an array of surface pressures
pnew = np.arange(200, 901, 50)

# Read in variables
P0mb = 1000.
hyam = ds.hyam  # get a coefficiants
hybm = ds.hybm  # get b coefficiants
PS = ds.PS  # get pressure
PS = PS / 100  # Convert from Pascal to mb

# Read in variables from data interpolated to pressure levels
# interp_hybrid_to_pressure is the Python version of vinth2p in NCL script
T = interp_hybrid_to_pressure(data=ds.T,
                              ps=PS,
                              hyam=hyam,
                              hybm=hybm,
                              p0=P0mb,
                              new_levels=pnew,
                              method='log')
W = interp_hybrid_to_pressure(data=ds.OMEGA,
                              ps=PS,
                              hyam=hyam,
                              hybm=hybm,
                              p0=P0mb,
                              new_levels=pnew,
                              method='log')
V = interp_hybrid_to_pressure(data=ds.V,
                              ps=PS,
                              hyam=hyam,
                              hybm=hybm,
                              p0=P0mb,
                              new_levels=pnew,
                              method='log')

# Extract data
T = T.isel(time=0).sel(lon=170, method="nearest")
W = W.isel(time=0).sel(lon=170, method="nearest")
V = V.isel(time=0).sel(lon=170, method="nearest")

# Scale W
wscaler = np.mean(W)
vscaler = np.mean(V)
scale = abs(vscaler / wscaler)

wscale = W * scale

###############################################################################
# Plot:

# Generate figure (set its size (width, height) in inches)
fig = plt.figure(figsize=(10, 12))

# Generate axes using Cartopy and draw coastlines
ax = plt.axes()

# Specify which contours should be drawn
levels = np.linspace(200, 300, 11)

# # Plot contour lines
T.plot.contour(ax=ax,
               levels=levels,
               colors='black',
               linewidths=0.5,
               linestyles='solid',
               add_labels=False)

# # Plot filled contours
colors = T.plot.contourf(ax=ax,
                         levels=levels,
                         cmap='viridis',
                         add_labels=False,
                         add_colorbar=False)

# Interpolate datasets for streamplot function
# https://stackoverflow.com/questions/34711705/axis-error-in-matplotlib-pyplot-streamplot
# regularly spaced grid spanning the domain of x and y
xi = np.linspace(T['lat'].min(), T['lat'].max(), T['lat'].size)
yi = np.linspace(T['plev'].min(), T['plev'].max(), T['plev'].size)

# bicubic interpolation to fit parameter requirements for streamplot
uCi = interp2d(T['lat'], T['plev'], V.data)(xi, yi)
vCi = interp2d(T['lat'], T['plev'], wscale.data)(xi, yi)

# X = T['lat'].data
# Y = T['plev'].data
# U = V.data
# V = wscale.data

# norm = np.sqrt(U**2 + V**2)
# norm_flat = norm.flatten()

# start_points = np.array([X.flatten(), Y.flatten()]).T

# scale = .2/np.max(norm)

# for i in range(start_points.shape[0]):
#     plt.streamplot(X[i],
#                    Y[i],
#                    U[i],
#                    V[i],
#                    start_points=np.array([start_points[i,:]]),
#                    minlength=.95*norm_flat[i]*scale,
#                    maxlength=1.0*norm_flat[i]*scale,
#                    integration_direction='backward',
#                    density=10,
#                    arrowsize=0.0)

norm = np.sqrt(uCi**2 + vCi**2)

# Use streamplot to resemble curly vector
ax.streamplot(xi,
              yi,
              uCi,
              vCi,
              linewidth=0.5,
              density=10,
              arrowsize=0.7,
              arrowstyle='->',
              color='black',
              integration_direction='backward')

ax.quiver(xi, yi, uCi / norm, vCi / norm, scale=100, linewidth=0.1)

# Draw legend for vector plot
ax.add_patch(
    plt.Rectangle((53, 941),
                  35,
                  55,
                  facecolor='white',
                  edgecolor='black',
                  clip_on=False))

# Add quiverkey
# Draw translucent vector plot to be set as input for quiverkey
Q = ax.quiver(T['lat'], T['plev'], V.data, wscale.data, alpha=0, scale=400)
ax.quiverkey(Q,
             0.831,
             0.118,
             30,
             '3',
             labelpos='N',
             coordinates='figure',
             color='black',
             alpha=1,
             fontproperties={'size': 13})
ax.quiverkey(Q,
             0.831,
             0.118,
             30,
             'Reference Vector',
             labelpos='S',
             coordinates='figure',
             color='black',
             alpha=1,
             fontproperties={'size': 13})

# Use geocat.viz.util convenience function to add minor and major tick lines
gvutil.add_major_minor_ticks(ax, x_minor_per_major=3, labelsize=16)

# Use geocat.viz.util convenience function to set axes tick values
gvutil.set_axes_limits_and_ticks(ax,
                                 xlim=(-88, 88),
                                 ylim=(900, 200),
                                 xticks=np.arange(-60, 61, 30),
                                 yticks=np.array(
                                     [200, 250, 300, 400, 500, 700, 850]),
                                 xticklabels=['60S', '30S', '0', '30N', '60N'])

# Use geocat.viz.util convenience function to add titles and the pressure label
gvutil.set_titles_and_labels(ax,
                             maintitle="Pressure/Height Vector",
                             maintitlefontsize=24,
                             ylabel='Pressure (mb)',
                             labelfontsize=24)

# Create second y-axis to show geo-potential height. Currently we're using
# arbitrary values for height as we haven't figured out how to make this work
# properly yet.
axRHS = ax.twinx()

# Use geocat.viz.util convenience function to set axes tick values
gvutil.set_axes_limits_and_ticks(axRHS, ylim=(0, 13), yticks=np.array([4, 8]))

# manually set tick length, width and ticklabel size
axRHS.tick_params(labelsize=16, length=8, width=0.9)

# Use geocat.viz.util convenience function to add titles and the pressure label
axRHS.set_ylabel(ylabel='Height (km)', labelpad=10, fontsize=24)

# Force the plot to be square by setting the aspect ratio to 1
ax.set_box_aspect(1)
axRHS.set_box_aspect(1)

# Turn off minor ticks on Y axis on the left hand side
ax.tick_params(axis='y', which='minor', left=False, right=False)

# Call tight_layout function before adding the color bar to prevent user warnings
plt.tight_layout()

# Create inset axes for color bars
cax = inset_axes(ax,
                 width='97%',
                 height='8%',
                 loc='lower left',
                 bbox_to_anchor=(0.03, -0.24, 1, 1),
                 bbox_transform=ax.transAxes,
                 borderpad=0)

# Add a colorbar
cab = plt.colorbar(colors,
                   cax=cax,
                   orientation='horizontal',
                   ticks=levels[:-2:2],
                   extendrect=True,
                   drawedges=True,
                   spacing='uniform')

# Set colorbar ticklabel font size
cab.ax.xaxis.set_tick_params(length=0, labelsize=16)

# Show plot
plt.show()
