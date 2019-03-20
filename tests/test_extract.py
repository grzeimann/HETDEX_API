#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 12:05:39 2019

@author: gregz
"""

from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy import units as u
# Plotting tool
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, RangeTool, PrintfTickFormatter
from bokeh.plotting import figure, save, output_file
from bokeh.palettes import Greys as palette
# Import Extract class
from hetdex_api.extract import Extract
import numpy as np

palette.reverse()

def make_plot(name, wavelength, spec_list, color_list, label_list, image):
    plot = figure(plot_height=300, plot_width=800,
               toolbar_location=None, x_axis_location="above",
               background_fill_color="#efefef", x_range=(3470., 5540.),
               y_axis_type="linear", y_range=(1., 10**5))

    imageplot = figure(plot_height=500, plot_width=500,
                       tools="crosshair, pan, reset, save, wheel_zoom",
                       y_axis_location="right",
                       tooltips=[("x", "$x"), ("y", "$y"),
                                 ("value", "@image")])

    select = figure(title=("Drag the selection "
                           "box to change the range above"),
                    plot_height=130, plot_width=800, y_range=plot.y_range,
                    y_axis_type="linear",
                    tools="", toolbar_location=None,
                    background_fill_color="#efefef")
    for spectrum, color, label in zip(spec_list, color_list, label_list):               
        source = ColumnDataSource(data=dict(wavelength=wavelength, 
                                            spectrum=spectrum))
        plot.line('wavelength', 'spectrum', source=source, line_width=3,
                  line_alpha=0.6, line_color=color,
                  legend=label)
        select.line('wavelength', 'spectrum', source=source,
                    line_color=color)

    plot.xaxis.major_label_text_font_size = "16pt"
    plot.yaxis.major_label_text_font_size = "16pt"
    plot.xaxis.axis_label = 'Wavelength'
    plot.xaxis.axis_label_text_font_size = "20pt"
    plot.yaxis.axis_label = r'$10^{-17}$ ergs / s / $cm^{2}$ / $\AA$'
    plot.yaxis.axis_label_text_font_size = "20pt"
    plot.xaxis.major_tick_line_color = "firebrick"
    plot.xaxis.major_tick_line_width = 3
    plot.xaxis.minor_tick_line_color = "orange"
    plot.yaxis.major_tick_line_color = "firebrick"
    plot.yaxis.major_tick_line_width = 3
    plot.yaxis.minor_tick_line_color = "orange"
    plot.yaxis[0].formatter = PrintfTickFormatter(format="%3.2f")
    select.ygrid.grid_line_color = None
    range_tool = RangeTool(x_range=plot.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.add_tools(range_tool)
    select.toolbar.active_multi = range_tool
    imageplot.image(image=[image[0]], x=image[1].min(), y=image[2].min(),
                    dw=image[1].max()-image[1].min(),
                    dh=image[2].max()-image[2].min(), palette=palette)
    output_file(name+".html", title=name)
    save(row(column(plot, select), imageplot))

# Initiate class
E = Extract()

# Load a given shot
E.load_shot('20190208v025')
RA = E.fibers.hdfile.root.Shot.cols.ra[:][0]
Dec = E.fibers.hdfile.root.Shot.cols.dec[:][0]

# Get SDSS spectra in the field
# pip install --user astroquery
from astroquery.sdss import SDSS
from astropy import coordinates as coords
pos = coords.SkyCoord(RA * u.deg, Dec * u.deg, frame='fk5')
xid = SDSS.query_region(pos, radius=11*u.arcmin, spectro=True)
ra, dec = xid['ra'], xid['dec']
sp = SDSS.get_spectra(matches=xid)

# Build aperture PSF for aperture extraction
fixed_aperture = 3.
aperture = E.tophat_psf(fixed_aperture, 10.5, 0.25)

# Get curve of growth from VIRUS PSF for the given loaded shot
psf = E.model_psf(gmag_limit=22.)
r, curve_of_growth = E.get_psf_curve_of_growth(psf)
correction = 1. / np.interp(fixed_aperture, r, curve_of_growth)
E.log.info('PSF correction for radius, %0.1f", is: %0.2f' % (3., correction))

coords = SkyCoord(ra * u.deg, dec * u.deg)
L = []
for coord, S in zip(coords, sp):
    coord_str = coord.to_string(style='hmsdms')
    E.log.info('Working on coordinate: %s' % coord_str)
    info_result = E.get_fiberinfo_for_coord(coord, radius=5.)
    if info_result is None:
        continue
    E.log.info('Found fibers for coordinate: %s' %
               coord.to_string(style='hmsdms'))
    ifux, ifuy, xc, yc, ra, dec, data, error, mask = info_result
    # Re-centroid? If so, do it here before building aperture (i.e., change xc, yc)
    image = E.make_collapsed_image(xc, yc, ifux, ifuy, data, mask,
                                   scale=0.25, seeing_fac=1.5, boxsize=10.75,
                                   wrange=[4900, 5300], nchunks=3,
                                   convolve_image=True)
    weights = E.build_weights(xc, yc, ifux, ifuy, aperture)
    result = E.get_spectrum(data, error, mask, weights)
    spectrum, spectrum_error = [res*correction for res in result]
    sdssspec = np.interp(E.wave, 10**(S[1].data['loglam']), S[1].data['flux'])
    make_plot(coord_str, E.wave, [spectrum, sdssspec],
              ['SteelBlue', 'Crimson'], ['VIRUS', 'SDSS'], image)