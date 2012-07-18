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

cd /cfu/autosubmit/$EXPID

# options and paths required for setting up experiment at HPC
HPCARCH=`grep -w HPCARCH conf/autosubmit_${EXPID}.conf | cut -d '=' -f2 |sed 's/ //g'`
HPCUSER=`grep -w HPCUSER conf/expdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
MODEL=`grep -w MODEL conf/expdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
VERSION=`grep -w VERSION conf/expdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
MODELS_DIR=`grep -w MODELS_DIR conf/archdef_${EXPID}.conf | cut -d '=' -f2 |sed 's/ //g'`
SCRATCH_DIR=`grep -w SCRATCH_DIR conf/archdef_${EXPID}.conf | cut -d '=' -f2 | sed 's/ //g'`
MODSRC="modsrc.tar" # name for tar file; would be containing modified sources

if [[ $MODEL != '' && $VERSION != '' ]]; then
 REALSOURCES="/cfu/models/$MODEL/$VERSION/sources"
 if [[ -d sources && -d $REALSOURCES ]]; then
  LIST=`diff -rqu sources $REALSOURCES | awk '{print $2}'`
  LSWC=`diff -rqu sources $REALSOURCES | awk '{print $2}' | wc -l`
  if [[ $LSWC -gt 0 ]]; then
   tar -cvf conf/$MODSRC $LIST
  fi
 else
  echo "sources are not available yet"
 fi
else
 echo "MODEL and VERSION must be filled into expdef_${EXPID}.conf"
 exit 1
fi

# setup process starts from here
case $HPCARCH in
 bsc) HPCARCH="mn" ;;
esac
SSH="ssh $HPCARCH"
SETUP_DIR=$SCRATCH_DIR/$HPCUSER/$EXPID
$SSH mkdir -p $SETUP_DIR/bin

if [[ -f conf/$MODSRC ]]; then
 # copy modified sources at HPC
 scp conf/$MODSRC $HPCARCH:$SETUP_DIR

 # copy pre-compiled sources; assuming that those are already available at HPC
 $SSH "\
 if [[ ! -d $SETUP_DIR/sources ]]; then \
  cp -rp $MODELS_DIR/$MODEL/$VERSION/sources $SETUP_DIR ;\
 fi"

 # inflate modified sources with pre-compiled sources
 $SSH "\
 cd $SETUP_DIR ;\
 tar -xvf $MODSRC"

 # re-compile sources; assuming that everything is not being compiled from scratch (by default)
 $SSH rm -rf $SETUP_DIR/bin/*
 case $MODEL in
  ecearth)
   case $VERSION in
    v2.*)
     $SSH "\
     cd $SETUP_DIR/sources/build ;\
     ./compilation.ksh ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $SETUP_DIR/sources/oasis3/prism_2-5/prism/*/bin/oasis3.MPI1.x $SETUP_DIR/bin ;\
      ln -sf $SETUP_DIR/sources/nemo/nemo_build/opa_exe.* $SETUP_DIR/bin ;\
      ln -sf $SETUP_DIR/sources/ifs/bin/ifsMASTER $SETUP_DIR/bin ;\
     fi"
    ;;
    v3.0*)
     $SSH "\
     cd $SETUP_DIR/sources/build-config ;\
     ./compilation.sh ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $SETUP_DIR/sources/oasis*/*/bin/oasis3.MPI1.x $SETUP_DIR/bin ;\
      ln -sf $SETUP_DIR/sources/nemo*/bin/opa_* $SETUP_DIR/bin ;\
      ln -sf $SETUP_DIR/sources/ifs*/bin/ifsmaster* $SETUP_DIR/bin ;\
     fi"
    ;;
    v3-*)
     $SSH "\
     cd $SETUP_DIR/sources/build-config ;\
     ./compilation.sh ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $SETUP_DIR/sources/oasis*/*/bin/oasis3.MPI1.x $SETUP_DIR/bin ;\
      ln -sf $SETUP_DIR/sources/ifs*/bin/ifsmaster* $SETUP_DIR/bin ;\
     fi"
     OCONFIGS=`$SSH ls -1 $SETUP_DIR/sources/nemo*/CONFIG | grep ORCA`
     for OCONFIG in $OCONFIGS; do
      $SSH "\
      mkdir -p $SETUP_DIR/bin/$OCONFIG ;\
      ln -sf $SETUP_DIR/sources/nemo*/CONFIG/$OCONFIG/BLD/bin/*.exe $SETUP_DIR/bin/$OCONFIG"
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
     cd $SETUP_DIR/sources/build ;\
     ./compilation.ksh ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $SETUP_DIR/sources/nemo/nemo_build/opa_exe* $SETUP_DIR/bin ;\
     fi"
    ;;
    v3.2)
     $SSH "\
     cd $SETUP_DIR/sources/modipsl/config/ORCA2_LIM ;\
     ./compilation.sh ;\
     if [[ $? -eq 0 ]]; then \
     ln -sf $SETUP_DIR/sources/modipsl/bin/* $SETUP_DIR/bin ;\
     fi"
    ;;
    v3.3)
     $SSH "\
     cd $SETUP_DIR/sources/NEMOGCM/CONFIG ;\
     ./compilation.sh ;\
     if [[ $? -eq 0 ]]; then \
      ln -sf $SETUP_DIR/sources/NEMOGCM/CONFIG/ORCA2_LIM/BLD/bin/*.exe $SETUP_DIR/bin ;\
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
 # if there is nothing to be re-compiled at HPC then link already compiled binaries correctly under ../../$EXPID/bin
 $SSH ln -sf $MODELS_DIR/$MODEL/$VERSION/bin/* $SETUP_DIR/bin
fi

date
