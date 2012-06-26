#!/bin/bash
set -evx

lstexp=( 'i00v' 'i019' ) 
dirautosubmit='/home/vguemas/autosubmit_version2'

lstrun=`ssh ithaca qstat | awk '{print $3}' | cut -c1-4 `
for exp in ${lstexp[@]} ; do
  if [[ ${lstrun[@]/${exp}} == ${lstrun[@]} ]] ; then
    id=`ps -ef | grep $exp | grep autosubmit |  awk '{print $2}'`
    echo $id
    if [[ ! -z "$id" ]] ; then
      kill -9 $id
    fi
    cd ${dirautosubmit}/src
    python recovery.py -e $exp -g -s
    nohup python autosubmit.py ${exp} >& ${exp}.log &
    echo $exp >> lstexp
    date >> lstexp
  fi
done
