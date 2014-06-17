#!/bin/bash

# Copyright 2014 Climate Forecasting Unit, IC3

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.

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
