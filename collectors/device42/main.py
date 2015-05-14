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
  if VERBOSE:
    print 'Collecting data'
  view_data = {}
  # create auth object for basic authentication
  auth_obj = HTTPBasicAuth(cfg['cmdline']['username'],
                           cfg['cmdline']['password'])

  # get devices in each service level
  for svc_level in cfg['cmdline']['service_levels']:
    url = 'https://%s/api/1.0/devices/?service_level=%s' % (cfg['cmdline']['host'],
                                                            svc_level)
    rs = requests.get(url, verify=False, auth=auth_obj)
    if rs.status_code != 200:
      print 'Failed to check url - %s' % url
      sys.exit(1)
    response_data = rs.json()

    count = 0
    nsvc_devices = len(response_data['Devices'])
    for device in response_data['Devices']:
      # for each device capture its info minus the null params
      if svc_level not in view_data:
        view_data[svc_level] = {}

      if cfg['cmdline']['max_records'] and \
         count == cfg['cmdline']['max_records']:
        break

      count +=1

      if VERBOSE:
        print '%s: Getting %d/%d' % (svc_level, count, nsvc_devices)
      sys.stdout.flush()

      device_name = device['name']
      device_url = device['device_url']

      # query the device url
      device_url = 'https://%s/%s' % (cfg['cmdline']['host'], device_url)
      device_rs = requests.get(device_url, verify=False, auth=auth_obj)
      if device_rs.status_code != 200:
        print 'Failed to check url - %s' % url
        sys.exit(1)

      device_info = device_rs.json()

      # skip devices not in use
      if device_info['in_service'] != True:
        continue

      if not 'ip_addresses' in device_info:
        continue

      # remove the params which don't have any value
      cleaned_device_info = {}
      for param in device_info:
        if not device_info[param]:
          continue
        cleaned_device_info[param] = device_info[param]

      if not 'ip_addresses' in cleaned_device_info:
        continue
      ips = []
      for ip_info in cleaned_device_info['ip_addresses']:
        view_data[ip_info['ip']] = cleaned_device_info

      #device_type = device_info['type']
      #if device_type not in view_data[svc_level]:
      #  view_data[svc_level][device_type] = []
      #view_data[svc_level][device_type].append(cleaned_device_info)

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
  parser.add_argument('-s', '--service_levels',
                      help='device42 service levels to search',
                      nargs='*', required=True)
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
