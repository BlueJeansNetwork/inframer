#!/usr/bin/env python

import os
import sys
import json
import argparse
import boto.ec2
from collections import OrderedDict
from util import utils

VERBOSE = False

def collect_data(cfg):

  region = cfg['cmdline']['region']

  if VERBOSE:
    print 'collecting aws data for region %s' % region

  ec2_conn = boto.ec2.connect_to_region(region)
  curr_reservations = ec2_conn.get_all_instances()
  instances = [i for r in curr_reservations for i in r.instances]

  view_data = {}
  count = 1

  for instance in instances:
    # flatten out the ds, stringify the values and unflatten it - shortcut
    # rather than taking selective items
    flattened_ds = utils.flatten_ds(instance.__dict__)
    updated_ds = {}
    for k, v in flattened_ds.items():
      updated_ds[k] = str(v)

    view_data[instance.id] = utils.unflatten_ds(updated_ds)
    view_data[instance.id]['tags'] = instance.tags
    view_data[instance.id]['state'] = instance.state

    if cfg['cmdline']['max_records'] and \
           count == cfg['cmdline']['max_records']:
      break
    count += 1

  if cfg['cmdline']['dump_ds']:
    print json.dumps(view_data, indent=4)

  return view_data

def parse_cmdline(args, cfg):
  ''' Parse user cmdline '''
  desc = 'Get aws info'
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--view',
                      help='host_status',
                      type=str, default=cfg['mod_cfg']['view'])
  parser.add_argument('--region',
                      help='aws region',
                      type=str, default=cfg['mod_cfg']['region'])
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
