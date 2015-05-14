#!/usr/bin/env python

import os
import sys
import json
import requests
import argparse

from requests.auth import HTTPBasicAuth

if hasattr(requests, 'packages'):
  requests.packages.urllib3.disable_warnings()

NAGIOS_STATE_MAP = {
  '0': 'OK',
  '1': 'WARNING',
  '2': 'CRITICAL',
  '3': 'UNKNOWN'
}

VERBOSE = False

def collect_data(cfg):
  if VERBOSE:
    print 'collecting data'
    print "mapping IPs to hostnames"

  url = 'http://%s:%d/_objects/hosts/_state' % (cfg['cmdline']['host'], 
                                                cfg['cmdline']['port'])
  rs = requests.get(url)
  if rs.status_code != 200:
    if VERBOSE:
      print 'Failed to check url - %s' % url
    sys.exit(1)
  response_data = rs.json()

  ip_to_hostname = {}
  for hostname in response_data:
    address = response_data[hostname]['address']
    ip_to_hostname[address] = hostname

  total_ips = len(ip_to_hostname)
  if VERBOSE:
    print 'checking host status for %d ips' % (total_ips)

  view_data = {}
  count = 1
  for ip in ip_to_hostname:
    hostname = ip_to_hostname[ip]
    if VERBOSE:
      print '%d/%d: Getting status for %s' % (count, total_ips, hostname)
    url = 'http://%s:%d/_status/%s/_services' % (cfg['cmdline']['host'], 
                                                 cfg['cmdline']['port'],
                                                 hostname)
    rs = requests.get(url)
    if rs.status_code != 200:
      print 'Failed to check url - %s' % url
      continue
    response_data = rs.json()

    for service in response_data:
      curr_state = NAGIOS_STATE_MAP[response_data[service]['current_state']]
      if ip not in view_data:
        view_data[ip] = {}
      view_data[ip][service] = curr_state

    if cfg['cmdline']['max_records'] and \
       count == cfg['cmdline']['max_records']:
      break

    count += 1

  if cfg['cmdline']['dump_ds']:
    print json.dumps(view_data, indent=4)

  return view_data

def parse_cmdline(args, cfg):
  ''' Parse user cmdline '''
  desc = 'Get infra data from device42'
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--view',
                      help='host_status',
                      type=str, default=cfg['mod_cfg']['view'])
  parser.add_argument('-H', '--host',
                      help='nagira host',
                      type=str, default=cfg['mod_cfg']['host'])
  parser.add_argument('-p', '--port',
                      help='nagira port',
                      type=int, default=cfg['mod_cfg']['port'])
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
