#!/bin/bash
#
# nohup ./nccf_atm_daily.sh expid startdate >& expid-startdate.log &
#
# This script will extract variabls from EC-Earth daily atmospheric output 
# which is available in ICMGG* & ICMSH* files, save each variable in one file 
# and also combine members together. It will modify the header informaton 
# of the generated files according to CMIP5 standard and the variable names 
# will be modified according PCMDI standard variable names.
#
# Written by Hui Du
#
# Institut Català de Ciències del Clima / Climate Forecasting Unit (IC3/CFU)
# Created:  February 22, 2010

set -xv

##################################
####  User Defined Variables  #### 
##################################

VERSION=3
INSTITUTION="IC3            "
SOURCE="EC-Earth3,GLORYS2v1,ERA40/Int,Atm_SV+O pert" # loaded from database (max length 60 char's)
VAR_LST="T2M SST MSL PRECIP SSR STR SLHF SSHF D2M U10M V10M SD SSRD STRD TTR TSR E STL1 TCC T U V Z Q MX2T MN2T"
LEVEL_LST="92500,85000,70000,60000,50000,20000,10000,5000,1000"
MEM_LST=( fc0 )
ENSEMBLE=${#MEM_LST[@]}
DATADIR=/media/nas_data/cfu/exp                # where ICMGG* & ICMSH* files located
SAVEDIR=/cfunas/exp/ecearth                    # for Saving outputs
HEAD_DIR=/cfu/pub/scripts/postp_ecearth/header # some of the header information
WORKDIR=/scratch/${USER}/nccf_atm_daily_$$     # working dir
NFRP=3 # ecearth output frequency (hours), this is for computing the accumulated precipitation 
       # and flux variables (solar and thermal radiation, sensible and latent fluxes)
FACTOR=$((NFRP*3600))           # 3600 (seconds per hour)
HOUR_LST="00,06,12,18"
HOUR_LST_3D="00,12"
INTERVAL=6                      # frequence to save daily data, 6: every 6 hours, 3: every 3 hours, 12: every 12 hours
INTERVAL_3D=12                  # frequence to save daily data, 6: every 6 hours, 3: every 3 hours, 12: every 12 hours
INTERVAL_MXMN=24                # frequence to save daily data, 6: every 6 hours, 3: every 3 hours, 12: every 12 hours
REFTIME_UNIT=day                # time since 1950-01-01
TABLE=table_of_variable_6hourly
#####  End of User Defined Dariables  ####


##################################
####  User Defined Functions  #### 
##################################

# check if args are ok
function check_args(){
	# if [ $# -ne 2 ]; then
	if [ $# -lt 2 ]; then
		echo
		echo "USAGE: $(basename $0) <exp_id> <startdate> >"
		echo " Please keep in mind that this will deal with the grib files of all the leading months, it will take a long time to finish"
		echo
		exit 1
	fi
}

# calculate the reference time (in days) since 1950-01-01
function get_reftime(){
	yy=`echo $1|cut -c1-4`
	mm=`echo $1|cut -c5-6`
	D1=`date +%s -d "1950-01-01"`
	D2=`date +%s -d "${yy}-${mm}-01"`
	((diff_sec=D2-D1))
	reftime_nday=`echo -| awk -v SECS=$diff_sec '{printf "%d",SECS/(60*60*24)}'`
}

# calculate the reference time (in hours or in days)) since "startdate"
function rtime(){
	date1=$1
	date2=$2
	factor=${REFTIME_UNIT} # h for hour, d for days
	year1=`echo $date1|cut -c1-4`
	month1=`echo $date1|cut -c5-6`
	day1=`echo $date1|cut -c7-8`
	year2=`echo $date2|cut -c1-4`
	month2=`echo $date2|cut -c5-6`
	day2=`echo $date2|cut -c7-8`
	sec1=`date --utc --date "${year1}-${month1}-${day1}" +%s`
	sec2=`date --utc --date "${year2}-${month2}-${day2}" +%s`
	case ${factor} in
		hour)
			factor=3600 # 60*60
		;;
		day)
			factor=86400 # 60*60*24
		;;
	esac
	reftime_value=$(((sec2-sec1)/factor))
}

# calculate the days since 1950-01-01, $1 has to have the format 1960-11 (duplicate of get_reftime() at some extent?)
function day_diff(){
	D1=`date +%s -d "1950-01-01"`
	D2=`date +%s -d "$1-01"`
	((diff_sec=D2-D1))
	nday=`echo -| awk -v SECS=$diff_sec '{printf "%d",SECS/(60*60*24)}'`
}

function header(){
	int=${INTERVAL}
	int=$2
	yy=`echo $1|cut -c1-4`
	mm=`echo $1|cut -c5-6`
	NLT=$(cal $mm $yy |egrep "^[ 0-9][0-9]| [ 0-9][0-9]$" |wc -w)
	
	NLT=$((NLT*24/int))
	
	ncks -h -d ensemble,0,$((ENSEMBLE-1)),1 ${HEAD_DIR}/template.nc toto.nc # select sub member
	cp toto.nc toto1.nc
	
	rtime $sdate ${yy}${mm}01
	leadtime_ini=$((reftime_value*24)) # convert days to hours
	
	leadtime=$((leadtime_ini+int))
	time_bnd1=$leadtime_ini
	time_bnd2=$((leadtime_ini+int))
	ncap2 -O -h -s "leadtime(0)=${leadtime};time_bnd(,0)=${time_bnd1};time_bnd(,1)=${time_bnd2}" toto.nc toto.nc
	for ((i=2;i<=$NLT;i++));do
		leadtime=$((leadtime+int))
		time_bnd1=$time_bnd2
		time_bnd2=$((time_bnd1+int))
		ncap2 -O -h -s "leadtime(0)=${leadtime};time_bnd(,0)=${time_bnd1};time_bnd(,1)=${time_bnd2}" toto1.nc toto1.nc
		ncrcat -O -h toto.nc toto1.nc toto.nc
	done
	mv toto.nc header.nc; rm toto1.nc
	
	rtime 19500101 ${yy}${mm}01
	ncap2 -O -h -s "reftime()=${reftime_value}" header.nc header.nc
}

# function to modify level information
modify_level(){
	# ncap -O -h -s "level_{varnew}=float($2)" $1 $1
	ncatted -O -h -a standard_name,sc,o,c,"height" $1       # standard name
	ncatted -O -h -a long_name,sc,o,c,"reference height" $1 # long name
	ncatted -O -h -a data_type,sc,o,c,"float" $1            # data type
	ncatted -O -h -a units,sc,o,c,"m" $1                    # units
	ncatted -O -h -a axis,sc,o,c,"Z" $1                     # axis
	ncatted -O -h -a positive,sc,o,c,"up" $1
}

leadtime(){
	for ((i=0;i<=$((nt-2));i++)); do
		ncap2 -O -h -s "leadtime($i)=(time($i)+(time($((i+1)))-time($i))/2);time_bnd($i,0)=time($i);time_bnd($i,1)=time($((i+1)))" $1 $1
	done
	
	ncap2 -O -h -s "leadtime($((nt-1)))=((leadtime($((nt-2)))+744));time_bnd($((nt-1)),0)=time($((nt-1)));time_bnd($((nt-1)),1)=(time($((nt-1)))+744)" $1 $1
}

delete_time(){
	ncrename -O -h -v time,kaka $1
	ncks -O -h -x -v kaka $1 $1
}

delete_time_bnd(){
	ncrename -O -h -v time_bnd,kaka $1
	ncks -O -h -x -v kaka $1 $1
}

delete_att(){
	fname=$1
	vname=$2
	attribute=$3
	ncatted -h -a ${attribute},${vname},d,, $fname
}

new_name(){
	case $1 in # rename variable names in model output to the standard names which should be used in post-processed files
		"T2M")
			varnew=tas
			par=167.128
			idx=1
		;;
		"PRECIP")
			varnew=prlr
			par1=142.128 # LSP
			par2=143.128 # CP
			idx=7
		;;
		"SST")
			VAR=SSTK
			varnew=tos
			par=34.128
			idx=10
		;;
		"MSL")
			varnew=psl
			par=151.128
			idx=2
		;;
		"SSR")
			varnew=rss
			par=176.128
			idx=5
		;;
		"STR")
			varnew=rls
			par=177.128
			idx=6
		;;
		"SLHF")
			varnew=hflsd
			par=147.128
			idx=9
		;;
		"SSHF")
			varnew=hfssd
			par=146.128
			idx=8
		;;
		"T")
			varnew=ta
			par=130.128
			idx=11
		;;
		"U")
			varnew=ua
			par=131.128
			idx=12
		;;
		"V")
			varnew=va
			par=132.128
			idx=13
		;;
		"Z")
			varnew=g
			par=129.128
			idx=14
		;;
		"Q")
			varnew=hus
			par=133.128
			idx=23
		;;
		"SSRD")
			varnew=rsds
			par=169.128
			idx=15
		;;
		"STRD")
			varnew=rlds
			par=175.128
			idx=16
		;;
		"D2M")
			varnew=tdps
			par=168.128
			idx=17
		;;
		"U10M")
			varnew=uas
			par=165.128
			idx=18
		;;
		"V10M")
			varnew=vas
			par=166.128
			idx=19
		;;
		"TTR")
			varnew=rst
			par=179.128
			idx=20
		;;
		"TSR")
			varnew=rlut
			par=178.128
			idx=21
		;;
		"SD")
			varnew=snld
			par=141.128
			idx=22
		;;
		"E")
			varnew=evlwr
			par=182.128
			idx=24
		;;
		"STL1")
			varnew=ts
			par=139.128
			idx=25
		;;
		"TCC")
			varnew=clt
			par=164.128
			idx=26
		;;
		"MX2T")
			varnew=tasmax
			par=201.128
			idx=27
		;;
		"MN2T")
			varnew=tasmin
			par=202.128
			idx=28
		;;
	esac
}

# for GG files (surface variables)
function generate_netcdf_surface(){
	echo ${MEM_LST[@]}
	
	yymm=$1 # actual year and month of the reforecasts
	year=`echo $yymm|cut -c1-4`
	month=`echo $yymm|cut -c5-6`
	
	day_diff ${year}-${month}
	echo $nday
	# suffix=${yymm}_6hourly.nc
	
	for mem in ${MEM_LST[@]}; do
		type=GG
		file=ICM${type}${expid}+${yymm}.grb
		filenew=${mem}_${type}.grb
		scp ${DATADIR}/${expid}/${sdate}/${mem}/outputs/${file} ./${filenew}
		
		for varname in ${VAR_LST_2D[@]}; do
			new_name $varname
			output=${mem}_${varnew}.nc
			
			case "$varname" in # for precip, have to add CP and LSP to get total precip
				'PRECIP')
					for par in ${par1} ${par2}; do # par1, LSP (large scale precipitation), par2, CP (convective precipitation)
						gribnew=${par}_${mem} # par1, LSP (large scale precipitation)
						grib_copy -w param=${par} ${filenew} ${gribnew}.grb
						cdo -R -r -t ecmwf -f nc splitvar ${gribnew}.grb ${gribnew}_; rm ${gribnew}.grb
						varname=`ls ${par}_*.nc|cut -f3 -d'_'|cut -f1 -d'.'`
						new_name $varname
						ncrename -h -v $varname,$varnew ${gribnew}_${varname}.nc
						mv ${gribnew}_${varname}.nc ${mem}_${varname}.nc
					done
					cdo  add ${mem}_CP.nc ${mem}_LSP.nc toto.nc ; rm ${mem}_CP.nc ${mem}_LSP.nc # ${mem}_${varnew}.nc # add CP and LSP to get total precipitation
					cdo selhour,03,09,15,21 toto.nc toto03.nc
					cdo selhour,06,12,18,00 toto.nc toto06.nc
					rm toto.nc
					cdo add toto03.nc toto06.nc ${output}
					ncap2 -O -h -s "$varnew=$varnew/21600" ${output} ${output} # convert accumulated values to values per second
				;;
				'MX2T'|'MN2T')
					gribnew=${par}_${mem}
					grib_copy -w param=${par} ${filenew} ${gribnew}.grb
					cdo -R -r -t ecmwf -f nc splitvar ${gribnew}.grb ${gribnew}_; rm ${gribnew}.grb
					varname=`ls ${par}_*.nc|cut -f3 -d'_'|cut -f1 -d'.'`
					new_name $varname
					ncrename -h -v $varname,$varnew ${gribnew}_${varname}.nc
					case $varnew in
						'tasmax')
							cdo timselmax,8 ${gribnew}_${varname}.nc ${output};rm ${gribnew}_${varname}.nc
						;;
						'tasmin')
							cdo timselmin,8 ${gribnew}_${varname}.nc ${output};rm ${gribnew}_${varname}.nc
						;;
					esac
				;;
				'SSR'|'STR'|'SLHF'|'SSHF'|'TSRC'|'TTRC'|'SSRD'|'STRD'|'SSTD'|'TSR'|'TTR'|'TSRC'|'TTRC'|'SSRC'|'STRC'|'E')
					gribnew=${par}_${mem}
					grib_copy -w param=${par} ${filenew} ${gribnew}.grb
					cdo -R -r -t ecmwf -f nc splitvar ${gribnew}.grb ${gribnew}_; rm ${gribnew}.grb
					varname=`ls ${par}_*.nc|cut -f3 -d'_'|cut -f1 -d'.'`
					new_name $varname
					ncrename -h -v $varname,$varnew ${gribnew}_${varname}.nc
					cdo selhour,03,09,15,21 ${gribnew}_${varname}.nc toto03.nc
					cdo selhour,06,12,18,00 ${gribnew}_${varname}.nc toto06.nc
					rm ${gribnew}_${varname}.nc
					cdo add toto03.nc toto06.nc ${output}
					rm toto03.nc toto06.nc
					ncap2 -O -h -s "$varnew=$varnew/21600" ${output} ${output} # convert accumulated values to values per second,for flux variables
				;;
				
				'T2M'|'SST'|'MSL'|'D2M'|'U10M'|'V10M'|'SD'|'STL1'|'TCC')
					gribnew=${par}_${mem}
					grib_copy -w param=${par} ${filenew} ${gribnew}.grb
					cdo -R -r -t ecmwf -f nc splitvar ${gribnew}.grb ${gribnew}_; rm ${gribnew}.grb
					varname=`ls ${par}_*.nc|cut -f3 -d'_'|cut -f1 -d'.'`
					new_name $varname
					cdo selhour,"$HOUR_LST" ${gribnew}_${varname}.nc ${output}; rm ${gribnew}_${varname}.nc
					ncrename -v ${varname},${varnew} ${output}
				;;
				
				'Q')
					gribnew=${par}_${mem}
					grib_copy -w param=${par} ${filenew} ${gribnew}.grb
					cdo -R -r -t ecmwf -f nc splitvar ${gribnew}.grb ${gribnew}_; rm ${gribnew}.grb
					varname=`ls ${par}_*.nc|cut -f3 -d'_'|cut -f1 -d'.'`
					cdo sellevel,${LEVEL_LST} -selhour,"$HOUR_LST_3D" ${gribnew}_${varname}.nc ${output};  rm ${gribnew}_${varname}.nc # select levels and hours
					ncrename -v ${varname},${varnew} ${output}
					ncrename -d lev,level ${output}
					ncrename -v lev,level ${output}
				;;
			esac
		done # loop for variables
		rm $filenew # delete the grib file
	done # loop for members
	
	# combine memebers
	for varname in ${VAR_LST_2D[@]}; do
		new_name $varname
		output=${varnew}_${suffix}.nc
		ncecat -O -h fc?_${varnew}.nc ${output} # combine all members
		rm -f fc?_${varnew}.nc
		ncrename -h -d lon,longitude -v lon,longitude -d record,ensemble ${output}
		ncrename -h -d lat,latitude -v lat,latitude  ${output}
		ncpdq -O -h -a time,ensemble ${output} ${output} # reshape the dimensions as per requirement of final output
		ncatted -O -h -a ,${varnew},d,c, ${output}
		if [ $varnew == hus ];then
			ncks -h -A header_3D.nc ${output}
			delete_att ${output} leadtime bounds
			elif [ $varnew == tasmax ] || [ $varnew == tasmin  ];then
			ncks -h -A header_MXMN.nc ${output}
		else
			ncks -h -A header.nc ${output}
		fi
		case ${varnew} in
			'tas'|'tos'|'psl'|'tdps'|'uas'|'vas'|'snld'|'hus'|'ts'|'clt')
				delete_time_bnd ${output}
			;;
		esac
	done
}

function modify_var(){
	varname=$1
	new_name $varname
	output=${varnew}_${suffix}.nc

	# get the CFU standard attributes to be written in the variable
	variables=`cat ${HEAD_DIR}/${TABLE} | cut -f$idx -d'|' | sed -e 's/ /@/g'`
	cfustandard_name=`echo $variables | cut -f2 -d' ' | sed -e 's/@/ /g'`      # variable standard name
	cfulong_name=`echo $variables     | cut -f3 -d' ' | sed -e 's/@/ /g'`      # variable long name
	cfucell_methods=`echo $variables  | cut -f4 -d' ' | sed -e 's/@/ /g'`      # variable cell methods
	cfuunit=`echo $variables          | cut -f5 -d' ' | sed -e 's/@/ /g'`      # variable unit
	cfuunit_long=`echo $variables     | cut -f6 -d' ' | sed -e 's/@/ /g'`      # variable unit long name
	cfulevel_number=`echo $variables  | cut -f7 -d' ' | sed -e 's/@/ /g'`      # variable level
	cfulevel_type=`echo $variables    | cut -f8 -d' ' | sed -e 's/@/ /g'`      # variable level type
	cfulevel_units=`echo $variables   | cut -f9 -d' ' | sed -e 's/@/ /g'`      # variable level unit
	
	# cell_methods is only needed for accumulative variables
	case ${varnew} in
		'prlr'|'rss'|'rls'|'hflsd'|'hfssd'|'rsds'|'rlds'|'rst'|'rlut'|'evlwr'|'tasmax'|'tasmin')
			ncatted -O -h -a cell_methods,${varnew},o,c,"$cfucell_methods" ${output} # {var}iable cell methods
		;;
	esac

	# adding and modifying the variable attributes
	ncatted -O -h -a _FillValue,${varnew},a,f,1.e+12 ${output}
	ncatted -O -h -a standard_name,${varnew},a,c,"$cfustandard_name" ${output} # {var}iable standard name
	ncatted -O -h -a long_name,${varnew},a,c,"$cfulong_name" ${output}         # {var}iable long name
	ncatted -O -h -a unit_long,${varnew},a,c,"$cfuunit_long" ${output}         # {var}iable long unit name
	ncatted -O -h -a units,${varnew},a,c,"$cfuunit" ${output}                  # {var}iable units
	
	case ${varnew} in
		'tas'|'tos'|'psl'|'tdps'|'uas'|'vas'|'snld'|'hus'|'ts'|'clt')
			# delete_time_bnd ${output}
			delete_att ${output} leadtime bounds
			ncatted -O -h -a coordinates,${varnew},o,c,"longitude latitude reftime leadtime experiment_id source realization institution sc" ${output} # variable coordinates
		;;
		'prlr'|'rss'|'rls'|'hflsd'|'hfssd'|'rsds'|'rlds'|'rst'|'rlut'|'evlwr'|'tasmax'|'tasmin')
			ncatted -O -h -a coordinates,${varnew},o,c,"longitude latitude reftime time_bnd leadtime experiment_id source realization institution sc" ${output}
	esac
	
	case ${varnew} in
		'prlr'|'rss'|'rls'|'hflsd'|'hfssd'|'rsds'|'rlds'|'rst'|'rlut'|'evlwr'|'tasmax'|'tasmin')
			ncatted -O -h -a cell_methods,${varnew},o,c,"$cfucell_methods" ${output} # {var}iable cell methods
		;;
	esac

	# adding and modifying the 'sc' attributes
	if [[ ${varnew} == clt ]];then
		levelname=level
	else
		levelname=sc
	fi
	
	ncap2 -s ${levelname}="$cfulevel_number" ${output} -h -O ${output}
	
	ncatted -O -h -a data_type,${levelname},o,c,"$cfulevel_type" ${output}   # variable level type
	ncatted -O -h -a units,${levelname},o,c,"$cfulevel_units" ${output}      # variable level units
	ncatted -O -h -a standard_name,${levelname},c,c,"height" ${output}       # standard name
	ncatted -O -h -a long_name,${levelname},c,c,"reference height" ${output} # long name
	ncatted -O -h -a axis,${levelname},c,c,"Z" ${output}                     # axis
	ncatted -O -h -a positive,${levelname},c,c,"up" ${output}

	# adding variable axis
	ncatted -O -h -a axis,longitude,o,c,"X" ${output}    # variable longitude axis
	ncatted -O -h -a axis,latitude,o,c,"Y" ${output}     # variable latitude axis
	ncatted -O -h -a axis,${levelname},o,c,"Z" ${output} # variable level axis

	# delete history
	ncatted -h -a history,global,d,, $output

	# change institution name
	ncatted -h -a institution,global,m,c,"IC3" $output

	# create a script to change the expid, insitutution, ensember, source and realiazation
	i=0 # index
	for mem in ${MEM_LST[@]}; do
		v=`echo $mem | sed -e 's/fc//g'` # real value of the member without "fc"
cat> modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$expid";realization($i)=$v;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE";reftime()=${reftime_nday}' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done

	# delete time variable
	delete_time $output
}

# for SH files (pressure level variables)
function generate_netcdf_upper(){
	echo ${MEM_LST[@]}
	
	yymm=$1 # actual year and month of the reforecasts
	year=`echo $yymm|cut -c1-4`
	month=`echo $yymm|cut -c5-6`
	
	day_diff ${year}-${month}
	echo $nday
	
	for mem in ${MEM_LST[@]}; do
		type=SH
		file=ICM${type}${expid}+${yymm}.grb
		filenew=${expid}_${sdate}_${mem}_${type}${yymm}.grb
		scp ${DATADIR}/${expid}/${sdate}/${mem}/outputs/${file} ./${filenew}
		
		for varname in ${VAR_LST_3D[@]} ; do
			new_name $varname
			output=${mem}_${varnew}.nc
			grib_copy -w param=${par} ${filenew} toto.grb                         # select grib parameter
			cdo -R -r -t ecmwf -f nc splitvar toto.grb ""; rm toto.grb            # convert to netcdf
			cdo sp2sp,106 ${varname}.nc toto1.nc                                  # reduce resolution
			cdo -r sp2gp toto1.nc toto.nc                                         # interploate to regular grid
			cdo sellevel,${LEVEL_LST} -selhour,00,12 toto.nc ${mem}_${varnew}.nc  # select levels and hours
			ncrename -h -v $varname,$varnew ${mem}_${varnew}.nc
		done # loop for variables
		rm $filenew # delete the grib file
	done # loop for members
	
	# combine memebers
	for varname in ${VAR_LST_3D[@]}; do
		new_name $varname
		output=${varnew}_${suffix}.nc
		ncecat -O -h fc?_${varnew}.nc ${output} # combine all members
		rm -f fc?_${varnew}.nc
		ncrename -d record,ensemble ${output}
		ncrename -d lon,longitude -d lat,latitude -d lev,level ${output}
		ncrename -v lon,longitude -v lat,latitude -v lev,level ${output}
		ncpdq -O -h -a time,ensemble ${output} ${output} # reshape the dimensions as per requirement of final output 
		ncatted -O -h -a ,${varnew},d,c, ${output}
		ncks -h -A header_3D.nc ${output}
		delete_time_bnd ${output}
		delete_att ${output} leadtime bounds
	done
}

function modify_var_upper(){
	var=$1
	new_name $var
	output=${varnew}_${suffix}.nc
	
	# get the CFU standard attributes to be written in the variable
	variables=`cat ${HEAD_DIR}/$TABLE | cut -f$idx -d'|' | sed -e 's/ /@/g'`
	cfustandard_name=`echo $variables | cut -f2 -d' ' | sed -e 's/@/ /g'`    # variable standard name
	cfulong_name=`echo $variables     | cut -f3 -d' ' | sed -e 's/@/ /g'`    # variable long name
	cfucell_methods=`echo $variables  | cut -f4 -d' ' | sed -e 's/@/ /g'`    # variable cell methods
	cfuunit=`echo $variables          | cut -f5 -d' ' | sed -e 's/@/ /g'`    # variable unit
	cfuunit_long=`echo $variables     | cut -f6 -d' ' | sed -e 's/@/ /g'`    # variable unit long name
	cfulevel_number=`echo $variables  | cut -f7 -d' ' | sed -e 's/@/ /g'`    # variable level
	cfulevel_type=`echo $variables    | cut -f8 -d' ' | sed -e 's/@/ /g'`    # variable level type
	cfulevel_units=`echo $variables   | cut -f9 -d' ' | sed -e 's/@/ /g'`    # variable level unit
	
	# modify variable attributes
	ncatted -O -h -a ,${varnew},d,, ${output}
	
	ncatted -O -h -a _FillValue,${varnew},a,f,1.e+12f ${output}
	ncatted -O -h -a standard_name,${varnew},o,c,"$cfustandard_name" ${output} # variable standard name
	ncatted -O -h -a long_name,${varnew},o,c,"$cfulong_name" ${output}         # variable long name
	# ncatted -O -h -a cell_methods,${varnew},o,c,"$cfucell_methods" ${output} # variable cell methods
	ncatted -O -h -a unit_long,${varnew},o,c,"$cfuunit_long" ${output}         # variable long unit name
	ncatted -O -h -a units,${varnew},o,c,"$cfuunit" ${output}                  # variable units
	ncatted -O -h -a data_type,level,o,c,"$cfulevel_type" ${output}            # variable level type
	ncatted -O -h -a units,level,o,c,"$cfulevel_units" ${output}               # variable level units
	# ncatted -O -h -a coordinates,${varnew},o,c,"longitude latitude leadtime reftime time_bnd experiment_id source realization institution level" ${output}
	ncatted -O -h -a coordinates,${varnew},o,c,"longitude latitude leadtime reftime experiment_id source realization institution level" ${output}

	# modify longitude attributes
	lon_min=0
	lon_max=359.25
	lat_min=-89.4270841760375
	lat_max=89.4270841760375  # these valuse shoud be obtaind from the file instead of hardcoded
	
	ncatted -O -h -a axis,longitude,o,c,"X" ${output}                # variable longitude axis
	ncatted -O -h -a topology,longitude,c,c,"circular" ${output}     # variable longitude axis
	ncatted -O -h -a modulo,longitude,c,f,"360" ${output}            # variable longitude axis
	ncatted -O -h -a valid_min,longitude,c,f,"$lon_min" ${output}    # variable longitude valid_min
	ncatted -O -h -a valid_max,longitude,c,f,"$lon_max" ${output}    # variable longitude valid_max

	# modify latitude attributes
	ncatted -O -h -a axis,latitude,o,c,"Y" ${output}                # variable latitude axis
	ncatted -O -h -a valid_min,latitude,c,f,"$lat_min" ${output}    # variable latitude valid_min
	ncatted -O -h -a valid_max,latitude,c,f,"$lat_max" ${output}    # variable latitude valin_max
	
	# modify level attributes
	ncatted -O -h -a standard_name,level,o,c,"air_pressure" ${output} # standard name
	ncatted -O -h -a long_name,level,o,c,"air pressure" ${output}     # long name
	ncatted -O -h -a data_type,level,o,c,"float" ${output}            # data type
	ncatted -O -h -a units,level,o,c,"hPa" ${output}                  # units
	ncatted -O -h -a axis,level,o,c,"Z" ${output}                     # axis
	ncatted -O -h -a positive,level,c,c,"up" ${output}

	# modify the level values, should be hPa instead of Pa
	ncap2 -O -h -s "level()=level()/100" ${output} ${output}
	
	# ncks  -h -A header_3D.nc ${output}
	delete_time $output
	ncatted -h -a history,global,d,, $output            # delete history
	ncatted -h -a institution,global,m,c,"IC3" $output  # change institution name in global attributes
	
	# create a script to change the expid, insitutution, ensember, source and realiazation
	i=0 # index
	for mem in ${MEM_LST[@]}; do
		v=`echo $mem | sed -e 's/fc//g'` # value of the member without "fc"
cat> modify_ncvalue<<EOF
ncap2 -O -h -s 'experiment_id($i,0:3)="$expid";realization($i)=$v;institution($i,0:14)="$INSTITUTION";source($i,0:59)="$SOURCE"' \$1 \$1
EOF
		cat modify_ncvalue
		bash modify_ncvalue $output; rm modify_ncvalue
		i=$((i+1))
	done
}

function modify_header(){
	for varname in ${VAR_LST_2D[@]}; do
		if [[ $varname != 'Q' ]]; then
			modify_var $varname
			save_final_output $varname
		fi
	done # loop for variables
}

function modify_header_3D(){
	for varname in ${VAR_LST_3D[@]}; do
		modify_var_upper $varname
		save_final_output $varname
	done # loop for variables
}

# save final post-processed output (file in *.nc.gz format)
function save_final_output(){
	var=$1
	new_name $var
	output=${varnew}_${suffix}.nc

        tardir=${SAVEDIR}/${expid}/daily/${varnew}/
        mkdir -p $tardir
        find ${SAVEDIR}/${expid}/daily/. -type d | xargs chmod 775 2>/dev/null
        if [ -e ${tardir}/${output}.gz ] ; then
                mv ${output} new_${output}
                ncpdq -O -h -a ensemble,time new_${output} new_${output}        # shape the dimensions
                mv ${tardir}/${output}.gz .
                gunzip ${output}.gz
                mv ${output} old_${output}
                ncpdq -O -h -a ensemble,time old_${output} old_${output}        # shape the dimensions
                ncrcat -O -h old_${output} new_${output} ${output}
                ncpdq -O -h -a time,ensemble ${output} ${output}                # again reshape the dimensions as per requirement of final output
                rm old_${output} new_${output}
        fi
        chmod 770 ${output}
        gzip ${output}
        mv ${output}.gz ${tardir}
}
####  End of the User Defined Functions  #### 


##################################
#### Main Part of the Script  ####
##################################

# GRIB_API, NCO and CDO must be available in $PATH

date

rm -rf ${WORKDIR}
mkdir -p ${WORKDIR}
if [[ ! -d ${WORKDIR} ]]; then
 exit 1
fi
cd ${WORKDIR}

check_args $@

expid=$1
sdate=$2

# seperate and count 2D&3D varaibles
j=1
k=1
for var in ${VAR_LST}; do
        case $var in
                T2M|SST|MSL|PRECIP|SSR|STR|SLHF|SSHF|D2M|U10M|V10M|SD|SSRD|STRD|TTR|TSR|Q|E|STL1|TCC|MX2T|MN2T)
                        VAR_LST_2D[$j]="$var"
                        j=$((j+1))
                ;;
                T|U|V|Z)
                        VAR_LST_3D[$k]="$var"
                        k=$((k+1))
                ;;
        esac
done

# prepare yyyymm list in some file (member is hard-coded here?) 
ls ${DATADIR}/${expid}/${sdate}/fc3/outputs/ICMGG*.grb|cut -f2 -d'+'|cut -c1-6 > yearmonth_lst

# main loop for performing post-processing
cat yearmonth_lst > subset_data
while read line; do
	yyyymm=$line
	suffix=${sdate}_$yyyymm
	get_reftime $yyyymm
	header $yyyymm ${INTERVAL_3D}; mv header.nc header_3D.nc
	header $yyyymm ${INTERVAL_MXMN}; mv header.nc header_MXMN.nc
	header $yyyymm ${INTERVAL}
	
	if [[ ${#VAR_LST_2D[@]} -gt 0 ]]; then
		generate_netcdf_surface  $yyyymm
		modify_header
		if [ -e hus_${suffix}.nc ];then
			modify_var_upper Q
			save_final_output Q
		fi
	fi
	
	if [[ ${#VAR_LST_3D[@]} -gt 0 ]]; then
		generate_netcdf_upper  $yyyymm
		modify_header_3D
	fi
	rm -f ${WORKDIR}/*.nc
done < subset_data

date
####  End of the Main Part of Script  ####
