#!/bin/bash
#
# ./nccf_atm_monthly.sh path_to_config_file >& EXPID-startdate.log &
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
# Adapted: Pierre-Antoine Bretonnière - IC3 , January 2013
set -xv

#################################
####  User Defined Funtions  #### 
#################################

# check if args are ok
function check_args(){
NB_ARGS=$#
 if [ $# -ne 1 ] ; then
  echo
  echo "USAGE: config_file "
  echo "For example: ./nccf_atm_monthly.new.sh /home/$user/cfu_git/autosubmit/pp/atmos/config_file "
  echo
  exit 1
 fi
}

function get_leadtime(){
#gets lead_time and checks if all members have the same number of months
NMONTH=9999999
for DIR in $MEM_LST
do
 cd ${DATADIR}/${EXPID}/${SDATE}/${DIR}/outputs # hard coded
 NFILE=`ls MMA*|wc -l`
 for TMPFILE in `ls MMA*`
  do
     NMONTHS_LOC=`tar tvf $TMPFILE | grep GG | wc -l`
    [ $NMONTH -ne $NMONTHS_LOC ] && [ $NMONTH -ne 9999999 ] && echo "all members or start dates don't have the same number of months, be careful" 
    [ $NMONTH -ge $NMONTHS_LOC ] && NMONTH=$NMONTHS_LOC
  done
 NLT=$((NFILE*NMONTH))
 cd ${WORKDIR}
done
}

function header(){
 SD=$1
 rtime 19500101 ${SD}
 ncks -h -d ensemble,0,$((ENSEMBLE-1)),1 ${HEAD_DIR}/template.nc toto.nc # select sub member
 cp toto.nc toto1.nc
 TIME_BND1=0
 TIME_BND2=`get_hours $SD`
 LEADTIME=$(((TIME_BND1+TIME_BND2)/2))

 ncap2 -O -h -s "leadtime(0)=${LEADTIME};time_bnd(,0)=${TIME_BND1};time_bnd(,1)=${TIME_BND2}" toto.nc toto.nc

 for ((i=1;i<=$((NLT-1));i++)); do
  FORDATE=`leadtime2date $SD $i`
  INTERVAL=`get_hours $FORDATE`
  TIME_BND1=$TIME_BND2
  TIME_BND2=$((TIME_BND1+INTERVAL))
  LEADTIME=$(((TIME_BND1+TIME_BND2)/2))
  echo $fordate $interval $time_bnd1 $time_bnd2
  ncap2 -O -h -s "reftime(0)=${REFTIME_VALUE};leadtime(0)=${LEADTIME};time_bnd(,0)=${TIME_BND1};time_bnd(,1)=${TIME_BND2}" toto1.nc toto1.nc
  ncrcat -O -h toto.nc toto1.nc toto.nc
 done

 mv toto.nc header.nc; rm toto1.nc

 ncap2 -O -h -s "reftime(0)=reftime(1)" header.nc header.nc
}


# function to get reftime time
function rtime(){
 DATE1=$1
 DATE2=$2
 FACTOR=day # h for hour, d for days
 YEAR1=`echo $DATE1|cut -c1-4`
 MONTH1=`echo $DATE1|cut -c5-6`
 DAY1=`echo $DATE1|cut -c7-8`
 YEAR2=`echo $DATE2|cut -c1-4`
 MONTH2=`echo $DATE2|cut -c5-6`
 DAY2=`echo $DATE2|cut -c7-8`
 SEC1=`date --utc --date "${YEAR1}-${MONTH1}-${DAY1}" +%s`
 SEC2=`date --utc --date "${YEAR2}-${MONTH2}-${DAY2}" +%s`
 case $FACTOR in 
  hour)
  FACTOR=3600 # 60*60
  ;;
  day)
  FACTOR=86400 # 60*60*24
  ;;
 esac
 REFTIME_VALUE=$(((SEC2-SEC1)/FACTOR))
}


function leadtime2date(){
# function leadtime2date, based on starting date and lead time to calculate date(year &  month) of the corresponding leadtime
 INIDATE=$1
 OFFSET=$2

 YY=`echo $INIDATE|cut -c1-4`
 MM=`echo $INIDATE|cut -c5-6`
 MM=`echo $MM | sed 's/^0*//;s/^$/0/' `
 YY1=$((YY+offset/12))

 NMONTH=$((offset%12))
 MM1=$((MM+NMONTH))
 if [ $MM1 -gt 12 ]; then
  YY1=$((YY1+1))
  MM1=$((MM1-12))
 fi

 if [ $MM1 -lt 10 ]; then
  MM1="0$MM1"
 fi
}

# get the total number of HOURS for a specific MONTH
function get_hours(){
 YYMM=$1
 YEAR=`echo $YYMM|cut -c1-4`
 MONTH=`echo $YYMM|cut -c5-6`
 NDAYS=$(cal $MONTH $YEAR |egrep "^[ 0-9][0-9]| [ 0-9][0-9]$" |wc -w)
 HOURS=$((NDAYS*24))
 echo $HOURS
}


function extract(){

typeset var jt
typeset var YEAR0
typeset var YEARF
typeset var MON0
typeset var MONF

for MEM in ${MEM_LST[@]}; do
# untar and unzip MMA SH files and GG files 

if [  -z ${LEAD_LIST[@]} ];then 
 PATH_TO_SEARCH=${DATADIR}/${EXPID}/${SDATE}/$MEM
 FILE_LIST=`find $PATH_TO_SEARCH -type f -iname "MMA*" 2> /dev/null`
else
 YEAR0=${LEAD_LIST[0]}
 MON0=${LEAD_LIST[1]}
 YEARF=${LEAD_LIST[2]}
 MONF=${LEAD_LIST[3]}
 CHUNK_SIZE=${LEAD_LIST[4]}
 YYYY0=`echo $SDATE | cut -b -4`
 MM0=`echo $SDATE | cut -b 5-6`
 LTIME0=1
 LTIMEF=$(( ( ($YEARF - $YEAR0) * 12 + $MONF - $MON0+1 )/$CHUNK_SIZE ))
 jt=$LTIME0
 while [ $jt -le $((LTIMEF)) ]
  do 
   YEAR1=$(( $YEAR0 +($MON0+($jt-1)*$CHUNK_SIZE-1)/ 12 ))
   MON1=$(( ( $MON0 + ( $jt - 1 ) * ($CHUNK_SIZE) ) % 12))   
   YEAR2=$(( $YEAR1 + ( $MON1 + $CHUNK_SIZE-1 ) / 12  ))
   MON2=$(( ( $MON1 + $CHUNK_SIZE-1 ) % 12 ))
   jt=$(($jt+1))
   FILE=` ls ${DATADIR}/${EXPID}/${SDATE}/$MEM/outputs/MMA_${EXPID}_${SDATE}_${MEM}_${YEAR1}$(printf "%02d" $MON1)01-${YEAR2}$(printf "%02d" $MON2)*.tar`
   FILE_LIST="$FILE_LIST ${FILE}"
  done
fi
 echo ${FILE_LIST}
    
   for f in ${FILE_LIST};do
     SH_FILES=`tar tf ${f}|grep SH`
     for FILE in ${SH_FILES};do
      tar xvf ${f} ${FILE} ;gunzip -q ${FILE}; mv ${FILE%???} ${FILE%???}.$MEM
     done
      GG_FILES=`tar tf ${f}|grep GG`
      for FILE in ${GG_FILES};do
       tar xvf ${f} ${FILE} ;gunzip -q ${FILE}; mv ${FILE%???} ${FILE%???}.$MEM
      done
    done
done
}

function read_vars(){
#if no list of variables is provided in the namelist, looks for all variables in the files
OUTPUT_FILE=$1
GRID_TYPE=$2

VAR_LST_DIM=`ncdump -h $OUTPUT_FILE | grep float | sed -e s/float//g | sed -e s/\,\ /@/g  | sed -e s/\;//g ` #get the names of the variables in output files
for VAR_DIM in $VAR_LST_DIM
do
NB_DIMS=`echo $VAR_DIM | sed -e s/[^@]/\ /g | wc -w` #count the number of dimensions of each variable
VAR=`echo $VAR_DIM | sed -e 's/(.*)//g' `
case $GRID_TYPE in
 GG)
[ $NB_DIMS -eq 2 ] && VAR_LST_2D_GG=`echo ${VAR_LST_2D_GG} $VAR` || VAR_LST_3D_GG=`echo ${VAR_LST_3D_GG} $VAR` #create a separate list of variables for 2d and 3d
;;
 SH)
[ $NB_DIMS -eq 2 ] && VAR_LST_2D_SH=`echo ${VAR_LST_2D_SH} $VAR` || VAR_LST_3D_SH=`echo ${VAR_LST_3D_SH} $VAR` #create a separate list of variables for 2d and 3d
;;
esac

done
}

# for surface variables (manipulate GG files)
function surface(){
echo ${MEM_LST[@]}
for MEM in ${MEM_LST[@]}; do
  FILES=`ls MMA*GG*.nc.$MEM` 
####  process each variable  ####
 for VAR in ${VAR_LST_2D[@]}; do # untar once and extract all the variables
	new_name $VAR	
      case $VAR in
        "PRECIP") # for precip, have to add CP and LSP to get total precip
	      varnew=prlr
          for f in ${FILES}; do
            SUFFIX=$MEM.$f
            cdo selname,CP $f CP.$SUFFIX # select CP
            ncrename -h -v CP,prlr CP.$SUFFIX 
            cdo selname,LSP $f LSP.$SUFFIX # select LSP       
            ncrename -h -v LSP,prlr LSP.$SUFFIX
            cdo add CP.$SUFFIX LSP.$SUFFIX ${varnew}.${SUFFIX} # add CP and LSP to get total precipitation 
            cdo divc,${FACTOR} ${varnew}.${SUFFIX} toto.nc;rm ${varnew}.${SUFFIX}; mv toto.nc ${varnew}.${SUFFIX}
          done
          prlr_files=`ls ${varnew}*`
          cdo copy ${prlr_files} tmp_${varnew}_$SDATE.$MEM.nc # combine all the time steps in one file
          rm -r prlr*.nc CP* LSP*
        ;;
        "SSRU")
          varnew=rsus
          for f in ${FILES}; do
            SUFFIX=$MEM.$f
            cdo selname,SSRD $f SSRD.$SUFFIX 
            ncrename -h -v SSRD,rsus SSRD.$SUFFIX
            cdo selname,SSR $f SSR.$SUFFIX        
            ncrename -h -v SSR,rsus SSR.$SUFFIX
            cdo sub SSR.$SUFFIX SSRD.$SUFFIX ${varnew}.${SUFFIX}   
            cdo divc,${FACTOR} ${varnew}.${SUFFIX} toto.nc;rm ${varnew}.${SUFFIX}; mv toto.nc ${varnew}.${SUFFIX}
          done
          rsus_files=`ls ${varnew}*`
          cdo copy ${rsus_files} tmp_${varnew}_$SDATE.$MEM.nc # combine all the time steps in one file
          rm -r rsus*.nc SSR* SSRD*
        ;;
        "STRU")
          varnew=rlus
          for f in ${FILES}; do
            SUFFIX=$MEM.$f
            cdo selname,STRD $f STRD.$SUFFIX 
            ncrename -h -v STRD,rlus STRD.$SUFFIX
            cdo selname,STR $f STR.$SUFFIX                   
            ncrename -h -v STR,rlus STR.$SUFFIX
            cdo sub STR.$SUFFIX STRD.$SUFFIX ${varnew}.${SUFFIX}   
            cdo divc,${FACTOR} ${varnew}.${SUFFIX} toto.nc;rm ${varnew}.${SUFFIX}; mv toto.nc ${varnew}.${SUFFIX}
          done
          rsus_files=`ls ${varnew}*`
          cdo copy ${rsus_files} tmp_${varnew}_$SDATE.$MEM.nc # combine all the time steps in one file
          rm -r rlus*.nc STR* STRD*
        ;;
        *)  
	      new_name $VAR       
          for f in ${FILES};do
            cdo selname,${VAR} ${f} ${VAR}.$MEM.${f%????}
          done
          TMP_FILES=`ls ${VAR}*.nc`
          TMP_OUT=tmp_${varnew}_$SDATE.$MEM.nc
          cdo copy ${TMP_FILES} ${TMP_OUT} # combine all the time steps in one file
          ncrename -v ${VAR},${varnew} ${TMP_OUT}
          case ${varnew} in
            "rss"|"rls"|"rsscs"|"rsds"|"rlds"|"hflsd"|"hfssd"|"rlt"|"rst"|"rltcs"|"rstcs")
            cdo divc,${FACTOR} ${TMP_OUT} toto.nc; rm ${TMP_OUT};mv toto.nc ${TMP_OUT}
            ncatted -O -a units,${varnew},m,c,"W m-2" ${TMP_OUT}
            ;;
          esac
          rm ${TMP_FILES}
#          cdo divc,${FACTOR} ${TMP_OUT} toto.nc; rm ${TMP_OUT};mv toto.nc ${TMP_OUT}
        ;;
      esac
  done # loop for VAR
done # loop for members 

# finish selecting the variables 
# combine members and change the attributes
 for VAR in ${VAR_LST_2D[@]}; do 
    new_name $VAR
    LSMBSH=${LISTMEMB[0]}-${LISTMEMB[${#LISTMEMB[@]}-1]}
    PREVIOUS_FILE=`ls -tr ${SAVEDIR}/${EXPID}/monthly_mean/${varnew}_3hourly/${varnew}_${SDATE}_*.nc | tail -1`
    if [ ! -z $PREVIOUS_FILE ] ; then
     cd ${SAVEDIR}/${EXPID}/monthly_mean/${varnew}_3hourly/; FILE_NAME_PREVIOUS=`ls ${varnew}_${SDATE}_*.nc | tail -1 `; cd -
     IDX_1ST=`echo ${varnew}_${SDATE}_ | wc -m `
     FIRST_MEMBER_PREVIOUS=`echo $FILE_NAME_PREVIOUS | cut -b$IDX_1ST `
     IDX_LST=` expr $IDX_1ST + 2 `
     LAST_MEMBER_PREVIOUS=`echo $FILE_NAME_PREVIOUS  | cut -b$IDX_LST `
#security check:
     if [ $LAST_MEMBER_PREVIOUS -le `expr ${LISTMEMB[0]} - 1 ` ] ; then
     cp $PREVIOUS_FILE tmp_$FILE_NAME_PREVIOUS
       if [ $LAST_MEMBER_PREVIOUS -eq `expr ${LISTMEMB[0]} - 1 ` ] ; then
        LSMBSH=${FIRST_MEMBER_PREVIOUS}-${LISTMEMB[${#LISTMEMB[@]}-1]}
       else
        echo "Actual list of members does not follow directly the ones already post-processed! Check you did not forget any members at the beginning of your list"
        MISSING_FIRST=`expr ${LAST_MEMBER_PREVIOUS} + 1 `
        MISSING_LAST=`expr ${LISTMEMB[0]} - 1 `
        LSMBSH=${FIRST_MEMBER_PREVIOUS}_${LISTMEMB[${#LISTMEMB[@]}-1]}-${MISSING_FIRST}_${MISSING_LAST}
       fi
     else
      echo "Some members are going to be treated twice! If you are not adding new lead_times, revise the consistency between your member list and the previously processed files"
     fi
    fi
gather_memb tmp_${varnew}_$SDATE ${varnew}_${SDATE}_${LSMBSH}.nc $varnew $VAR
output=${varnew}_${SDATE}_${LSMBSH}.nc

##### Change the header informations #####
#
# Get the CFU standard attributes to be written in the variable
#
   	variables=`cat ${HEAD_DIR}/table_of_variable | cut -f$idx -d'|' | sed -e 's/ /@/g'`  #to be changed into more interactive with xml table
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
        for att in units valid_range actual_range code table GRID_TYPE ; do 
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
        ncrename -h -d lon,longitude -v lon,longitude  ${output}
        ncrename -h -d record,ensemble ${output}
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

# create a script to change the EXPID, insitutution, ensember, source and realiazation 
	i=0 # index
	for MEM in ${LISTMEMB[@]}; do

cat>modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$EXPID";realization($i)=$MEM;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE"' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done
##
        ncrename -O -h -v time,kaka $output # delete time variable 
        ncks -O -h -x -v kaka $output $output # delete time variable
        save_final_output $varnew $output

 done # loop for variables 
}

function new_name(){  #to be rethought: make a match between var_name and xml table
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
        "SSTK")
#        "SST")
#weird...        VAR=SSTK
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
        "CC")
        varnew=cl
        idx=35
#pab!!!! new variables to be added when variable list read directly in outputs, some are missing
        ;;
        *)
        varnew=$1
        idx=000
        ;;
      esac
}


function gather_memb {

#  Gather the members in a single netcdf file 

# $1 : prefix netcdf file name for all the members        
# $2 : output file name                               
# Created in May 2012           Author : vguemas@ic3.cat                            
# Adapted for atmospherical outputs January 2013 pierre-antoine.bretonniere@ic3.cat 

  OLD_FILE=`ls ${1}_*`
  NEW_FILES=`ls ${1}.*`
  VAR_LOC=$3
  VAR_OLD=$4

  rm -f tmp_cat.nc tmp_0_${OLD_FILE} tmp_${OLD_FILE} 
  ncecat ${NEW_FILES} tmp_cat.nc
  ncrename -d record,ensemble tmp_cat.nc
  ncecat -O -h tmp_cat.nc tmp_cat2.nc
  ncpdq -O -h -a ensemble,record tmp_cat2.nc tmp_cat2.nc
  ncwa -O -h -a record tmp_cat2.nc tmp_cat2.nc
  mv tmp_cat2.nc tmp_cat.nc #new
 for var_check in $VAR_LST_3D_GG
  do
  if [ $VAR_OLD == $var_check ];then
   ncks -O -h -a -v lon,lat,$VAR_LOC tmp_cat.nc tmp_cat.nc
#   ncks -O -h -a -v lon,lat,$VAR_LOC tmp_cat2.nc tmp_cat3.nc
#   mv tmp_cat3.nc tmp_cat.nc
#  else
#   mv tmp_cat2.nc tmp_cat.nc
  fi
 done
 if [ ! -z $OLD_FILE ] ; then
  ncks -C -O -v longitude,latitude,$VAR_LOC $OLD_FILE tmp_0_${OLD_FILE}
  ncecat -O -h tmp_0_${OLD_FILE} tmp_${OLD_FILE}
  ncpdq -O -h -a ensemble,record tmp_${OLD_FILE} tmp_${OLD_FILE}
  ncwa -O -h -a record tmp_${OLD_FILE} tmp_${OLD_FILE}
  ncrcat tmp_cat.nc tmp_${OLD_FILE} $2
 else
  mv tmp_cat.nc $2
 fi
}

function save_final_output(){
# save final post-processed output (file in *.nc format)
 varnew=$1
 output=$2
   
 TARDIR=${SAVEDIR}/${EXPID}/monthly_mean/${varnew}_${NFRP}hourly
 [ ! -d $TARDIR ] && mkdir -p $TARDIR
 find ${SAVEDIR}/${EXPID}/monthly_mean/. -type d | xargs chmod 775 2>/dev/null
  if [ -e ${TARDIR}/${output} ] ; then
   mv ${output} new_${output}
   ncpdq -O -h -a ensemble,time new_${output} new_${output} # shape the dimensions
   mv ${TARDIR}/${output} old_${output}
   ncpdq -O -h -a ensemble,time old_${output} old_${output} # shape the dimensions
   ncrcat -O -h old_${output} new_${output} ${output}
   ncpdq -O -h -a time,ensemble ${output} ${output}         # again reshape the dimensions as per requirement of final output
   rm old_${output} new_${output}
  fi
 chmod 770 ${output}
 mv ${output} ${TARDIR}
#for tos, change value on land from 0 to NaN
 if [ $varnew == "tos" ]; then
#  ln -sf /cfunas/exp/ecearth/land_sea_mask_320x160.nc .
  ln -sf ${MASK_PATH} .
  cdo div `basename ${MASK_PATH}` `basename ${MASK_PATH}` mask1.nc
#  cdo div land_sea_mask_320x160.nc land_sea_mask_320x160.nc mask1.nc
  cdo div $output mask1.nc $output.tmp
  mv $output.tmp $output
  rm mask1.nc `basename ${MASK_PATH}`
 fi
#to make a smooth transition between the 2 versions of nccf_atm_monthly, as R functions look for atmospherical monthly means called $var_yyyymmdd.nc (without the members), a link between the 2 naming conventions is created so that R functions still work while they have not been updated.
 ln -sf ${TARDIR}/${output} ${TARDIR}/${varnew}_${SDATE}.nc
}
   
# Select variables and levels   
function combine_3d(){
for MEM in ${MEM_LST[@]}; do
   FILES=`ls MMA*SH*.nc.$MEM`
   echo $FILES
   for f in ${FILES}; do   
    for var in ${VAR_LST_3D_SH[@]}; do
        new_name $var
        TMP_OUT=tmp_${varnew}_$f
        cdo selname,${var} -sellevel,${LEVEL_LST} ${f} ${TMP_OUT}
    done
    rm ${f}
   done
    FILES=`ls MMA*GG*.nc.$MEM`
    for f in ${FILES}; do
   for var in ${VAR_LST_3D_GG[@]}; do
        new_name $var
        TMP_OUT=tmp_${varnew}_$f
     case $var in #pab
       Q)  
        cdo selname,${var} -sellevel,${LEVEL_LST} ${f} ${TMP_OUT} #
       ;;
       *)
        cdo selname,${var} ${f} ${TMP_OUT} #pab
        ;;
      esac
    done
    done

# combine all time step in one file
     for var in ${VAR_LST_3D[@]}; do
	  new_name $var
      FILES=`ls tmp_${varnew}_*`
      output=${varnew}_$SDATE.$MEM.nc
      cdo copy ${FILES} ${output} # combine all the time steps in one file
      ncrename -v ${var},${varnew} ${output}
      rm -r ${FILES}
    done #loop for variables 
done # loop for members 
}
######end of combine3d ##########


# interpolate from SH to regular grid
function regrid2x2(){
 for var in ${VAR_LST_3D_SH[@]}; do
   new_name $var
   FILES=`ls ${varnew}_$SDATE.*.nc`
   for f in ${FILES}; do   
      cdo -r sp2gp -selname,${varnew} ${f} rg_${f}; rm ${f}
   done
 done
 for var in ${VAR_LST_3D_GG[@]}; do
   new_name $var
   FILES=`ls ${varnew}_$SDATE.*.nc`
   for f in ${FILES}; do
 
      cdo selname,${varnew} ${f} rg_${f}; rm ${f}
   done
 done
}


function upper(){
   for var in ${VAR_LST_3D[@]}; do
    new_name $var


    LSMBSH=${LISTMEMB[0]}-${LISTMEMB[${#LISTMEMB[@]}-1]}
    PREVIOUS_FILE=`ls ${SAVEDIR}/${EXPID}/monthly_mean/${varnew}_3hourly/${varnew}_${SDATE}_*.nc | tail -1`
    if [  ! -z $PREVIOUS_FILE ] ; then
     cd ${SAVEDIR}/${EXPID}/monthly_mean/${varnew}_3hourly/; FILE_NAME_PREVIOUS=`ls ${varnew}_${SDATE}_*.nc | tail -1 `; cd -
     IDX_1ST=`echo ${varnew}_${SDATE}_ | wc -m `
     FIRST_MEMBER_PREVIOUS=`echo $FILE_NAME_PREVIOUS | cut -b$IDX_1ST `
     IDX_LST=` expr $IDX_1ST + 2 `
     LAST_MEMBER_PREVIOUS=`echo $FILE_NAME_PREVIOUS  | cut -b$IDX_LST `
#security check:
     if [ $LAST_MEMBER_PREVIOUS -le `expr ${LISTMEMB[0]} - 1 ` ] ; then
        cp $PREVIOUS_FILE rg_$FILE_NAME_PREVIOUS
       if [ $LAST_MEMBER_PREVIOUS -eq `expr ${LISTMEMB[0]} - 1 ` ] ; then
        LSMBSH=${FIRST_MEMBER_PREVIOUS}-${LISTMEMB[${#LISTMEMB[@]}-1]}
       else
        echo "Actual list of members does not follow directly the ones already post-processed! Check you did not forget any members at the beginning of your list"
        MISSING_FIRST=`expr ${LAST_MEMBER_PREVIOUS} + 1 `
        MISSING_LAST=`expr ${LISTMEMB[0]} - 1 `
        LSMBSH=${FIRST_MEMBER_PREVIOUS}_${LISTMEMB[${#LISTMEMB[@]}-1]}-${MISSING_FIRST}_${MISSING_LAST}
       fi
     else
      echo "Some members are going to be treated twice! Revise the consistency between your member list and the previously processed files"
     fi
    fi
    gather_memb rg_${varnew}_$SDATE ${varnew}_${SDATE}_${LSMBSH}.nc $varnew $VAR
    output=${varnew}_${SDATE}_${LSMBSH}.nc
	rm ${FILES}
   for CHECK_VAR in $VAR_LST_3D_SH
    do
    if [ $CHECK_VAR == $var ];then
    	ncrename -d lon,longitude -d lat,latitude -d lev,level ${output}
    	ncrename -v lon,longitude -v lat,latitude -v lev,level ${output}
    fi
   done
   for CHECK_VAR in $VAR_LST_3D_GG
    do
    if [ $CHECK_VAR == $var ];then
#	ncrename -d lon,longitude -d lat,latitude -d mlev,level ${output}
#    ncrename -v lon,longitude -v lat,latitude -v mlev,level ${output}
	ncrename -d lon,longitude -d lat,latitude ${output}
    ncrename -d mlev,level ${output}
    ncrename -v lon,longitude -v lat,latitude ${output}
    ncrename -v mlev,level ${output}
    fi
   done
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
        for att in units valid_range actual_range code table GRID_TYPE truncation; do
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
      #  ncks  -h -A $HEAD_DIR/${SDATE}.nc ${output}
        ncks  -h -A header.nc ${output}
        ncrename -O -h -v time,kaka $output # delete time variable 
        ncks -O -h -x -v kaka $output $output # delete time variable
        ncatted -h -a history,global,d,, $output  #delete history
        ncatted -h -a institution,global,m,c,"IC3" $output ## change institution name in global attributes

# create a script to change the EXPID, insitutution, ensember, source and realiazation 
	i=0 # index
	for mem in ${LISTMEMB[@]}; do
cat>modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$EXPID";realization($i)=$mem;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE"' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done
##
#        rm -f ${files}*
        save_final_output $varnew $output
 done # loop over variables 
}



# for maximum and minimum temperature (manipulate daily data files)
function maxmin(){
for VAR in ${VAR_LST_MXMN[@]}; do
 new_name $VAR
 output=${VAR}_${SDATE}.nc
 cp $DATADIR/${EXPID}/daily/$VAR/${VAR}_${SDATE}_*.nc.gz .
 gunzip ${VAR}_${SDATE}_*.nc.gz 
 SDATE1=`echo ${SDATE}|cut -c1-6`
 cdo timmean ${VAR}_${SDATE}_${SDATE1}.nc ${output} ; rm ${VAR}_${SDATE}_${SDATE1}.nc
 files=`ls ${VAR}_${SDATE}_*.nc` 
 for f in $files;do
  cdo timmean $f toto.nc;rm $f
  ncrcat -O -h ${output} toto.nc ${output};rm toto.nc
 done # loop for files
 ncrename -h -d lev,ensemble ${output}
 ncrename -O -h -v lev,kaka ${output} #delete lev var
 ncks -O -h -x -v kaka ${output} ${output} #delete lev var
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
for att in GRID_TYPE ; do 
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

# create a script to change the EXPID, insitutution, ensember, source and realiazation 
	i=0 # index
	for mem in ${LISTMEMB[@]}; do
cat>modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$EXPID";realization($i)=$mem;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE"' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done
##

    save_final_output $varnew $output
done # loop for variables 
}
####  End of the User Defined Functions  #### 




###################################
####  Main Part of the Script  ####
###################################

# NCO and CDO must be available in $PATH

date

config_file=$1
check_args $@ 
#read config_file
. ${config_file}
ENSEMBLE=${#MEM_LST[@]}
#rm -rf ${WORKDIR}
mkdir -p ${WORKDIR}
if [[ ! -d ${WORKDIR} ]]; then
 exit 1
fi

cd ${WORKDIR}

base_path=${DATADIR}/${EXPID}/${SDATE}
mkdir -p ${SAVEDIR}/${EXPID}; # chmod -R 775 $SAVEDIR/${EXPID} 


LISTMEMB=(`echo ${MEM_LST[@]} | sed -e 's/fc//g'`) #member list without "fc"
get_leadtime
header $SDATE
extract
if [ -z ${VAR_LST_2D[@]}  ]; then
 GG=`ls *GG* | head -1`
 read_vars $GG GG
 SH=`ls *SH* | head -1`
 read_vars $SH SH
rm /scratch/${USER}/pp/VAR_LST_2D.txt 
VAR_LST_2D=`echo ${VAR_LST_2D_GG} ${VAR_LST_2D_SH}`
echo $VAR_LST_2D >> /scratch/${USER}/pp/VAR_LST_2D.txt
rm /scratch/${USER}/pp/VAR_LST_3D.txt 
VAR_LST_3D=`echo ${VAR_LST_3D_GG} ${VAR_LST_3D_SH}`
else
 VAR_LST_3D_SH_DEFAULT='T U V W Z'
 VAR_LST_3D_GG_DEFAULT='Q CC CIWC CLWC'
 VAR_LST_2D_GG_DEFAULT='T2M D2M SSTK MSL PRECIP SSR STR TTR TSR TSRC TTRC SLHF SSHF U10M V10M SSRD CP SF E SSRU SSRC STRU STRD TCC'
#if list of variables read from config_file, separation between GG and SH variables
 for var in ${VAR_LST_3D[@]}
 do
  for var_sh in ${VAR_LST_3D_SH_DEFAULT[@]} 
  do
   [ $var == $var_sh ] && VAR_LST_3D_SH=`echo $VAR_LST_3D_SH $var`
  done
  for var_gg in ${VAR_LST_3D_GG_DEFAULT[@]}
  do
   [ $var == $var_gg ] && VAR_LST_3D_GG=`echo $VAR_LST_3D_GG $var`
  done
 done  
 for var in ${VAR_LST_2D[@]}
 do
  for var_gg in ${VAR_LST_2D_GG_DEFAULT[@]}
  do
   [ $var == $var_gg ] && VAR_LST_2D_GG=`echo $VAR_LST_2D_GG $var`
  done
 done 
fi

surface

combine_3d
regrid2x2
upper


if [[ ${#VAR_LST_MXMN[@]} > 0 ]]; then
 maxmin
fi

cd; rm -rf $WORKDIR # clean up

date
####  End of the Main Part of Script  ####
