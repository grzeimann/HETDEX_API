# -*- coding: utf-8 -*-
"""
Created on March 29 2019
@author: Erin Mentuch Cooper

Extracts 2D CCD image for a given RA/DEC/WAVE/SHOTID or for a specific detectid

Example
-------
python3 get_spec2D.py -dets hdr1_sngt6pt5_for.tab -dx 32 -dy 9 --h5file -s
20190208035

"""

from __future__ import print_function

import sys
import glob

import os
import tables as tb
import argparse as ap
import os.path as op
import numpy as np

from astropy.io import ascii
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from astropy.visualization import ZScaleInterval

from input_utils import setup_logging
from hetdex_api.shot import Fibers
from hetdex_api.detections import Detections

matplotlib.use("agg")
#sys.path.append('/work/03261/polonius/hetdex/science/sciscripts/elixer.test')
sys.path.append('/work/03261/polonius/hetdex/science/sciscripts/elixer') 
import catalogs


def get_2Dimage(detectid_obj, detects, fibers, width=100, height=50):

    fiber_table = Table(
        detects.hdfile.root.Fibers.read_where("detectid == detectid_obj")
    )

    fsort = fiber_table.argsort(keys="weight", reverse=True)

    fiber_table = fiber_table[fsort]

    weight_total = np.sum(fiber_table["weight"])

    # open blank image to store summed image and 4 brightest fibers
    im_sum = np.zeros((height, width))

    for fiber_i in fiber_table:
        wave_obj = fiber_i["wavein"]
        multiframe_obj = fiber_i["multiframe"]
        expnum_obj = fiber_i["expnum"]
        fibnum_obj = fiber_i["fibnum"]
        weight = fiber_i["weight"] / weight_total
        im_fib = fibers.get_fib_image2D(
            wave_obj, fibnum_obj, multiframe_obj, expnum_obj, width=width, height=height
        )
        im_sum += weight * im_fib

    return im_sum


def get_2Dimage_array(detectid_obj, detects, fibers, width=100, height=50):

    fiber_table = Table(
        detects.hdfile.root.Fibers.read_where("detectid == detectid_obj")
    )

    fsort = fiber_table.argsort(keys="weight", reverse=True)

    fiber_table = fiber_table[fsort]

    weight_total = np.sum(fiber_table["weight"])

    im_arr = np.zeros((4, height, width))

    for i, fiber_i in enumerate(fiber_table[0:4]):
        wave_obj = fiber_i["wavein"]
        multiframe_obj = fiber_i["multiframe"]
        expnum_obj = fiber_i["expnum"]
        fibnum_obj = fiber_i["fibnum"]
        weight = fiber_i["weight"] / weight_total
        im_fib = fibers.get_fib_image2D(
            wave_obj, fibnum_obj, multiframe_obj, expnum_obj,
            width=width, height=height
        )
        im_arr[i] = im_fib

    return im_arr, fiber_table


def get_2Dimage_wave(detectid_obj, detects, fibers, width=100, height=50):
    fiber_table = Table(
        detects.hdfile.root.Fibers.read_where("detectid == detectid_obj"))
    maxfib = np.argmax(fiber_table["weight"])
    wave_obj = fiber_table["wavein"][maxfib]
    multiframe_obj = fiber_table["multiframe"][maxfib]
    expnum_obj = fiber_table["expnum"][maxfib]
    fibnum_obj = fiber_table["fibnum"][maxfib]
    idx = np.where(
        (fibers.fibidx == (fibnum_obj - 1))
        * (fibers.multiframe == multiframe_obj)
        * (fibers.expnum == expnum_obj)
    )[0][0]
    im_fib = fibers.wavelength[idx]

    sel = np.where(im_fib >= wave_obj)[0][0]
    x1 = np.maximum(0, sel - int(width / 2))
    x2 = np.minimum(1032, sel + int(width / 2) + (width % 2))

    x1_slice = np.minimum(0, width - (x2 - x1))
    x2_slice = x2 - x1

    im_wave = np.zeros(width)
    im_wave[x1_slice:x2_slice] = im_fib[x1:x2]

    return im_wave


def save_2Dimage(detectid_i, detects, fibers, width=100, height=20, path=os.getcwd()):
    # try:
    im_sum = get_2Dimage(detectid_i, detects, fibers, width=width, height=height)
    im_wave = get_2Dimage_wave(detectid_i, detects, fibers, width=width, height=height)
    im_out = np.vstack([im_wave, im_sum])
    zscale = ZScaleInterval(contrast=0.5, krej=2.5)
    vmin, vmax = zscale.get_limits(values=im_out)
    plt.imshow(
        im_out[1:-1, :],
        vmin=vmin,
        vmax=vmax,
        extent=[im_out[0, 0], im_out[0, -1], -int(height / 2.0), int(height / 2.0)],
        origin="lower",
        cmap=plt.get_cmap("gray"),
        interpolation="none",
    )
    plt.savefig(op.join(path, "imsum2D_" + str(detectid_i) + ".png"))
    np.savetxt(op.join(path, "imsum2D_" + str(detectid_i) + ".txt"), im_out)
    # except:
    #   print("failed to create sum, dims prob don't match")
    return im_out


def get_parser():
    """ Function that returns a parser"""

    parser = ap.ArgumentParser(
        description="""Create fiber cutout for a given position or detectid""",
        add_help=True
    )

    parser.add_argument(
        "-s",
        "--datevobs",
        help="""ShotID, e.g., 20170321v009, YYYYMMDDvOBS""",
        type=str,
        default=None,
    )

    parser.add_argument(
        "-dets", "--dets", help="""filelist of detectids""", default=None
    )

    parser.add_argument(
        "-ra",
        "--ra",
        help="""ra, e.g., right ascension in degrees""",
        type=float,
        default=None,
    )

    parser.add_argument(
        "-dec",
        "--dec",
        help="""ra, e.g., right ascension in degrees""",
        type=float,
        default=None,
    )

    parser.add_argument(
        "-rad",
        "--rad",
        help="""radius, e.g., aperture radius in arcsec""",
        type=float,
        default=3.0,
    )

    parser.add_argument(
        "-w", "--wave", help="""wavelength in AA""", type=float, default=None
    )

    parser.add_argument(
        "-dw", "--dwave", help="""delta wavelength in AA""", type=float, default=50.0
    )

    parser.add_argument(
        "-dx", "--width", type=int, help="""Width of image in wavelength dim in pix"""
    )

    parser.add_argument(
        "-dy", "--height", type=int, help="""Height of fiber image in pixels"""
    )

    parser.add_argument(
        "-p", "--path", help="""Path to save output""", default=os.getcwd(), type=str
    )

    parser.add_argument(
        "-i", "--infile", help="""File with table of ID/RA/DEC""", default=None
    )

    parser.add_argument(
        "-h5",
        "--h5file",
        help="""Store output in an h5 file called SHOTID.h5""",
        required=False,
        action="store_true",
    )

    parser.add_argument(
        "--merge",
        action="store_true",
        required=False,
        help="""Trigger to merge all im2D_SHOTID.h5 files after slurm job""",
    )
    return parser


def main(argv=None):
    """ Main Function """

    parser = get_parser()
    args = parser.parse_args(argv)
    args.log = setup_logging()

    print(args)

    class Image2D(tb.IsDescription):
        detectid = tb.Int64Col(pos=0)
        im_wave = tb.Float32Col(args.width, pos=1)
        im_sum = tb.Float32Col((args.height, args.width), pos=2)
        im_array = tb.Float32Col((4, args.height, args.width), pos=3)
        im_phot = tb.Float32Col((60, 60), pos=4)
        im_phot_hdr = tb.StringCol(2880)
        spec1D = tb.Float32Col((1036,))
        spec1D_err = tb.Float32Col((1036,))

    if args.merge:
        fileh = tb.open_file("merged_im2D.h5", "w")
        im2D_table = fileh.create_table(fileh.root, "Images", Image2D)

        files = sorted(glob.glob("im2D*.h5"))
        for file in files:
            fileh_i = tb.open_file(file, "r")
            im2D_table_i = fileh_i.root.Images.read()

            im2D_table.append(im2D_table_i)

            fileh_i.close()

        im2D_table.flush()
        fileh.close()
        sys.exit("Merged h5 files in current directory. Exiting")

    shotid_i = args.datevobs

    detects = Detections("hdr1", loadtable=False)

    # open up catalog library from elixer
    catlib = catalogs.CatalogLibrary()
    print("opening shot: " + str(shotid_i))
    fibers = Fibers(args.datevobs)

    if args.infile:
        try:
            catalog = Table.read(args.infile, format=ascii)
        except:
            catalog = Table.read(
                "/work/05350/ecooper/hdr1/catalogs/hdr1_sngt6pt5_for.tab",
                format="ascii",
            )

        selcat = catalog["shotid"] == int(shotid_i)
        detectlist = np.array(catalog["detectid"][selcat])

    elif args.dets:
        try:
            catalog = Table.read(args.dets, format="ascii")
            selcat = catalog["shotid"] == int(shotid_i)
            detectlist = np.array(catalog["detectid"][selcat])
        except:
            detectlist = np.loadtxt(args.dets, dtype=int)

    if args.h5file:

        fileh = tb.open_file("im2D_" + str(args.datevobs) + ".h5", "w")

        im2D_table = fileh.create_table(fileh.root, "Images", Image2D)

        for detectid_i in detectlist:
            print(detectid_i)
            # add data to HDF5 file
            row = im2D_table.row
            row["detectid"] = detectid_i
            row["im_wave"] = get_2Dimage_wave(
                detectid_i, detects, fibers, width=args.width, height=args.height
            )
            row["im_sum"] = get_2Dimage(
                detectid_i, detects, fibers, width=args.width, height=args.height
            )
            im_arr, fiber_table = get_2Dimage_array(
                detectid_i, detects, fibers, width=args.width, height=args.height
            )
            row["im_array"] = im_arr

            spec_tab = detects.get_spectrum(detectid_i)
            row["spec1D"] = spec_tab['spec1d']
            row["spec1D_err"] = spec_tab['spec1d_err']

            # add in phot image, need RA/DEC from catalog
            sel_det = detects.detectid == detectid_i
            coord = detects.coords[sel_det]

            try:
                cutout = catlib.get_cutouts(position=coord,
                                            radius=5,
                                            aperture=None,
                                            dynamic=False,
                                            filter='r')[0]
                if cutout['instrument'] == 'HSC':
                    row["im_phot"] = cutout['cutout'].data
                    header = cutout['cutout'].wcs.to_header()
                    row['im_phot_hdr'] = header.tostring()
            except IndexError:
                print('No imaging available for source')

            row.append()

        im2D_table.flush()
        
        fileh.close()

    else:
        for detectid_i in detectlist:
            print(detectid_i)
            save_2Dimage(
                detectid_i,
                detects,
                fibers,
                width=args.width,
                height=args.height,
                path=args.path,
            )

    if args.ra and args.dec:
        # NOTE this has not been updated yet.. will build functionality soon
        obj_coords = SkyCoord(args.ra * u.deg, args.dec * u.deg, frame="icrs")
        idx = fibers.query_region_idx(obj_coords, radius=(args.rad / 3600.0))

        output = Table()
        output["ra"] = fibers.coords.ra[idx] * u.deg
        output["dec"] = fibers.coords.dec[idx] * u.deg
        filenames = []

        fileidx = 101
        for i in idx:
            filename = "tmp" + str(fileidx) + ".dat"
            filenames.append(filename)
            save_rsp_spectrum(
                fibers, i, file=filename,
            )
            fileidx += 1

        output["filename"] = np.array(filenames)
        ascii.write(output, "fib_coords.dat", overwrite=True)

    fibers.close()

tb.file._open_files.close_all()

if __name__ == "__main__":
    main()
