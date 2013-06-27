#!/bin/bash
set -evx

#################################
####  User Defined Funtions  #### 
#################################




# check if args are ok and read options in config_file

 if [ $# -ne 1 ] ; then
  echo
  echo "USAGE: config_file "
  echo "For example: ./ocean_pp.new.bash /home/$user/cfu_git/autosubmit/pp/ocean/config_file "
  echo
  exit 1
 fi

config_file=$1
. ${config_file}

list_files=''
if [[ ${listpost[@]} =~ "3dtemp" ]] || [[ ${listpost[@]} =~ "3dsal" ]]; then
    echo "The list of diags contains 3dtemp or 3dsal"
    list_files=$(echo ${list_files} grid_T)
fi
if [[ ${listpost[@]} =~ "psi" ]]; then
    echo "The list of diags contains psi"
    list_files=$(echo ${list_files} grid_U grid_V)
fi
if [[ ${listpost[@]} =~ "moc" ]]; then
    echo "The list of diags contains moc"
    list_files=$(echo ${list_files} grid_V)
fi

if [[ ${listpost[@]} =~ "ice" ]]; then
    echo "The list of diags contains ice"
    list_files=$(echo ${list_files} icemod)
fi


###############################################################################
#
# moc needs to be computed before max_moc and area_moc
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if [[ ${listpost[@]##*moc*} != ${listpost[@]} ]] || [[ ${listpost[@]##*stc*} != ${listpost[@]}  ]] ; then
  if [[ ${listpost[@]#moc} != ${listpost[@]:1} ]] ; then
    listpost=( 'moc' "${listpost[@]#moc}" )
  fi
fi
#
# 3d interpolation required before average T sections over longitudes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if [[ ${listpost[@]##TSec_ave*} != ${listpost[@]} ]] ; then
  if [[ ${listpost[@]#3dtemp} != ${listpost[@]:1} ]] ; then
    listpost=( '3dtemp' "${listpost[@]#3dtemp}" )
    warning_T=.true.
  fi
fi
if [[ ${listpost[@]##SSec_ave*} != ${listpost[@]} ]] ; then
  if [[ ${listpost[@]#3dsal} != ${listpost[@]:1} ]] ; then
    listpost=( '3dsal' "${listpost[@]#3dsal}" )
    warning_S=.true.
  fi
fi
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#    You have created a function ? If your new diagnostic relies on an already 
#      existing diagnotics, you might need similar lignes to the above ones
#                        Any doubt ---> vguemas@ic3.cat
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#
# Preparing WORKDIR and set of available functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
WORKDIR=/scratch/tmp/post_ocean/$$
mkdir -p $WORKDIR
cd $WORKDIR
source $PATHCOMMONOCEANDIAG/common_ocean_post.txt
#
# Interval of lead months be post-processed
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
case $expid in
  'nemovar_s4'|'nemovar_combine') moni=09 ; syeari=1957 ; syearf=1957 ; insdate=1 ; typeoutput='MMO' ; NEMOVERSION='nemovar_O1L42' ;;
  'glorys2v1') moni=01 ; syeari=1993 ; syearf=1993 ; insdate=1 ; typeoutput='MMO' ;;
esac
case $expid in
    'nemovar_s4') rootout='/cfunas/exp/ECMWF/NEMOVAR_S4/monthly_mean' ;;
    'nemovar_combine') rootout='/cfunas/exp/ECMWF/NEMOVAR_COMBINE/monthly_mean' ;;
    'glorys2v1') rootout='/cfunas/exp/MERCATOR/GLORYS2V1/monthly_mean';;
esac
if [[ ${listpost[@]##max_moc} != ${listpost[@]} ]] || [[ -z "$ltimef" ]] || [[ -z "$ltime0" ]] ; then 
  if [[ ! -z "$year0" ]] && [[ ! -z "$yearf" ]] ; then
    ltime0=$(((${year0}-${syeari})*12+1))
    ltimef=$(((${yearf}-${syeari}+1-(10#$moni+10)/12)*12))
  else
    ltime0=$((((ltime0-1)/12)*12+1))
    ltimef=$((((ltimef+11)/12)*12))
  fi
fi
mon0=$(( (10#$moni+$ltime0-2)%12+1 ))
monf=$(( (10#$moni+$ltimef-2)%12+1 ))
#
# Loop on start dates 
# ~~~~~~~~~~~~~~~~~~~~
for ((yeari=$syeari;yeari<=$syearf;yeari=$(($yeari+intsdate)))) ; do
  #
  # Interval of years to be post-processed
  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  year0=$(($yeari+(10#$moni+$ltime0-2)/12))
  yearf=$(($yeari+(10#$moni+$ltimef-2)/12))
     
  for memb in ${listmemb[@]} ; do
    #
    # Fetching the files on cfunas
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    case $expid in 
      'nemovar_s4'|'nemovar_combine') get_nemovar ${expid} ${memb} ${year0} ${yearf} ${mon0} ${monf} "${list_files}"
      ;;
      'glorys2v1') get_glorys ${year0} ${yearf} ${mon0} ${monf} ;;
      *) freqout=${rootout:${#rootout}-12} ; freqout=${freqout/_mean} ; freqout=${freqout/*\/}
      get_diagsMMO ${yeari}${moni}01 ${expid} ${memb} $ltime0 $ltimef $chunklen $mod $typeoutput $freqout "${list_files}"
    esac
    #  
    # Ready for the post-processing
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for post in ${listpost[@]} ; do
       
      case $post in
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#  You have created a function ? Enter its call right here under the flag chosen
#              Remember to consider both 'MMO' and 'diags' cases
#                        Any doubt ---> vguemas@ic3.cat
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        'ext_raw_oce')
          if [[ $typeoutput == 'MMO' ]] ; then
            lstvars=`cdo showvar grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc`
            if [[ $raw_vars_ocean == '' ]] ; then
               lstext=`echo $lstvars | sed s/\ /,/g`
            else
             if [[ $raw_vars_ocean == 'default' ]] ; then
              lstextvar=( 'sosstsst' 'sosaline' 'somixhgt' 'somxl010' )
              lstext=''
              for varex in ${lstextvar[@]} ; do
               if [[ ${lstvars/${varex}/} != ${lstvars} ]] ; then
                 lstext=`echo ${lstext} ${varex}|sed s/\ /,/g`
               fi
              done         
             else
              lstext=$raw_vars_ocean
             fi
            fi
               
            ncks -O -v ${lstext} grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc oce_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          else 
            cp sstsssmld_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc oce_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;

        'ext_raw_ice')
          if [[ $typeoutput == 'MMO' ]] ; then
            lstvars=`cdo showvar icemod_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc`
            if [[ $raw_vars_ice == '' ]] ; then
               lstext=`echo $lstvars | sed s/\ /,/g`
            else
             if [[ $raw_vars_ice == 'default' ]] ; then
            lstextvar=( 'isnowthi' 'iicethic' 'ileadfra' 'iicetemp' 'ice_pres' )
            lstext=''
            for varex in ${lstextvar[@]} ; do
              if [[ ${lstvars/${varex}/} != ${lstvars} ]] ; then
                lstext=`echo ${lstext} ${varex}|sed s/\ /,/g`
              fi
            done
            else
              lstext=$raw_vars_ice
             fi
            fi

            ncks -O -v ${lstext} icemod_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ice_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;
       
        'heat_sal_mxl')
          if [[ $typeoutput == 'MMO' ]] ; then
            if [ ! -f heat_sal_mxl_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] ; then
            heat_sal_mxl grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc heat_sal_mxl_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
           fi
          fi
        ;;

        'psi')
          if [[ $typeoutput == 'MMO' ]] ; then
            if [ ! -f psi_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] ; then
            psi grid_U_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc grid_V_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc psi_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 
           fi
          fi        
        ;;

        'usalc')
          if [[ $typeoutput == 'MMO' ]] ; then
           if [ ! -f sal_300-5400m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] ; then
            vertmeansal grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 300 5400 sal_300-5400m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
           fi
          fi
        ;;
      
        'lmsalc')
          if [[ $typeoutput == 'MMO' ]] ; then
           if [ ! -f sal_0-300m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] ; then
            vertmeansal grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0 300 sal_0-300m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
           fi
          fi      
        ;;

        'ohc_specified_layer')
          if [ ! -f ohc_2d_avg_0-300m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ];then
          case $typeoutput in
           'MMO' ) pref='grid_T' ;;
           'diags') pref='t3d' ;;
          esac
          ohc_specified_layer ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 300.0 ohc_2d_avg_0-300m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          ohc_specified_layer ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 300.0 800.0 ohc_2d_avg_300-800m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;
 
        'vert_Tsections')
          case $typeoutput in
           'MMO' ) pref='grid_T' ;;
           'diags') pref='t3d' ;;
          esac
          for coord in 0 45 -45 -30 180 80
           do
            if [[ $coord == '0' ]] || [[ $coord == '45' ]] || [[ $coord == '-45' ]] ; then  
             [[ ` echo $coord | cut -b 1 ` == '-' ]] && direction=S || direction=N
             z_m=Z 
            else
             [[ ` echo $coord | cut -b 1 ` == '-' ]] && direction=W || direction=E
             z_m=M
            fi
             coord=`echo $coord | sed -e s/-//g`
            [ ! -f temp_${coord}${direction}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] && cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper $z_m $coord temp_${coord}${direction}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
           done
 
        ;;

        'vert_Ssections')
          if [[ $typeoutput == 'MMO' ]] ; then
           pref='grid_T'
           for coord in 0 45 -45 -30 180 80
            do
             if [[ $coord == '0' ]] || [[ $coord == '45' ]] || [[ $coord == '-45' ]] ; then  
              [[ ` echo $coord | cut -b 1 ` == '-' ]] && direction=S || direction=N
              z_m=Z 
             else
              [[ ` echo $coord | cut -b 1 ` == '-' ]] && direction=W || direction=E
              z_m=M
             fi
              coord=`echo $coord | sed -e s/-//g`
             [ ! -f sal_${coord}${direction}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] && cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc vosaline $z_m $coord sal_${coord}${direction}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
            done
          fi
        ;;
        '3dtemp')
          case $typeoutput in
           'MMO' ) pref='grid_T' ;;
           'diags') pref='t3d' ;;
          esac
          if [ ! -f regular3dT_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ]; then
             echo " Warning: you are about to perform a 3d interpolation "
             [ $warning_T ] && echo "(because you asked for cross sections calculations)"
             echo "this might take time to complete (~days), be sure you really need/want to do this..."
             interp3d ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper regular3dT_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;
        '3dsal')
          if [[ $typeoutput == 'MMO' ]] ; then
           pref='grid_T' 
          if [ ! -f regular3dS_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ]; then
             echo " Warning: you are about to perform a 3d interpolation "
             [ $warning_S ] && echo "(because you asked for cross sections calculations)"
             echo "this might take time to complete (~days), be sure you really need/want to do this..."
             interp3d ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc vosaline regular3dS_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
          fi
        ;;

        'TSec_ave190-220E')
          [ ! -f TSec_ave190-220E_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] && cdo zonmean -sellonlatbox,190,220,-90,90 regular3dT_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc TSec_ave190-220E_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;        
        'SSec_ave190-220E')
         if [[ $typeoutput == 'MMO' ]] ; then
          [ ! -f SSec_ave190-220E_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] && cdo zonmean -sellonlatbox,190,220,-90,90 regular3dS_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc SSec_ave190-220E_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
         fi
        ;;        

        'moc')
        if [[ $typeoutput == 'MMO' ]] ; then
         if [ ! -f moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ] ; then 
          moc grid_V_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
         fi
        fi
        ;;

        'max_moc')
          max_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 38 50 500 2000 max_moc_38N50N_500m-2km_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          max_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 40 40 0 10000 max_moc_40N_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;
   
        'stc')
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 25.0 NPac_stc_0N25N_0-200m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 200.0 zomsfpac
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc -25.0 0.0 SPac_stc_25S0S_0-200m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 200.0 zomsfpac
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 25.0 NAtl_stc_0N25N_0-200m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 200.0 
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc -25.0 0.0 SAtl_stc_25S0S_0-200m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 200.0 
        ;;

        'area_moc')
         if [ ! -f  moc_40N55N_1-2km_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ];then
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 40.0 55.0 moc_40N55N_1-2km_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
         fi
         if [ ! -f  moc_30N40N_1-2km_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ];then
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 30.0 40.0 moc_30N40N_1-2km_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
         fi
        ;;
 
        'siasiesiv' )

         if [ ! -f siasiesiv_N_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ]||[ ! -f siasiesiv_S_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ];then #check if ? instead of N or S works
          case $typeoutput in
           'MMO' ) pref='icemod' ;;
           'diags') pref='ice' ;;
          esac
          siasiesiv ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc tmp.nc
          mv ice_N_tmp.nc siasiesiv_N_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 
          mv ice_S_tmp.nc siasiesiv_S_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
         fi
        ;;

      esac
   
      case `echo $post|cut -c$((${#post}-2))-${#post}` in
        'ohc')
          case `echo $post | cut -c1` in
           'x') kmin=0 ; kmax=0 ; start=2 ; mxl=1 ;;
           'l') start=2 ; mxl=0
               case $NEMOVERSION in
               'Ec2.3_O1L42'|'N3.2_O1L42'|'nemovar_O1L42') kmin=25 ; kmax=42 ;;
               'Ec3.0_O1L46'|'Ec3.0_O25L46'|'N3.3_O1L46') kmin=23 ; kmax=46 ;;
               'Ec3.0_O1L75'|'Ec3.0_O25L75'|'glorys2v1_O25L75') kmin=45; kmax=75;;
              esac
              ;;
           'm') start=2 ; mxl=0
              case $NEMOVERSION in
               'Ec2.3_O1L42'|'N3.2_O1L42'|'nemovar_O1L42') kmin=21 ; kmax=24 ;;
               'Ec3.0_O1L46'|'Ec3.0_O25L46'|'N3.3_O1L46') kmin=18 ; kmax=22 ;;
               'Ec3.0_O1L75'|'Ec3.0_O25L75'|'glorys2v1_O25L75') kmin=35; kmax=44;;
              esac
              ;;
           'u') kmin=1 ; start=2 ; mxl=0
              case $NEMOVERSION in
               'Ec2.3_O1L42'|'N3.2_O1L42'|'nemovar_O1L42') kmax=20 ;;
               'Ec3.0_O1L46'|'Ec3.0_O25L46'|'N3.3_O1L46') kmax=17 ;;
               'Ec3.0_O1L75'|'Ec3.0_O25L75'|'glorys2v1_O25L75') kmax=34;;
              esac
             ;;
            *)  kmin="" ; kmax="" ; start=1 ; mxl=0 ;;
          esac
          case `echo $post | cut -c${start}-$((start+3))` in
           'ohc') basin='Glob' ;;
            *) basin=`echo $post | cut -c${start}-$((start+3))`
          esac
          case $typeoutput in
           'MMO' ) pref='grid_T' ;;
           'diags') 
             pref='t3d' 
             ncks -A -v somxl010,somixhgt sstsssmld_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc t3d_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
           ;;
          esac
          ohc ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc heatc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc $basin $mxl $kmin $kmax
        ;;
      esac

    done

    # Removing the raw output from this start dates and this member
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    clean_diagsMMO ${yeari}${moni}01 ${expid} ${memb} $ltime0 $ltimef $typeoutput "${list_files}"
  done

  # Prepare storage : choose output directory and file name
  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  for post in ${listpost[@]} ; do
    case $post in
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#     You have created a function ? Enter the output directory and the prefix
#                 or your(s) output files under the flag chosen
#                        Any doubt ---> vguemas@ic3.cat
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      'area_moc') dirout='moc'; files=('moc_40N55N_1-2km' 'moc_30N40N_1-2km') ;;
      'stc') dirout='moc' ; files=( 'NPac_stc_0N25N_0-200m' 'SPac_stc_25S0S_0-200m' 'NAtl_stc_0N25N_0-200m' 'SAtl_stc_25S0S_0-200m' ) ;; 
      'max_moc') dirout='moc' ; files=('max_moc_38N50N_500m-2km' 'max_moc_40N' ) ;;
      'siasiesiv' ) dirout='ice' ; files=('siasiesiv_N' 'siasiesiv_S') ;;
      'moc') dirout='moc' ; files=('moc') ;;
#      'ext_raw_ice') dirout='ice' ; files=('ice_raw') ;;
#      'ext_raw_oce') dirout='oce_raw' ; files=('oce_raw') ;;
      'ext_raw_ice') dirout='ice' ; files=('ice') ;;
      'ext_raw_oce') dirout='oce' ; files=('oce') ;;
      'heat_sal_mxl') dirout='heatc' ; files=('heat_sal_mxl') ;;
      'psi') dirout='psi' ; files=('psi') ;;
      'usalc') dirout='saltc' ; files=('sal_0-300m') ;;
      'lmsalc') dirout='saltc' ;  files=('sal_300-5400m') ;;
      'ohc_specified_layer') dirout='heatc' ; files=('ohc_2d_avg_0-300m' 'ohc_2d_avg_300-800m') ;;
      'vert_Tsections') dirout='sections' ; files=('temp_0N' 'temp_45N' 'temp_45S' 'temp_30W' 'temp_80E' 'temp_180E') ;;
      'vert_Ssections') dirout='sections' ; files=('sal_0N' 'sal_45N' 'sal_45S' 'sal_30W' 'sal_80E' 'sal_180E') ;;
      '3dtemp') dirout='InterpT' ; files=('regular3dT') ;;
      '3dsal') dirout='InterpS' ; files=('regular3dS') ;;
      'TSec_ave190-220E') dirout='sections' ; files=('TSec_ave190-220E') ;;
      'SSec_ave190-220E') dirout='sections' ; files=('SSec_ave190-220E') ;;
    esac
    case `echo $post|cut -c$((${#post}-2))-${#post}` in
      'ohc') 
        dirout='heatc'
        file='heatc'
        case `echo $post | cut -c1` in
         'x') mxl=1 ; start=2 ;;
         'l') start=2 ; mxl=0
             case $NEMOVERSION in
             'Ec2.3_O1L42'|'N3.2_O1L42'|'nemovar_O1L42') file='800-5350_'${file} ;;
             'Ec3.0_O1L46'|'Ec3.0_O25L46'|'N3.3_O1L46') file='855-5875_'${file} ;;
             'Ec3.0_O1L75'|'Ec3.0_O25L75'|'glorys2v1_O25L75') file='857-5902_'${file};;
            esac
            ;;
         'm') start=2 ; mxl=0 
            case $NEMOVERSION in
             'Ec2.3_O1L42'|'N3.2_O1L42'|'nemovar_O1L42') file='373-657_'${file} ;;
             'Ec3.0_O1L46'|'Ec3.0_O25L46'|'N3.3_O1L46') file='382-735_'${file} ;;
             'Ec3.0_O1L75'|'Ec3.0_O25L75'|'glorys2v1_O25L75') file='301-773_'${file};;
            esac
            ;;
         'u') start=2 ; mxl=0 
            case $NEMOVERSION in
             'Ec2.3_O1L42'|'N3.2_O1L42'|'nemovar_O1L42') file='0-315_'${file} ;;
             'Ec3.0_O1L46'|'Ec3.0_O25L46'|'N3.3_O1L46') file='0-322_'${file} ;;
             'Ec3.0_O1L75'|'Ec3.0_O25L75'|'glorys2v1_O25L75') file='0-271_'${file};;
            esac
            ;;
          *) mxl=0 ; start=1 ;;
        esac
 
        case `echo $post | cut -c${start}-$((start+3))` in
         'NAtl') file='NAtl_10N65N_'${file} ;;
         'TAtl') file='TAtl_30S30N_'${file};;
         'NPac') file='NPac_10N70N_'${file} ;;
         'TPac') file='TPac_30S30N_'${file} ;;
         'Arct') file='Arc_65N90N_'${file} ;;
         'Anta') file='Ant_90S60S_'${file} ;;
         'TInd') file='TInd_30S30N_'${file} ;;
        esac 
        if [[ $mxl == 1 ]] ; then
          file='mxl_'$file 
        fi
        files=( $file ) 
    esac
    pathout=${rootout}/${dirout}
    mkdir -m ug+w -m o-w -p $pathout
    for file in ${files[@]} ; do
      prefix=${file}_${expid}_${yeari}${moni}01_fc
      lsmbso=0-${listmemb[${#listmemb[@]}-1]}
      #
      # Merging the post-processed members together and with the previous members if existing
      # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      lsyrsh=${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
      lsmbsh=${listmemb[0]}-${listmemb[${#listmemb[@]}-1]}
      lsmbsb=0-$((${listmemb[0]}-1))
      if [ -e ${pathout}/${prefix}${lsmbsb}_${lsyrsh} ] ; then
        cp ${pathout}/${prefix}${lsmbsb}_${lsyrsh} .
        lsmbsh=0-${listmemb[${#listmemb[@]}-1]}
      fi
      gather_memb ${prefix} _${lsyrsh} ${prefix}${lsmbsh}_${lsyrsh}
      for jmemb in ${listmemb[@]} ; do
        rm -f ${prefix}${jmemb}_${lsyrsh}
      done
      #
      # Concatenating the result with the previous years if existing
      # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#     You have created a function ? If your diagnostic provides yearly output
#       you need to use the concat option rather than the ncrcat one below.
#                        Any doubt ---> vguemas@ic3.cat
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      lsyrsb=${yeari}${moni}_$((year0-(1-(10#$moni+10)/12)))$(printf "%02d" $(((mon0-13)%12+12)) ).nc
      lsyrso=${yeari}${moni}_${yearf}$(printf "%02d" ${monf}).nc
      if [ -e ${pathout}/${prefix}${lsmbsh}_${lsyrsb} ] ; then
        case $post in 
          'max_moc' ) concat ${pathout}/${prefix}${lsmbsh}_${lsyrsb} ${prefix}${lsmbsh}_${lsyrsh} $(printf "%02d" ${monf}) ${prefix}${lsmbsh}_${lsyrso} ;;
          *) ncrcat -O ${pathout}/${prefix}${lsmbsh}_${lsyrsb} ${prefix}${lsmbsh}_${lsyrsh} ${prefix}${lsmbsh}_${lsyrso} ;;
        esac
      else
        lsyrso=$lsyrsh
      fi
      #
      # Merging the result with the previous members if existing
      # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      if [ $lsyrsh != $lsyrso ] && [ -e ${pathout}/${prefix}${lsmbsb}_${lsyrso} ] ; then
        cp ${pathout}/${prefix}${lsmbsb}_${lsyrso} .
        gather_memb ${prefix} _${lsyrso} ${prefix}${lsmbso}_${lsyrso}
      else
        lsmbso=$lsmbsh
      fi
      #
      # Storing and cleaning
      # ~~~~~~~~~~~~~~~~~~~~~   
      cp ${prefix}${lsmbso}_${lsyrso} ${pathout}/. || { if [ -e ${pathout}/${prefix}${lsmbso}_${lsyrso} ];
        then
            echo "${prefix}${lsmbso}_${lsyrso} already exists in ${pathout}"
            sleep 5
        else
            echo " problem writing file in ${pathout} directory"
            exit
        fi
        }
      rm -f ${pathout}/${prefix}${lsmbsh}_${lsyrsb} ${prefix}${lsmbsh}_${lsyrso} ${prefix}${lsmbsb}_${lsyrso} ${pathout}/${prefix}${lsmbsb}_${lsyrso} ${prefix}${lsmbso}_${lsyrso} ${pathout}/${prefix}${lsmbsb}_${lsyrsh} ${prefix}${lsmbsb}_${lsyrsh}
    done
  done
done
rm -rf $WORKDIR
