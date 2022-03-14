#!/usr/bin/env python3

import collections

JobRow = collections.namedtuple(
    'JobRow', ['name', 'queue_time', 'run_time', 'status', 'energy', 'submit', 'start', 'finish', 'ncpus', 'run_id'])