#
#
# Generate the HDF5 sensitivity cubes from
# the flux limit FITs files. Also compute
# the averages across a shot
#
# Daniel Farrow (MPE)
#

# Script to compute averages
AV_FLIM_SCRIPT=/home/04120/dfarrow/HETDEX_API/compute_average_flux_limit.py 

INPATH=/work/04120/dfarrow/wrangler/flims/hdr1_fits_cubes
OUTPATH=/work/04120/dfarrow/wrangler/flims/hdr1

# File in to which to write the biweight location of the flux limits at 4540AA for each shot
AVERAGE_FLIM_FILE=/work/04120/dfarrow/wrangler/flims/hdr1/average_flims.txt

for fpath in `ls -d ${INPATH}/20*v*`
do
    datevobs=`basename ${fpath}`
    echo $datevobs
    pushd $fpath
    cd flim
    python $AV_FLIM_SCRIPT --fout "${outfolder}_ifu_flims.txt" --fn-shot-average $AVERAGE_FLIM_FILE *.fits
    add_sensitivity_cube_to_hdf5 *_3d.fits "${OUTPATH}/${datevobs}_sensitivity_cube.h5"
    popd
done
