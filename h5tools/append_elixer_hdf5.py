# -*- coding: utf-8 -*-
"""
Script to append elixer values to a detect h5 file
 takes a detect h5 path as input

>>> python3 append_elixer.hdf5 detect_hdr2.1_copy.h5

"""
import sys
import numpy as np
from hetdex_api.config import HDRconfig
import tables as tb
from astropy.table import Table


class Elixer(tb.IsDescription):
    detectid = tb.Int64Col(pos=0)
    mag_sdss_g = tb.Float32Col()
    mag_sdss_g_err = tb.Float32Col()
    plae_sdss_g = tb.Float32Col()
    plae_sdss_g_max = tb.Float32Col()
    plae_sdss_g_min = tb.Float32Col()
    #ELiXer combined (rules, inv variance, weights and Bayes) classification info
    combined_plae = tb.Float32Col()
    combined_plae_err = tb.Float32Col()
    plae_classification = tb.Float32Col()
    combined_continuum = tb.Float32Col()
    combined_continuum_err = tb.Float32Col()
                                        
detecth5 = sys.argv[1]
    
config = HDRconfig('hdr2.1')

filedet = tb.open_file(detecth5 , 'a')

fileelix = tb.open_file(config.elixerh5, 'r')

detectid = filedet.root.Detections.cols.detectid[:]

elix_table = Table(fileelix.root.Detections.read())

try:
    filedet.remove_node(filedet.root.Elixer, recursive=True)
except:
    pass
    
tableElixer = filedet.create_table(filedet.root, "Elixer", Elixer, "Elixer Info")

for detid in detectid:
    row = tableElixer.row

    sel_det = elix_table['detectid'] == detid

    if np.sum(sel_det) == 1:
        for col in Elixer().columns:
            row[col] = elix_table[col][sel_det]
        row.append()
    elif np.sum(sel_det) == 0:
        row.append()
        print('No elixer match for %s' % detid)
    else:
        row.append()
        print('More than 1 elixer match for %s' % detid)

tableElixer.flush()
tableElixer.cols.detectid.create_csindex()

fileelix.close()
filedet.close()
