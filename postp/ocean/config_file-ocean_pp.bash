#!/bin/bash
#This is an example of a configuration_file needed to launch ocean_pp_new.bash. For any other information about how to use it, you can refer to the cfu wiki

listpost=(  )          # Beware that the max_moc diagnostics can not be computed
#                        if you don't process complete years (that's a 
#                        diagnostic computed from annual means ('siasiesiv' 'ohc' 'moc' 'max_moc' 'area_moc' 'ext_raw_ice' (previously 'ice') 'ext_raw_oce' (previously 'sstsssmld') 'heat_sal_mxl' 'psi' 'usalc' 'lmsalc' 'uohc' 'mohc' 'lohc' 'xohc' 'ohc_specified_layer' 'stc' 'vert_Tsections' 'vert_STsections' (new)'3dtemp' '3dsal'(new) 'TSec_ave190-220E' 'SSec_ave190-220E'(new) 'NAtlohc' 'xNAtlohc' 'uNAtlohc' 'mNAtlohc' 'lNAtlohc' 'NPacohc' 'xNPacohc' 'uNPacohc' 'mNPacohc' 'lNPacohc' 'TAtlohc' 'xTAtlohc' 'uTAtlohc' 'mTAtlohc' 'lTAtlohc' 'TPacohc' 'xTPacohc' 'uTPacohc' 'mTPacohc' 'lTPacohc' 'TIndohc'  'xTIndohc' 'uTIndohc' 'mTIndohc' 'lTIndohc' 'Antaohc' 'xAntaohc' 'uAntaohc' 'mAntaohc' 'lAntaohc' 'Arctohc'  'xArctohc' 'uArctohc' 'mArctohc' 'lArctohc' ) 
raw_vars_ocean=(   )    # If listpost=ext_raw_oce, variables to be treated. If nothing specified, all variables present in input file will be treated. If raw_vars='default', sosstsst, sosaline, somixhgt and somxl010 will be extracted.
raw_vars_ice=(   )      # If listpost=ice, variables to be treated. If nothing specified, all variables will be treated. If raw_vars='default', isnowthi, iicethic, ileadfra, iicetemp, ice_pres will be extracted.
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
NEMOVERSION=Ec2.3_O1L42 # NEMO version
# Valid options : Ec2.3_O1L42      for Ec-Earth 2.3 ORCA1    L42
#                 Ec3.0_O1L46      for Ec-Earth 3.0 ORCA1    L46
#                 Ec3.0_O25L46     for Ec-Earth 3.0 ORCA0.25 L46
#                 N3.2_O1L42       for Nemo     3.2 ORCA1    L42
#                 N3.3_O1L46       for Nemo     3.3 ORCA1    L42
#                 nemovar_O1L42    for Nemo     COMBINE and ORAS4 ORCA1L42
#                 === Development in progress : ===
#                 glorys2v1_O25L75 for Nemo     GLORYS2v1    ORCA025L75
#                 ucl_O2L31        for Nemo     UCL          ORCA2L31
PATHCOMMONOCEANDIAG='/home/'${USER}'/autosubmit/postp/ocean'
CON_FILES='/cfu/autosubmit/con_files'
rootout='/cfunas/exp/'${mod}'/'${expid}'/monthly_mean'

