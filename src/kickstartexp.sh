#!/bin/bash

# ./kickstartexp.sh -e EXPID -j job_list/rerun_job_list -s TRUE/FALSE -t TRUE/FALSE

EXPID=chex
JOB_LIST=job_list
START=FALSE
SETUP=FALSE

while getopts e:j:s:t: option
do
 case $option in
  e) EXPID=$OPTARG;;
  j) JOB_LIST=$OPTARG;;
  s) START=$OPTARG;;
  t) SETUP=$OPTARG;;
  \?) exit 1;;
 esac
done
 
set -xuve
DST=/cfu/autosubmit/$EXPID
STAMP=`date +%Y%m%d_%H%M`

LOGS=$HOME/logs/autosubmit
mkdir -p $LOGS

if [[ $START == TRUE ]]; then 
   set +e
   rm -f $DST/tmp/* $DST/pkl/* $DST/plot/*
   set -e
   python create_exp.py $EXPID
   if [[ $SETUP == TRUE ]]; then
      echo "setup experiment"
      ./setupexp.sh -e $EXPID
   fi
   set +e
   nohup python autosubmit.py $EXPID >& $LOGS/${EXPID}_${STAMP}.log &
   set -e
else
   #python recovery.py -e $EXPID -j $JOB_LIST -g
   python recovery.py -e $EXPID -j $JOB_LIST -s
   if [[ $? == 0 ]]; then
      set +e
      nohup python autosubmit.py $EXPID >& $LOGS/${EXPID}_${STAMP}.log &
      set -e
   fi
fi
