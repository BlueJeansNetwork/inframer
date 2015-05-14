#!/usr/bin/env python

import sys
import redis
import json
import glob
import os

redis_namespace = '/inframer/api/v1/db'
targets = ['nagios/host_status', 'aws/region', 'chef/env', 'chef/node']
redis_conn = redis.StrictRedis(host='127.0.0.1', port=6379, db=1)
curr_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(curr_dir)

for target in targets:
  print 'loading %s' % target
  files = glob.glob(target + '/*')
  ds_list = [json.loads(open(x).read()) for x in files]
  for ds in ds_list:
    uniq_key = ds.keys()[0]
    ds_value = ds.values()[0]
    redis_key = redis_namespace + '/' + target + '/' + uniq_key
    redis_conn.set(redis_key, json.dumps(ds_value))
