# -*- coding: utf-8 -*-
"""
Created: 2019/01/23

@author: Erin Mentuch Cooper

This script can add calibration group info and data to
an exising HDF5 file or create a new HDF5 file

Example command line use:

python create_cal_hdf5.py -d 20181111 -o 21 -of cal_20181111v021.h5

or

python create_cal_hdf5.py -d 20181111 -o 21 -of 20181111v021.h5 --append


"""

import glob
import sys
import os
import os.path as op
import argparse as ap
import numpy as np
import tables as tb

from astropy.io import ascii
from astropy.io import fits
from input_utils import setup_logging


class AmpToAmp(tb.IsDescription):
    ampid = tb.StringCol(20)
    ifuslot = tb.StringCol(3)
    ifuid = tb.StringCol(3)
    specid = tb.StringCol(3)
    amp = tb.StringCol(2)
    normdata = tb.Float32Col((2, 100))


def main(argv=None):
    ''' Main Function '''
    # Call initial parser from init_utils
    parser = ap.ArgumentParser(description="""Create HDF5 Astrometry file.""",
                               add_help=True)

    parser.add_argument("-d", "--date",
                        help='''Date, e.g., 20170321, YYYYMMDD''',
                        type=str, default=None)

    parser.add_argument("-o", "--observation",
                        help='''Observation number, "00000007" or "7"''',
                        type=str, default=None)

    parser.add_argument("-tp", "--tpdir",
                        help='''Directory for Throughput Info''',
                        type=str,
                        default='/work/00115/gebhardt/maverick/detect/tp/')

    parser.add_argument("-am", "--ampdir",
                        help='''Directory for Amp to Amp''',
                        type=str,
                        default='/work/00115/gebhardt/maverick/getampnorm/all/')

    parser.add_argument('-of', '--outfilename', type=str,
                        help='''Relative or absolute path for output HDF5
                        file.''', default=None)

    parser.add_argument('-a', '--append',
                        help='''Appending to existing file.''',
                        action="count", default=0)

    args = parser.parse_args(argv)
    args.log = setup_logging()

    # Creates a new file if the "--append" option is not set or the file
    # does not already exist.

    does_exist = False
    if op.exists(args.outfilename) and args.append:
        fileh = tb.open_file(args.outfilename, 'a')
        does_exist = True
    else:
        fileh = tb.open_file(args.outfilename, 'w')

        group = fileh.create_group(fileh.root, 'Calibration',
                                   'HETDEX Calibration Info')
        groupAmpToAmp = fileh.create_group(group, 'AmpToAmp',
                                           'Amp to amp Fiber Normalization')
        groupThroughput = fileh.create_group(group, 'Throughput',
                                             'Throughput Curves')

    # populate the AmpToAmp group with normalization curves and metadata

    amptoampfiles = glob.glob(op.join(args.ampdir, 'multi*.norm'))

    for file in amptoampfiles:
        idx = file.find('multi_')
        ampid = file[idx:idx+20]
        data = ascii.read(file, names=['wave', 'norm'])
        fileh.create_table(groupAmpToAmp, str(ampid), data.as_array())

    # populate Throughput group with throughput curves

    tpfile = op.join(args.tpdir, str(args.date) + 'v' + str(args.observation.zfill(3)) + 'sedtp_f.dat')

    idx = tpfile.find('/20')
    datevshot = tpfile[idx+1:idx+13]
    tp_data = ascii.read(tpfile)
    data = tp_data['col1', 'col2', 'col3']
    data.names = ['waves', 'response', 'response_err']
    fileh.create_table(groupThroughput, datevshot, data.as_array())

    fileh.close()


if __name__ == '__main__':
    main()