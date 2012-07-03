#!/bin/bash
#
# nohup ./nccf_oce_monthly.sh >& expid.log &
#

set -exuv
date

# expid=i00k
expid=

# lstsdates=( 19601101 19651101 19701101 19751101 19851101 )
lstsdates=(  )

# lstmemb=( 0 1 2 3 4 )
lstmemb=(  )

# lstvars=( 'iicethic' 'ileadfra' 'somxl010' 'sosaline' )
lstvars=(  )

WORKDIR=/scratch/$USER/nccf_oce_monthly_$$
mkdir -p ${WORKDIR}

cd ${WORKDIR}
for sdate in ${lstsdates[@]} ; do
  for jmemb in ${lstmemb[@]} ; do
    listfiles=`ls /cfunas/exp/ecearth/$expid/$sdate/fc$jmemb/outputs/MMO*`
    for file in ${listfiles[@]} ; do
      cp $file toto.tar
      tar -xvf toto.tar
      gunzip *.gz
      rm -f *grid_U* *grid_V* *grid_W* toto.tar
    done
    cdo cat ORCA1_*icemod.nc toto1.nc
    cdo cat ORCA1_*grid_T*.nc toto2.nc
    rm -f *grid_T*
    rm -f *icemod*
    cdo merge toto1.nc toto2.nc toto.nc
    rm -f  toto1.nc toto2.nc
    for var in ${lstvars[@]} ; do
      cdo selvar,$var toto.nc tmp.nc 

    cat > scrip_use_in <<EOF1
&remap_inputs
    remap_wgt   = 'weigths/rmp_ORCA1t_to_HadISST_conserv.nc'
    infile      = 'tmp.nc'
    invertlat   = FALSE
    var         = '${var}'
    fromregular = FALSE
    outfile     = '${var}_${expid}_${jmemb}_${sdate}.nc'
/
EOF1
      ln -sf /cfu/pub/scripts/interpolation/scrip_use .
      ln -sf /cfu/pub/scripts/interpolation/weigths .

      ./scrip_use
      rm -f tmp.nc
    done
    rm -f toto.nc
  done
  for var in ${lstvars[@]} ; do
    ncecat -h -v ${var} ${var}_${expid}_*_${sdate}.nc ${var}_${expid}_${sdate}.nc
    ncrename -h -O -d y,latitude -d x,longitude ${var}_${expid}_${sdate}.nc
    ncks -h -A /home/vguemas/tools/lonlat_hadisst.nc ${var}_${expid}_${sdate}.nc
    rm -f ${var}_${expid}_*_${sdate}.nc 
    case $var in 
      'iicethic') varout=sit ;;
      'ileadfra') varout=sic ;;
      'somxl010') varout=mld ;; 
      'sosaline') varout=sss ;;
    esac
    ncrename -h -O -v $var,$varout ${var}_${expid}_${sdate}.nc
    ncrename -h -O -d record,ensemble ${var}_${expid}_${sdate}.nc 
    ncpdq -O -h -a time,ensemble ${var}_${expid}_${sdate}.nc ${var}_${expid}_${sdate}.nc
    mkdir -p /cfunas/exp/ecearth/$expid/monthly_mean/${varout}
    mv ${var}_${expid}_${sdate}.nc /cfunas/exp/ecearth/$expid/monthly_mean/${varout}/${varout}_${sdate}.nc
  done
done

rm -rf ${WORKDIR}
date
