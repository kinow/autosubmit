#!/bin/bash
set -evx

listpost=(  )          # Beware that the max_moc diagnostics can not be computed
#                        if you don't process complete years (that's a 
#                        diagnostic computed from annual means)
#listpost=('siasiesiv' 'ohc' 'moc' 'max_moc' 'area_moc' 'ice' 'sstsssmld' 'heat_sal_mxl' 'psi' 'usalc' 'lmsalc' 'uohc' 'mohc' 'lohc' 'xohc' 'ohc_specified_layer' 'stc' 'vert_Tsections' '3dtemp' 'TSec_ave190-220E' 'NAtlohc' 'xNAtlohc' 'uNAtlohc' 'mNAtlohc' 'lNAtlohc' 'NPacohc' 'xNPacohc' 'uNPacohc' 'mNPacohc' 'lNPacohc' 'TAtlohc' 'xTAtlohc' 'uTAtlohc' 'mTAtlohc' 'lTAtlohc' 'TPacohc' 'xTPacohc' 'uTPacohc' 'mTPacohc' 'lTPacohc' 'TIndohc'  'xTIndohc' 'uTIndohc' 'mTIndohc' 'lTIndohc' 'Antaohc' 'xAntaohc' 'uAntaohc' 'mAntaohc' 'lAntaohc' 'Arctohc'  'xArctohc' 'uArctohc' 'mArctohc' 'lArctohc' ) 
expid=i00k              # expid or nemovar_s4 / nemovar_combine
mod='ecearth'           # nemo / ecearth
typeoutput='MMO'        # diags / MMO
# Possible options : ( 'siasiesiv' 'ohc' 'moc' 'max_moc' 'area_moc' 'ice' 'sstsssmld' 'heat_sal_mxl' 'psi' 'usalc' 'lmsalc' 'uohc' 'mohc' 'lohc' 'xohc' 'ohc_specified_layer' 'stc' '3dtemp' 'TSec_ave190-220E' 'NAtlohc' 'xNAtlohc' 'uNAtlohc' 'mNAtlohc' 'lNAtlohc' 'NPacohc' 'xNPacohc' 'uNPacohc' 'mNPacohc' 'lNPacohc' 'TAtlohc' 'xTAtlohc' 'uTAtlohc' 'mTAtlohc' 'lTAtlohc' 'TPacohc' 'xTPacohc' 'uTPacohc' 'mTPacohc' 'lTPacohc' 'TIndohc'  'xTIndohc' 'uTIndohc' 'mTIndohc' 'lTIndohc' 'Antaohc' 'xAntaohc' 'uAntaohc' 'mAntaohc' 'lAntaohc' 'Arctohc'  'xArctohc' 'uArctohc' 'mArctohc' 'lArctohc' )
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
listmemb=( 0 1 2 3 4 )  # list of members
syeari=1960             # first start date
syearf=2005             # last start date
moni=11                 # first month of the hindcast
intsdate=1              # interval between start dates
chunklen=4              # length of the chunks (in months)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ltime0=1                # first leadtime to post-process
ltimef=4                # last leadtime to postprocess
# Fill up either ltime0/ltimef or year0/yearf
year0=                  # first year to post-process in the fist start date
yearf=                  # last year to post-process in the fist start date
# If you fill up the year argument, complete years will be processed, year by
# year from moni 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
NEMOVERSION=v2.2            # NEMO version
PATHCOMMONOCEANDIAG='/home/'${USER}'/autosubmit/postp/ocean'
CON_FILES='/cfu/autosubmit/con_files'
rootout='/cfunas/exp/'${mod}'/'${expid}'/monthly_mean'
# If you post-process daily of monthly means the output directory is daily_mean
# or monthly_mean
# daily means is only tested for nemo currently
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
if [[ ${listpost[@]##Tsec_ave*} != ${listpost[@]} ]] ; then
  if [[ ${listpost[@]#3dtemp} != ${listpost[@]:1} ]] ; then
    listpost=( '3dtemp' "${listpost[@]#3dtemp}" )
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
  'nemovar_s4'|'nemovar_combine') moni=09 ; syeari=1957 ; syearf=1957 ; insdate=1 ; typeoutput='MMO' ; NEMOVERSION='nemovar' ;;
esac
if [[ ${listpost[@]##max_moc} != ${listpost[@]} ]] || [[ ! -z "$ltimef" ]] || [[ ! -z "$ltime0" ]] ; then 
  if [[ -z "$year0" ]] && [[ -z "$yearf" ]] ; then
    ltime0=$(((${year0}-${yeari})*12+1))
    ltimef=$(((${yearf}-${yeari}+1-(10#$moni+10)/12)*12))
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
      'nemovar_s4'|'nemovar_combine') get_nemovar ${expid} ${memb} ${year0} ${yearf}
      case $expid in
        'nemovar_s4') endyear=2012 ;;
        'nemovar_combine') endyear=2009 ;;
      esac
      case $yearf in
        $endyear) monf=5; ltimef=9 ;;
      esac
      ;;
      *) get_diagsMMO ${yeari}${moni}01 ${expid} ${memb} $ltime0 $ltimef $chunklen $mod $typeoutput  
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
        'sstsssmld')
          if [[ $typeoutput == 'MMO' ]] ; then
            ncks -O -v sosstsst,sosaline,somixhgt,somxl010 grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc sstsssmld_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;

        'ice')
          if [[ $typeoutput == 'MMO' ]] ; then
            ncks -O -v isnowthi,iicethic,ileadfra,iicetemp icemod_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc ice_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;
       
        'heat_sal_mxl')
          if [[ $typeoutput == 'MMO' ]] ; then
            heat_sal_mxl grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc heat_sal_mxl_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;

        'psi')
          if [[ $typeoutput == 'MMO' ]] ; then
            psi grid_U_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc grid_V_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc psi_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 
          fi        
        ;;

        'usalc')
          if [[ $typeoutput == 'MMO' ]] ; then
            vertmeansal grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 300 5400 sal_300-5400m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi
        ;;
      
        'lmsalc')
          if [[ $typeoutput == 'MMO' ]] ; then
            vertmeansal grid_T_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0 300 sal_0-300m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          fi      
        ;;

        'ohc_specified_layer')
          case $typeoutput in
           'MMO' ) pref='grid_T' ;;
           'diags') pref='t3d' ;;
          esac
          ohc_specified_layer ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 0.0 300.0 ohc_2d_avg_0-300m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          ohc_specified_layer ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 300.0 800.0 ohc_2d_avg_300-800m_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;
 
        'vert_Tsections')
          case $typeoutput in
           'MMO' ) pref='grid_T' ;;
           'diags') pref='t3d' ;;
          esac
          cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper Z 0 temp_0N_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper Z 45 temp_45N_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper Z -45 temp_45S_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper M -30 temp_30W_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper M 180 temp_180E_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          cutsection ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper M 80 temp_80E_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;

        '3dtemp')
          case $typeoutput in
           'MMO' ) pref='grid_T' ;;
           'diags') pref='t3d' ;;
          esac
          interp3d ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc votemper regular3dT_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;

        'TSec_ave190-220E')
          cdo zonmean -sellonlatbox,190,220,-90,90 regular3dT_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc TSec_ave190-220E_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;        

        'moc')
        if [[ $typeoutput == 'MMO' ]] ; then
          moc grid_V_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
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
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 40.0 55.0 moc_40N55N_1-2km_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
          area_moc moc_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 30.0 40.0 moc_30N40N_1-2km_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;
 
        'siasiesiv' )
          case $typeoutput in
           'MMO' ) pref='icemod' ;;
           'diags') pref='ice' ;;
          esac
          siasiesiv ${pref}_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc tmp.nc
          mv ice_N_tmp.nc siasiesiv_N_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc 
          mv ice_S_tmp.nc siasiesiv_S_${expid}_${yeari}${moni}01_fc${memb}_${year0}$(printf "%02d" ${mon0})_${yearf}$(printf "%02d" ${monf}).nc
        ;;

      esac
   
      case `echo $post|cut -c$((${#post}-2))-${#post}` in
        'ohc')
          case `echo $post | cut -c1` in
           'x') kmin=0 ; kmax=0 ; start=2 ; mxl=1 ;;
           'l') kmin=25 ; kmax=42 ; start=2 ; mxl=0 ;;
           'm') kmin=21 ; kmax=24 ; start=2 ; mxl=0 ;;
           'u') kmin=1 ; kmax=20 ; start=2 ; mxl=0 ;;
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
    clean_diagsMMO ${yeari}${moni}01 ${expid} ${memb} $ltime0 $ltimef $typeoutput
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
      'ice') dirout='ice' ; files=('ice') ;;
      'sstsssmld') dirout='sstsssmld' ; files=('sstsssmld') ;;
      'heat_sal_mxl') dirout='sstsssmld' ; files=('heat_sal_mxl') ;;
      'psi') dirout='psi' ; files=('psi') ;;
      'usalc') dirout='saltc' ; files=('sal_0-300m') ;;
      'lmsalc') dirout='saltc' ;  files=('sal_300-5400m') ;;
      'ohc_specified_layer') dirout='heatc' ; files=('ohc_2d_avg_0-300m' 'ohc_2d_avg_300-800m') ;;
      'vert_Tsections') dirout='sections' ; files=('temp_0N' 'temp_45N' 'temp_45S' 'temp_30W' 'temp_80E' 'temp_180E') ;;
      '3dtemp') dirout='InterpT' ; files=('regular3dT') ;;
      'TSec_ave190-220E') dirout='sections' ; files=('TSec_ave190-220E') ;;
    esac
    case `echo $post|cut -c$((${#post}-2))-${#post}` in
      'ohc') 
        dirout='heatc'
        file='heatc'
        case `echo $post | cut -c1` in
         'x') mxl=1 ; start=2 ;;
         'l') file='800-5350_'${file} ; start=2 ; mxl=0 ;;
         'm') file='373-657_'${file} ; start=2 ; mxl=0 ;;
         'u') file='0-315_'${file}; start=2 ; mxl=0 ;;
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
    mkdir -p $pathout
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
      lsyrsb=${yeari}${moni}_$((year0-${monf}/12))$(printf "%02d" ${monf}).nc
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
      cp ${prefix}${lsmbso}_${lsyrso} ${pathout}/. 
      rm -f ${pathout}/${prefix}${lsmbsh}_${lsyrsb} ${prefix}${lsmbsh}_${lsyrso} ${prefix}${lsmbsb}_${lsyrso} ${pathout}/${prefix}${lsmbsb}_${lsyrso} ${prefix}${lsmbso}_${lsyrso} ${pathout}/${prefix}${lsmbsb}_${lsyrsh} ${prefix}${lsmbsb}_${lsyrsh}
    done
  done
done
rm -rf $WORKDIR
chmod 775 /scratch/tmp/post_ocean
