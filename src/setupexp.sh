#!/bin/bash
# ./setupexp.sh -e $expid

EXPID=chex

while getopts e: option
do
 case $option in
  e) EXPID=$OPTARG;;
  \?) exit 1;;
 esac
done

set -xuve
date

# options and paths required for setting up experiment at HPC
cd /cfu/autosubmit/$EXPID
HPCARCH=`grep -w HPCARCH conf/expdef_${EXPID}.conf | cut -d '=' -f2 |sed 's/ //g'`
HPCPROJ=`grep -w HPCPROJ conf/expdef_${EXPID}.conf | cut -d '=' -f2 |sed 's/ //g'`
HPCUSER=`grep -w HPCUSER conf/expdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
MODEL=`grep -w MODEL conf/expdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
VERSION=`grep -w VERSION conf/expdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
MODELS_DIR=`grep -w MODELS_DIR conf/archdef_${EXPID}.conf | cut -d '=' -f2 |sed 's/ //g'`
SCRATCH_DIR=`grep -w SCRATCH_DIR conf/archdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
MODSRC="modsrc.tar" # name for tar file; would be containing modified sources
MODSETUP="modsetup.tar" # name for tar file; would be containing modified setup (namelist etc)

# prepare modified stuff correctly
mkdir -p model
if [[ $MODEL != '' && $VERSION != '' ]]; then
 # in case, user need to modify the sources manually prepare at "/cfu/autosubmit/$EXPID/model/sources"
 REALSOURCES="/cfu/models/$MODEL/$VERSION/sources"
 if [[ -d model/sources && -d $REALSOURCES ]]; then
  LIST=`diff -rqu model/sources $REALSOURCES | awk '{print $2}'`
  LSWC=`diff -rqu model/sources $REALSOURCES | awk '{print $2}' | wc -l`
  if [[ $LSWC -gt 0 ]]; then
   tar -cvf conf/$MODSRC $LIST
  fi
 else
  echo "sources are not available yet"
 fi
 # register setup stuff w.r.t EXPID once
 REALSETUP="/cfu/models/$MODEL/$VERSION/setup"
 if [[ ! -d model/setup ]]; then
    cp -rp $REALSETUP model/
 fi
 tar -cvf conf/$MODSETUP model/setup
else
 echo "MODEL and VERSION must be filled into expdef_${EXPID}.conf"
 exit 1
fi

# setup process starts from here
case $HPCARCH in
 bsc) HPCARCH="mn-$HPCPROJ" ;;
 marenostrum3) HPCARCH="mn-$HPCPROJ" ;;
esac
SSH="ssh $HPCARCH"
MAIN=$SCRATCH_DIR/$HPCPROJ/$HPCUSER/$EXPID

# process for bin (deal with modsrc.tar)
BIN=$MAIN/model/bin
$SSH mkdir -p $BIN
$SSH rm -rf $BIN/*
if [[ -f conf/$MODSRC ]]; then
 # copy modified sources at HPC
 scp conf/$MODSRC $HPCARCH:$MAIN

 # copy pre-compiled sources; assuming that those are already available at HPC
 $SSH "\
 if [[ ! -d $MAIN/model/sources ]]; then \
  cp -rp $MODELS_DIR/$MODEL/$VERSION/sources $MAIN/model ;\
 fi"

 # inflate modified sources with pre-compiled sources
 $SSH "\
 cd $MAIN ;\
 tar -xvf $MODSRC"

 # re-compile sources; assuming that everything is not being compiled from scratch (by default)
 case $MODEL in
  ecearth)
   case $VERSION in
    v2*)
     $SSH "\
     cd $MAIN/model/sources/build ;\
     ./compilation.ksh ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $MAIN/model/sources/oasis3/prism_2-5/prism/*/bin/oasis3.MPI1.x $BIN ;\
      ln -sf $MAIN/model/sources/nemo/nemo_build/opa_exe.* $BIN ;\
      ln -sf $MAIN/model/sources/ifs/bin/ifsMASTER $BIN ;\
     fi"
    ;;
    v3*)
     $SSH "\
     cd $MAIN/model/sources/build-config ;\
     ./compilation.cmd ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $MAIN/model/sources/oasis*/*/bin/oasis3.MPI1.x $BIN ;\
      ln -sf $MAIN/model/sources/ifs*/bin/ifsmaster* $BIN ;\
     fi"
     OCONFIGS=`$SSH ls -1 $MAIN/model/sources/nemo*/CONFIG | grep ORCA`
     for OCONFIG in $OCONFIGS; do
      $SSH "\
      mkdir -p $BIN/$OCONFIG ;\
      ln -sf $MAIN/model/sources/nemo*/CONFIG/$OCONFIG/BLD/bin/*.exe $BIN/$OCONFIG"
     done
    ;;
    *)
     echo "$VERSION is not correct"
    ;;
   esac
  ;;
  nemo)
   case $VERSION in
    ecearth-v2*)
     $SSH "\
     cd $MAIN/model/sources/build ;\
     ./compilation.ksh ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $MAIN/model/sources/nemo/nemo_build/opa_exe* $BIN ;\
     fi"
    ;;
    v3.2)
     $SSH "\
     cd $MAIN/model/sources/modipsl/config/ORCA2_LIM ;\
     ./compilation.sh ;\
     if [[ $? -eq 0 ]]; then \
     ln -sf $MAIN/model/sources/modipsl/bin/* $BIN ;\
     fi"
    ;;
    v3.3)
     $SSH "\
     cd $MAIN/model/sources/NEMOGCM/CONFIG ;\
     ./compilation.sh ;\
     if [[ $? -eq 0 ]]; then \
      OCONFIGS=`$SSH ls -1 $MAIN/model/sources/NEMOGCM/CONFIG | grep ORCA1`
      for OCONFIG in $OCONFIGS; do
       $SSH "\
       mkdir -p $BIN/$OCONFIG ;\
       ln -sf $MAIN/model/sources/NEMOGCM/CONFIG/$OCONFIG/BLD/bin/*.exe $BIN/$OCONFIG"
      done
     fi"
    ;;
    *)
     echo "$VERSION is not correct"
    ;;
   esac
  ;;
  *)
   echo "$MODEL is not correct"
  ;;
 esac
else
 # if there is nothing to be re-compiled at HPC then link already compiled binaries 
 # correctly under ../../$EXPID/model/bin
 $SSH ln -sf $MODELS_DIR/$MODEL/$VERSION/bin/* $BIN
fi

# process for setup (deal with modsetup.tar)
SETUP=$MAIN/model/setup
$SSH mkdir -p $SETUP
$SSH rm -rf $SETUP/*
if [[ -f conf/$MODSETUP ]]; then
 # copy setup (scripts) at HPC and untar
 scp conf/$MODSETUP $HPCARCH:$MAIN
 $SSH "\
 cd $MAIN ;\
 tar -xvf $MODSETUP"
else
 # if there is nothing modified into setup (scripts) then copy already available setup
 # correctly under ../../$EXPID/model/setup
 $SSH cp -rp $MODELS_DIR/$MODEL/$VERSION/setup/* $SETUP
fi

date
