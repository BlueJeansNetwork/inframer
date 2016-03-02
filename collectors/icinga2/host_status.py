#!/usr/bin/env python

import os
import sys
import json
import icinga2_api
import argparse
from icinga2_api import api

VERBOSE = False

def collect_data(cfg):
  if VERBOSE:
    print 'collecting data'

  obj = api.Api(profile=cfg['cmdline']['profile'])

  uri = '/v1/objects/hosts'
  data = {}
  output = obj.read(uri, data)

  if output['status'] != 'success': 
    print 'ERROR: icinga2 api call failed'
    print json.dumps(output, indent=2)
    sys.exit(1)

  view_data = {}
  for rec in output['response']['data']['results']:
    ip = rec['attrs']['address']
    view_data[ip] = rec

  if cfg['cmdline']['dump_ds']:
    print json.dumps(view_data, indent=2)

  return view_data

def parse_cmdline(args, cfg):
  ''' Parse user cmdline '''
  desc = 'Get host data from icinga2 '
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--view',
                      help='host_status',
                      type=str, default=cfg['mod_cfg']['view'])
  parser.add_argument('-p', '--profile',
                      help='icinga2 api profile',
                      type=str, default=cfg['mod_cfg']['profile'])
  parser.add_argument('-m', '--max_records',
                      help='will not get more than max_records - for testing',
                      type=int, default=None)
  parser.add_argument('-v', '--verbose',
                      help='verbose mode',
                      action='store_true',
                      default=False)
  parser.add_argument('--dump_ds',
                      help='dump the data structure created to stdout',
                      action='store_true',
                      default=False)

  opts = parser.parse_args(args=args)

  global VERBOSE
  if opts.verbose:
    VERBOSE = True

  return dict(vars(opts))
