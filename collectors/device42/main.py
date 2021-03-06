#!/usr/bin/env python

import os
import sys
import json
import requests
import argparse

from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()

VERBOSE = False

def collect_data(cfg):
  log_prefix = 'device42:'

  if VERBOSE:
    print log_prefix + ' collecting data'

  view_data = {}
  # create auth object for basic authentication
  auth_obj = HTTPBasicAuth(cfg['cmdline']['username'],
                           cfg['cmdline']['password'])

  input_ids = None
  if 'ids' in cfg['cmdline'] and cfg['cmdline']['ids'] is not None:
    input_ids = set(cfg['cmdline']['ids'])

  # get devices in each service level
  url = 'https://%s/api/1.0/devices/' % (cfg['cmdline']['host'])
  rs = requests.get(url, verify=False, auth=auth_obj)
  if rs.status_code != 200:
    print '%s failed to check url - %s' % (log_prefix, url)
    sys.exit(1)
  response_data = rs.json()
  valid_devices = response_data['Devices']

  if input_ids is not None:
    valid_devices = [x for x in response_data['Devices'] if \
                     str(x['device_id']) in input_ids]

    valid_ids = [str(x['device_id']) for x in valid_devices]
    invalid_ids = list(set(input_ids) - set(valid_ids))

    if VERBOSE:
      if valid_devices:
        print '%s valid device ids: %s' % (log_prefix, valid_ids)

    if invalid_ids:
      print '%s invalid device ids: %s' % (log_prefix, invalid_ids)

  count = 0
  nsvc_devices = len(valid_devices)

  for device in valid_devices:
    if cfg['cmdline']['max_records'] and \
       count == cfg['cmdline']['max_records']:
      break

    count +=1

    if VERBOSE:
      print '%s device_id:%s Getting %d/%d' % (log_prefix, 
                                               device['device_id'],
                                               count, 
                                               nsvc_devices)
    sys.stdout.flush()

    device_name = device['name']
    device_url = device['device_url']

    # query the device url
    device_url = 'https://%s/%s' % (cfg['cmdline']['host'], device_url)
    device_rs = requests.get(device_url, verify=False, auth=auth_obj)
    if device_rs.status_code != 200:
      print '%s failed to check url - %s' % (log_prefix, url)
      sys.exit(1)

    device_info = device_rs.json()

    # remove the params which don't have any value
    cleaned_device_info = {}
    for param in device_info:
      if not device_info[param]:
        continue
      cleaned_device_info[param] = device_info[param]

    view_data[str(device_info['device_id'])] = cleaned_device_info

  if cfg['cmdline']['dump_ds']:
    print json.dumps(view_data, indent=4)

  return view_data

def parse_cmdline(args, cfg):
  ''' Parse user cmdline '''
  desc = 'Get infra data from device42'
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--view',
                      help='inventory',
                      type=str, default=cfg['mod_cfg']['view'])
  parser.add_argument('-H', '--host',
                      help='device42 host',
                      type=str, default=cfg['mod_cfg']['host'])
  parser.add_argument('-u', '--username',
                      help='device42 username',
                      type=str, default=cfg['mod_cfg']['username'])
  parser.add_argument('-p', '--password',
                      help='device42 password',
                      type=str, required=True)
  parser.add_argument('-i', '--ids',
                      help='device42 ids to search',
                      nargs='*', required=False)
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
