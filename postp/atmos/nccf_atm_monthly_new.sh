#!/bin/bash
#
# nohup ./nccf_atm_monthly.sh expid startdate >& expid-startdate.log &
#
#
# This script will extract variabls from EC-Earth monthly atmospheric output 
# which is available in MMA files, save each variable in one file and also
# combine members together. It will modify the header informaton of the
# generated files according to CMIP5 standard and the variable names will be
# modified according PCMDI standard variable names.
#
# Written by Hui Du
#
# Institut Català de Ciències del Clima / Climate Forecasting Unit (IC3/CFU)
# Created:  February 22, 2010

set -xv

##################################
####  User Defined Variables  #### 
##################################

INSTITUTION="IC3            "
SOURCE="EC-Earth2.3.0" # loaded from database (max length 60 char's) 
VAR_LST="T2M D2M U10M V10M PRECIP CP E SF SST MSL SSR STR SLHF SSHF SSRD SSRU SSRC STRD STRU TSR TSRC TTRC TTR TCC"
#VAR_LST="T U V W Q CL CIWC CILC"

LEVEL_LST="92500,85000,70000,60000,50000,20000,10000,5000,1000"
MEM_LST=( fc0 )
ENSEMBLE=${#MEM_LST[@]}
DATADIR=/cfunas/exp/ecearth                    # where MMA files located
SAVEDIR=/cfunas/exp/ecearth                    # for Saving outputs 
HEAD_DIR=/cfu/pub/scripts/postp_ecearth/header # some of the header information
WORKDIR=/scratch/tmp/$USER/nccf_atm_monthly_$$     # working dir
NFRP=3 # ecearth output frequency (hours), this is for computing the accumulated precipitation 
       # and flux variables (solar and thermal radiation, sensible and latent fluxes)
FACTOR=$((NFRP*3600)) # 3600 (seconds per hour)
#####  End of User Defined Dariables  ####


#################################
####  User Defined Funtions  #### 
#################################

# check if args are ok
function check_args(){
 if [ $# -ne 2 ]; then
  echo
  echo "USAGE: $(basename $0) <exp_id> <startdate> "
  echo "For example: b014 19601101 "
  echo
  exit 1
 fi
}

get_args(){
while getopts e:d:t:l:g: option
do
  case $option in
    e) EXPID=$OPTARG;;
    d) DATA=$OPTARG;;
    t) TYPE=$OPTARG;;
    l) LATMAX=$OPTARG;;
    g) IFGLOBAL=$OPTARG;;
    \?) exit 1;;
  esac
done
}

function get_leadtime(){
 cd ${DATADIR}/${expid}/${sdate}/fc0/outputs # hard coded
 nfile=`ls MMA*|wc -l`
 tmpfile=`ls MMA*|head -1`
 nmonth=`tar tvf $tmpfile |grep GG|wc -l`
 NLT=$((nfile*nmonth))
 cd ${WORKDIR}
}

function trim_zero(){
 echo $1 | sed 's/^0*//;s/^$/0/'
}

# fucntion leadtime2date, based on starting date and lead time to calculate date(year &  month) of the corresponding leadtime
function leadtime2date(){
 inidate=$1
 offset=$2

 yy=`echo $inidate|cut -c1-4`
 mm=`echo $inidate|cut -c5-6`
 mm=`trim_zero $mm`
 yy1=$((yy+offset/12))

 nmonth=$((offset%12))
 mm1=$((mm+nmonth))
 if [ $mm1 -gt 12 ]; then
  yy1=$((yy1+1))
  mm1=$((mm1-12))
 fi

 if [ $mm1 -lt 10 ]; then
  mm1="0$mm1"
 fi
 echo $yy1$mm1
}

# get the total number of hours for a specific month
function get_hours(){
 yymm=$1
 year=`echo $yymm|cut -c1-4`
 month=`echo $yymm|cut -c5-6`
 ndays=$(cal $month $year |egrep "^[ 0-9][0-9]| [ 0-9][0-9]$" |wc -w)
 hours=$((ndays*24))
 echo $hours
}

# function to get reftime time
function rtime(){
 date1=$1
 date2=$2
 factor=day # h for hour, d for days
 year1=`echo $date1|cut -c1-4`
 month1=`echo $date1|cut -c5-6`
 day1=`echo $date1|cut -c7-8`
 year2=`echo $date2|cut -c1-4`
 month2=`echo $date2|cut -c5-6`
 day2=`echo $date2|cut -c7-8`
 sec1=`date --utc --date "${year1}-${month1}-${day1}" +%s`
 sec2=`date --utc --date "${year2}-${month2}-${day2}" +%s`
 case $factor in 
  hour)
  factor=3600 # 60*60
  ;;
  day)
  factor=86400 # 60*60*24
  ;;
 esac
 reftime_value=$(((sec2-sec1)/factor))
}

function header(){
 sd=$1
 echo $sd
 rtime 19500101 ${sd}
 ncks -h -d ensemble,0,$((ENSEMBLE-1)),1 ${HEAD_DIR}/template.nc toto.nc # select sub member
 cp toto.nc toto1.nc
 time_bnd1=0
 time_bnd2=`get_hours $sd`
 leadtime=$(((time_bnd1+time_bnd2)/2))

 ncap2 -O -h -s "leadtime(0)=${leadtime};time_bnd(,0)=${time_bnd1};time_bnd(,1)=${time_bnd2}" toto.nc toto.nc

 for ((i=1;i<=$((NLT-1));i++)); do
  fordate=`leadtime2date $sd $i`
  echo $sd $i $fordate
  interval=`get_hours $fordate`
  time_bnd1=$time_bnd2
  time_bnd2=$((time_bnd1+interval))
  leadtime=$(((time_bnd1+time_bnd2)/2))
  echo $fordate $interval $time_bnd1 $time_bnd2
  ncap2 -O -h -s "reftime(0)=${reftime_value};leadtime(0)=${leadtime};time_bnd(,0)=${time_bnd1};time_bnd(,1)=${time_bnd2}" toto1.nc toto1.nc
  ncrcat -O -h toto.nc toto1.nc toto.nc
 done

 mv toto.nc header.nc; rm toto1.nc

 ncap2 -O -h -s "reftime(0)=reftime(1)" header.nc header.nc
}

# function to modify level information 
modify_level(){
 ncatted -O -h -a standard_name,level_$2,o,c,"height" $1       # standard name
 ncatted -O -h -a long_name,level_$2,o,c,"reference height" $1 # long name
 ncatted -O -h -a data_type,level_$2,o,c,"float" $1            # data type
 ncatted -O -h -a units,level_$2,o,c,"m" $1                    # units
 ncatted -O -h -a axis,level_$2,o,c,"Z" $1                     # axis
 ncatted -O -h -a positive,level_$2,o,c,"up" $1         
}

# function to changing part of the header information 
correct_time(){
 ncap2 -O -h -s "time()=(time()+720)" $1 $1
 ncatted -O -h -a units,time,m,c,"hours since $sdate-$MM-$DD 00:00:00" $1
}

leadtime(){
 for ((i=0;i<=$((nt-2));i++)); do
  ncap2 -O -h -s "leadtime($i)=(time($i)+(time($((i+1)))-time($i))/2);time_bnd($i,0)=time($i);time_bnd($i,1)=time($((i+1)))" $1 $1
 done
 ncap2 -O -h -s "leadtime($((nt-1)))=((leadtime($((nt-2)))+744));time_bnd($((nt-1)),0)=time($((nt-1)));time_bnd($((nt-1)),1)=(time($((nt-1)))+744)" $1 $1
}

# delete the variable time
delete_time(){
 ncrename -O -h -v time,kaka $1
 ncks -O -h -x -v kaka $1 $1
}

delete_var(){
 ncrename -O -h -v $2,kaka $1
 ncks -O -h -x -v kaka $1 $1
}

new_name(){
      case $1 in # rename variable names in model output to the standard names which should be used in post-processed files 
        "T2M")
        varnew=tas
        idx=1
        ;;
        "D2M")
        varnew=d2m
        idx=25
        ;;
        "U10M")
        varnew=uas
        idx=15
        ;;
        "V10M")
        varnew=vas
        idx=16
        ;;
        "PRECIP")
        varnew=prlr
        idx=7
        ;;
        "CP")
        varnew=prc
        idx=26
        ;;
        "SF")
        varnew=prsn
        idx=27
        ;;
        "E")
        varnew=evspsbl
        idx=28
        ;;
        "SST")
        VAR=SSTK
        varnew=tos
        idx=10
        ;;
        "MSL")
        varnew=psl
        idx=2
        ;;
        "SSR")
        varnew=rss
        idx=5
        ;;
        "SSRU")
        varnew=rsus
        idx=30
        ;;
        "SSRC")
        varnew=rsscs
        idx=29
        ;;
        "TSR")
        varnew=rst
        idx=21
        ;;
        "TSRC")
        varnew=rstcs
        idx=22
        ;;
        "TTR")
        varnew=rlt
        idx=23
        ;;
        "TTRC")
        varnew=rltcs
        idx=24
        ;;
        "STR")
        varnew=rls
        idx=6
        ;;
        "STRD")
        varnew=rlds
        idx=31
        ;;
        "STRU")
        varnew=rlus
        idx=32
        ;;
        "SLHF")
        varnew=hflsd
        idx=9
        ;;
        "SSHF")
        varnew=hfssd
        idx=8
        ;;
        "SSRD")
        varnew=rsds
        idx=20
        ;;
        "T")
        varnew=ta
        idx=11
        ;;
        "U")
        varnew=ua
        idx=12
        ;;
        "V")
        varnew=va
        idx=13
        ;;
        "W")
        varnew=wap
        idx=34
        ;;
        "CL")
        varnew=cl
        idx=35
        ;;
        "CLWC")
        varnew=clw
        idx=36
        ;;
        "CIWC")
        varnew=cli 
        idx=37
        ;;
        "Z")
        varnew=g
        idx=14
        ;;
        "Q")
        varnew=hus
        idx=19
        ;;
        "tasmax")
        varnew=tasmax
        idx=17
        ;;
        "tasmin")
        varnew=tasmin
        idx=18
        ;;
        "TCC")
        varnew=clt
        idx=33
        ;;
      esac
}

# for surface variables (manipulate GG files)
function surface(){
echo ${MEM_LST[@]}
for mem in ${MEM_LST[@]}; do
    
##### untar and unzip MMA files #####
  path_to_search=${base_path}/$mem/outputs
  cp $path_to_search/MMA*.tar . 
  file_list=`ls MMA*.tar`
  echo ${file_list}
  for f in ${file_list};do
    echo "FILE: $f -> ${file_list}"
    tar xvf $f; rm *SH*.gz; gunzip -q *.gz
    rm $f
  done

  files=`ls MMA*GG*.nc` 

####  process each variable  ####
 for VAR in ${VAR_LST_2D[@]}; do # untar once and extract all the variables
	new_name $VAR	
      case $VAR in
        "PRECIP") # for precip, have to add CP and LSP to get total precip
	      varnew=prlr
          for f in ${files}; do
            suffix=$mem.$f
            cdo selname,CP $f CP.$suffix # select CP
            ncrename -h -v CP,prlr CP.$suffix 
            cdo selname,LSP $f LSP.$suffix # select LSP       
            ncrename -h -v LSP,prlr LSP.$suffix
            cdo add CP.$suffix LSP.$suffix ${varnew}.${suffix} # add CP and LSP to get total precipitation 
            cdo divc,${FACTOR} ${varnew}.${suffix} toto.nc;rm ${varnew}.${suffix}; mv toto.nc ${varnew}.${suffix}
          done
          prlr_files=`ls ${varnew}*`
          cdo copy ${prlr_files} tmp_${varnew}_$sdate.$mem.nc # combine all the time steps in one file
          rm -r prlr*.nc CP* LSP*
        ;;
        "SSRU")
          varnew=rsus
          for f in ${files}; do
            suffix=$mem.$f
            cdo selname,SSRD $f SSRD.$suffix 
            ncrename -h -v SSRD,rsus SSRD.$suffix
            cdo selname,SSR $f SSR.$suffix        
            ncrename -h -v SSR,rsus SSR.$suffix
            cdo sub SSR.$suffix SSRD.$suffix ${varnew}.${suffix}   
            cdo divc,${FACTOR} ${varnew}.${suffix} toto.nc;rm ${varnew}.${suffix}; mv toto.nc ${varnew}.${suffix}
          done
          rsus_files=`ls ${varnew}*`
          cdo copy ${rsus_files} tmp_${varnew}_$sdate.$mem.nc # combine all the time steps in one file
          rm -r rsus*.nc SSR* SSRD*
        ;;
        "STRU")
          varnew=rlus
          for f in ${files}; do
            suffix=$mem.$f
            cdo selname,STRD $f STRD.$suffix 
            ncrename -h -v STRD,rlus STRD.$suffix
            cdo selname,STR $f STR.$suffix                   
            ncrename -h -v STR,rlus STR.$suffix
            cdo sub STR.$suffix STRD.$suffix ${varnew}.${suffix}   
            cdo divc,${FACTOR} ${varnew}.${suffix} toto.nc;rm ${varnew}.${suffix}; mv toto.nc ${varnew}.${suffix}
          done
          rsus_files=`ls ${varnew}*`
          cdo copy ${rsus_files} tmp_${varnew}_$sdate.$mem.nc # combine all the time steps in one file
          rm -r rlus*.nc STR* STRD*
        ;;
        *)  
	      new_name $VAR       
          for f in ${files};do
            cdo selname,${VAR} ${f} ${VAR}.$mem.$f
          done
          tmp_files=`ls ${VAR}*.nc`
          tmp_out=tmp_${varnew}_$sdate.$mem.nc
          cdo copy ${tmp_files} ${tmp_out} # combine all the time steps in one file
          ncrename -v ${VAR},${varnew} ${tmp_out}
          case ${varnew} in
            "rss"|"rls"|"rsscs"|"rsds"|"rlds"|"hflsd"|"hfssd"|"rlt"|"rst"|"rltcs"|"rstcs")
            cdo divc,${FACTOR} ${tmp_out} toto.nc; rm ${tmp_out};mv toto.nc ${tmp_out}
            ncatted -O -a units,${varnew},m,c,"W m-2" ${tmp_out}
            ;;
          esac
          rm ${tmp_files}
        ;;
      esac
  done # loop for VAR
  rm ${files}
done # loop for members 

# finish selecting the varialbes 
# combine memebers and change the attributes
 for VAR in ${VAR_LST[@]}; do 
    new_name $VAR
   	output=${varnew}_$sdate.nc
   	ncecat tmp_${varnew}_$sdate.*.nc ${output} # Combine all members in one file by add one more dimension 
   	rm tmp_${varnew}_$sdate.*

##### Change the header informations #####
#
# Get the CFU standard attributes to be written in the variable
#
   	variables=`cat ${HEAD_DIR}/table_of_variable | cut -f$idx -d'|' | sed -e 's/ /@/g'`
  	cfustandard_name=`echo $variables | cut -f2 -d' ' | sed -e 's/@/ /g'`  # variable standard name
   	cfulong_name=`echo $variables     | cut -f3 -d' ' | sed -e 's/@/ /g'`  # variable long name
   	cfucell_methods=`echo $variables  | cut -f4 -d' ' | sed -e 's/@/ /g'`  # variable cell methods
   	cfuunit=`echo $variables          | cut -f5 -d' ' | sed -e 's/@/ /g'`  # variable unit
   	cfuunit_long=`echo $variables     | cut -f6 -d' ' | sed -e 's/@/ /g'`  # variable unit long name
   	cfulevel_number=`echo $variables  | cut -f7 -d' ' | sed -e 's/@/ /g'`  # variable level
   	cfulevel_type=`echo $variables    | cut -f8 -d' ' | sed -e 's/@/ /g'`  # variable level type
   	cfulevel_units=`echo $variables   | cut -f9 -d' ' | sed -e 's/@/ /g'`  # variable level unit
#
# Adding the variable level
#
   	ncap2 -s level_${varnew}="$cfulevel_number" ${output} -h -O ${output}
#
# Removing unnecessary attributes
#
        for att in units valid_range actual_range code table grid_type ; do 
	  ncatted -O -h -a ${att},${varnew},d,c, ${output}	
        done
#
# Adding and modifying the {varnew}iable attributes
#
        ncatted -O -h -a _FillValue,${varnew},a,f,1.e+12 ${output}
        ncatted -O -h -a standard_name,${varnew},o,c,"$cfustandard_name" ${output} # {varnew}iable standard name
        ncatted -O -h -a long_name,${varnew},o,c,"$cfulong_name" ${output}         # {varnew}iable long name
        ncatted -O -h -a cell_methods,${varnew},o,c,"$cfucell_methods" ${output}   # {varnew}iable cell methods
        ncatted -O -h -a unit_long,${varnew},o,c,"$cfuunit_long" ${output}         # {varnew}iable long unit name
        ncatted -O -h -a units,${varnew},o,c,"$cfuunit" ${output}                  # {varnew}iable units
        ncatted -O -h -a data_type,level_${varnew},o,c,"$cfulevel_type" ${output}  # {varnew}iable level type
        ncatted -O -h -a units,level_${varnew},o,c,"$cfulevel_units" ${output}     # {varnew}iable level units
        ncatted -O -h -a coordinates,${varnew},o,c,"longitude latitude reftime leadtime time_bnd experiment_id source realization institution level_${varnew}" ${output} # variable coordinates
#
# If the NetCDF file had a horizontal axis name different from longitude
#
        ncrename -h -d lon,longitude -v lon,longitude -d record,ensemble ${output}
#
# If the NetCDF file had a vertical axis name different from latitude
#
        ncrename -h -d lat,latitude -v lat,latitude  ${output}
#
# Adding variable axis
#
        ncatted -O -h -a axis,longitude,o,c,"X" ${output}       # variable longitude axis
        ncatted -O -h -a axis,latitude,o,c,"Y" ${output}        # variable latitude axis
        ncatted -O -h -a axis,level_${varnew},o,c,"Z" ${output} # variable level axis
# modify level information
# reshape the dimension and make time unlimited 

        ncpdq -O -h -a time,ensemble ${output} ${output}
        ncks -h -A header.nc ${output}

        nt=`cdo ntime ${output}`
        ncatted -O -h -a standard_name,level_${varnew},c,c,"height" ${output}       # standard name
        ncatted -O -h -a long_name,level_${varnew},c,c,"reference height" ${output} # long name
        ncatted -O -h -a data_type,level_${varnew},c,c,"float" ${output}            # data type
        ncatted -O -h -a units,level_${varnew},c,c,"m" ${output}                    # units
        ncatted -O -h -a axis,level_${varnew},c,c,"Z" ${output}                     # axis
        ncatted -O -h -a positive,level_${varnew},c,c,"up" ${output}
        ncap2 -O -h -s "level_${varnew}=float(${cfulevel_number})" $output $output
# delete history
        ncatted -h -a history,global,d,, $output
# change institution name
	    ncatted -h -a institution,global,m,c,"IC3" $output

# create a script to change the expid, insitutution, ensember, source and realiazation 
	i=0 # index
	for mem in ${MEM_LST[@]}; do
		v=`echo $mem | sed -e 's/fc//g'` # real value of the member without "fc"
cat>modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$expid";realization($i)=$v;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE"' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done
##
        delete_time $output # delete time variable 
        save_final_output $varnew $output

 done # loop for variables 
}

# for maximum and minimum temperature (manipulate daily data files)
function maxmin(){
for VAR in ${VAR_LST_MXMN[@]}; do
 new_name $VAR
 output=${VAR}_${sdate}.nc
 cp $DATADIR/${expid}/daily/$VAR/${VAR}_${sdate}_*.nc.gz .
 gunzip ${VAR}_${sdate}_*.nc.gz 
 sdate1=`echo ${sdate}|cut -c1-6`
 cdo timmean ${VAR}_${sdate}_${sdate1}.nc ${output}; rm ${VAR}_${sdate}_${sdate1}.nc
 files=`ls ${VAR}_${sdate}_*.nc` 
 for f in $files;do
  cdo timmean $f toto.nc;rm $f
  ncrcat -O -h ${output} toto.nc ${output};rm toto.nc
 done # loop for files
 ncrename -h -d lev,ensemble ${output}
 delete_var ${output} lev
 ncks -h -A header.nc ${output}
#
# Get the CFU standard attributes to be written in the variable
#
variables=`cat ${HEAD_DIR}/table_of_variable | cut -f$idx -d'|' | sed -e 's/ /@/g'`
cfustandard_name=`echo $variables | cut -f2 -d' ' | sed -e 's/@/ /g'`  # variable standard name
cfulong_name=`echo $variables     | cut -f3 -d' ' | sed -e 's/@/ /g'`  # variable long name
cfucell_methods=`echo $variables  | cut -f4 -d' ' | sed -e 's/@/ /g'`  # variable cell methods
cfuunit=`echo $variables          | cut -f5 -d' ' | sed -e 's/@/ /g'`  # variable unit
cfuunit_long=`echo $variables     | cut -f6 -d' ' | sed -e 's/@/ /g'`  # variable unit long name
cfulevel_number=`echo $variables  | cut -f7 -d' ' | sed -e 's/@/ /g'`  # variable level
cfulevel_type=`echo $variables    | cut -f8 -d' ' | sed -e 's/@/ /g'`  # variable level type
cfulevel_units=`echo $variables   | cut -f9 -d' ' | sed -e 's/@/ /g'`  # variable level unit
#
# Adding the variable level
#
ncap2 -s level_${varnew}="$cfulevel_number" ${output} -h -O ${output}
#
# Removing unnecessary attributes
#
for att in grid_type ; do 
 ncatted -O -h -a ${att},${varnew},d,c, ${output}      
done
#
# Adding and modifying the {varnew}iable attributes
#
ncatted -O -h -a standard_name,${varnew},o,c,"$cfustandard_name" ${output} # {varnew}iable standard name
ncatted -O -h -a long_name,${varnew},o,c,"$cfulong_name" ${output}         # {varnew}iable long name
ncatted -O -h -a cell_methods,${varnew},o,c,"$cfucell_methods" ${output}   # {varnew}iable cell methods
ncatted -O -h -a data_type,level_${varnew},o,c,"$cfulevel_type" ${output}  # {varnew}iable level type
ncatted -O -h -a units,level_${varnew},o,c,"$cfulevel_units" ${output}     # {varnew}iable level units
ncatted -O -h -a coordinates,${varnew},o,c,"longitude latitude reftime leadtime time_bnd experiment_id source realization institution level_${varnew}" ${output}
#
# Adding variable axis
#
ncatted -O -h -a axis,longitude,o,c,"X" ${output}       # variable longitude axis
ncatted -O -h -a axis,latitude,o,c,"Y" ${output}        # variable latitude axis
ncatted -O -h -a axis,level_${varnew},o,c,"Z" ${output} # variable level axis
# delete history
ncatted -h -a history,global,d,, $output
# change institution name
ncatted -h -a institution,global,m,c,"IC3" $output 

# create a script to change the expid, insitutution, ensember, source and realiazation 
	i=0 # index
	for mem in ${MEM_LST[@]}; do
		v=`echo $mem | sed -e 's/fc//g'` # real value of the member without "fc"
cat>modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$expid";realization($i)=$v;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE"' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done
##

    save_final_output $varnew $output
done # loop for variables 
}

# for pressure level variables (manipulate SH files)
extract(){
for mem in ${MEM_LST[@]}; do
# untar and unzip MMA SH files and GG files also if Q is in variable list
    path_to_search=${base_path}/$mem
    file_list=`find $path_to_search -type f -iname "mma*" 2> /dev/null`
    for f in ${file_list};do
     SH_files=`tar tf ${f}|grep SH`
     for file in ${SH_files};do
      tar xvf ${f} ${file};gunzip -q ${file}
     done
     if [[ $qq == 1 ]];then
      GG_files=`tar tf ${f}|grep GG`
      for file in ${GG_files};do
       tar xvf ${f} ${file};gunzip -q ${file}
      done
     fi
    done

# Select variables and levels   
   files=`ls MMA*SH*.nc`
   echo $files
   for f in ${files}; do   
    for var in ${VAR_LST_3D[@]}; do
      case $var in 
	   T|U|V|Z)
        new_name $var
        tmp_out=tmp_${varnew}_$f
        cdo selname,${var} -sellevel,${LEVEL_LST} ${f} ${tmp_out}
      ;;
     esac
    done
    rm ${f}
   done

   if [[ $qq == 1 ]];then
    files=`ls MMA*GG*.nc`
    echo $files
    for f in ${files}; do
     new_name Q
     tmp_out=tmp_${varnew}_$f
     cdo selname,Q -sellevel,${LEVEL_LST} ${f} ${tmp_out}
   	 rm ${f}
    done
   fi 

# combine all time step in one file
     for var in ${VAR_LST_3D[@]}; do
	  new_name $var
      files=`ls tmp_${varnew}_*`
      output=${varnew}_$sdate.$mem.nc
      cdo copy ${files} ${output} # combine all the time steps in one file
      ncrename -v ${var},${varnew} ${output}
      rm -r ${files}
    done #loop for variables 
done # loop for members 
}

# interpolate from SH to regular grid
regrid2x2(){
 for var in ${VAR_LST_3D[@]}; do
   new_name $var
   files=`ls ${varnew}_$sdate.*.nc`
   for f in ${files}; do   
    case $var in 
     T|U|V|Z|W)
      cdo -r sp2gp -selname,${varnew} ${f} rg_${f}; rm ${f}
     ;;
     Q|CC|CIWC|CLWC)
      cdo selname,${varnew} ${f} rg_${f}; rm ${f}
     ;;
    esac
   done
 done
}

function upper(){
   for var in ${VAR_LST_3D[@]}; do
    new_name $var
	output=${varnew}_$sdate.nc
	files=`ls rg_${varnew}_$sdate.*.nc`
	ncecat ${files} ${output} # Combine all members in one file by add one more dimension 
	rm ${files}
	ncrename -d lon,longitude -d lat,latitude -d lev,level ${output}
	ncrename -v lon,longitude -v lat,latitude -v lev,level ${output}
#
# Get the CFU standard attributes to be written in the variable
#
        variables=`cat ${HEAD_DIR}/table_of_variable | cut -f$idx -d'|' | sed -e 's/ /@/g'`
        cfustandard_name=`echo $variables | cut -f2 -d' ' | sed -e 's/@/ /g'`  # variable standard name
        cfulong_name=`echo $variables     | cut -f3 -d' ' | sed -e 's/@/ /g'`  # variable long name
        cfucell_methods=`echo $variables  | cut -f4 -d' ' | sed -e 's/@/ /g'`  # variable cell methods
        cfuunit=`echo $variables          | cut -f5 -d' ' | sed -e 's/@/ /g'`  # variable unit
        cfuunit_long=`echo $variables     | cut -f6 -d' ' | sed -e 's/@/ /g'`  # variable unit long name
        cfulevel_number=`echo $variables  | cut -f7 -d' ' | sed -e 's/@/ /g'`  # variable level
        cfulevel_type=`echo $variables    | cut -f8 -d' ' | sed -e 's/@/ /g'`  # variable level type
        cfulevel_units=`echo $variables   | cut -f9 -d' ' | sed -e 's/@/ /g'`  # variable level unit
#
# modify variable attributes
#
        for att in units valid_range actual_range code table grid_type truncation; do
          ncatted -O -h -a ${att},${varnew},d,, ${output}
        done

        ncatted -O -h -a _FillValue,${varnew},a,f,1.e+12 ${output}
        ncatted -O -h -a standard_name,${varnew},o,c,"$cfustandard_name" ${output} # variable standard name
        ncatted -O -h -a long_name,${varnew},o,c,"$cfulong_name" ${output}         # variable long name
        ncatted -O -h -a cell_methods,${varnew},o,c,"$cfucell_methods" ${output}   # variable cell methods
        ncatted -O -h -a unit_long,${varnew},o,c,"$cfuunit_long" ${output}         # variable long unit name
        ncatted -O -h -a units,${varnew},o,c,"$cfuunit" ${output}                  # variable units
        ncatted -O -h -a data_type,level,o,c,"$cfulevel_type" ${output}       # variable level type
        ncatted -O -h -a units,level,o,c,"$cfulevel_units" ${output}          # variable level units
        ncatted -O -h -a coordinates,${varnew},o,c,"longitude latitude leadtime reftime time_bnd experiment_id source realization institution level" ${output}  
#
# If the NetCDF file had a horizontal axis name different from longitude
#
        ncrename  -d record,ensemble ${output}
#
# modify logitude attributes  
#
        lon_min=0
        lon_max=359.25
        lat_min=-89.4270841760375
        lat_max=89.4270841760375  # These valuse shoud be obtaind from the file instead of hardcoded

        ncatted -O -h -a axis,longitude,o,c,"X" ${output}     # variable longitude axis
        ncatted -O -h -a topology,longitude,c,c,"circular" ${output}     # variable longitude axis
        ncatted -O -h -a modulo,longitude,c,f,"360" ${output}     # variable longitude axis
        ncatted -O -h -a valid_min,longitude,c,f,"$lon_min" ${output}     # variable longitude valid_min
        ncatted -O -h -a valid_max,longitude,c,f,"$lon_max" ${output}     # variable longitude valid_max
# modify latitude attributes 
        ncatted -O -h -a axis,latitude,o,c,"Y" ${output}      # variable latitude axis
        ncatted -O -h -a valid_min,latitude,c,f,"$lat_min" ${output}     # variable latitude valid_min
        ncatted -O -h -a valid_max,latitude,c,f,"$lat_max" ${output}     # variable latitude valin_max
# modify level attributes 
        ncatted -O -h -a standard_name,level,o,c,"air_pressure" ${output} # standard name
        ncatted -O -h -a long_name,level,o,c,"air pressure" ${output}         # long name
        ncatted -O -h -a data_type,level,o,c,"float" ${output}       # data type
        ncatted -O -h -a units,level,o,c,"hPa" ${output}                  #  units
        ncatted -O -h -a axis,level,o,c,"Z" ${output}          # axis
        ncatted -O -h -a positive,level,c,c,"up" ${output}
###
# modify the level values, should be hPa instead of Pa
	    ncap2 -O -h -s "level()=level()/100" ${output} ${output} 

        ncpdq -O -h -a time,ensemble ${output} ${output} # reshape the dimension and make time unlimited
      #  ncks  -h -A $HEAD_DIR/${sdate}.nc ${output}
        ncks  -h -A header.nc ${output}
	    delete_time $output
        ncatted -h -a history,global,d,, $output  #delete history
        ncatted -h -a institution,global,m,c,"IC3" $output ## change institution name in global attributes

# create a script to change the expid, insitutution, ensember, source and realiazation 
	i=0 # index
	for mem in ${MEM_LST[@]}; do
		v=`echo $mem | sed -e 's/fc//g'` # real value of the member without "fc"
cat>modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$expid";realization($i)=$v;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE"' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done
##
        rm -f ${files}*
        save_final_output $varnew $output
 done # loop over variables 
}

# save final post-processed output (file in *.nc format)
function save_final_output(){
 varnew=$1
 output=$2

 tardir=${SAVEDIR}/${expid}/monthly_mean/${varnew}_3hourly/
 mkdir -p $tardir
 find ${SAVEDIR}/${expid}/monthly_mean/. -type d | xargs chmod 775 2>/dev/null
  if [ -e ${tardir}/${output} ] ; then
   mv ${output} new_${output}
   ncpdq -O -h -a ensemble,time new_${output} new_${output} # shape the dimensions
   mv ${tardir}/${output} old_${output}
   ncpdq -O -h -a ensemble,time old_${output} old_${output} # shape the dimensions
   ncrcat -O -h old_${output} new_${output} ${output}
   ncpdq -O -h -a time,ensemble ${output} ${output}         # again reshape the dimensions as per requirement of final output
   rm old_${output} new_${output}
  fi
 chmod 770 ${output}
 mv ${output} ${tardir}
}
####  End of the User Defined Functions  #### 


###################################
####  Main Part of the Script  ####
###################################

# NCO and CDO must be available in $PATH

date

check_args $@

expid=$1
sdate=$2

rm -rf ${WORKDIR}
mkdir -p ${WORKDIR}
if [[ ! -d ${WORKDIR} ]]; then
 exit 1
fi
cd ${WORKDIR}

base_path=${DATADIR}/${expid}/${sdate}
mkdir -p ${SAVEDIR}/${expid}; # chmod -R 775 $SAVEDIR/${expid} 

# seperate and count 2D&3D varaibles
j=1
k=1
l=1
qq=0
for var in ${VAR_LST}; do
 if [[ $var == 'Q' ]] ;then
  qq=1
 fi
 case $var in
 T2M|D2M|SST|MSL|PRECIP|SSR|STR|TTR|TSR|TSRC|TTRC|SLHF|SSHF|U10M|V10M|SSRD|CP|SF|E|SSRU|SSRC|STRU|STRD|TCC)
 VAR_LST_2D[$j]="$var"
 j=$((j+1))
 ;;
 T|U|V|Z|Q|W|CC|CIWC|CLWC)
 VAR_LST_3D[$k]="$var"
 k=$((k+1))
 ;;
 tasmax|tasmin)
 VAR_LST_MXMN[$l]="$var"
 l=$((l+1))
 ;;
 esac
done

get_leadtime
header $sdate

if [[ ${#VAR_LST_2D[@]} > 0 ]]; then
 surface
fi

if [[ ${#VAR_LST_3D[@]} > 0 ]]; then
 extract
 regrid2x2
 upper
fi

if [[ ${#VAR_LST_MXMN[@]} > 0 ]]; then
 maxmin
fi

cd; rm -rf $WORKDIR # clean up

date
####  End of the Main Part of Script  ####
