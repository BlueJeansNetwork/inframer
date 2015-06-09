#!/usr/bin/env python

import json
import argparse
import requests
import atexit

VERBOSE = False
AUTH_TOKEN = None

def login(host, port, username, password):
  if VERBOSE:
    print 'netscalar: %s: logging in' % host

  url = "http://%s:%s/nitro/v1/config/login" % (host, port)
  data = {
    'login': {
      'username': username,
      'password': password
    }
  }
  headers = {'Content-Type': 'application/vnd.com.citrix.netscaler.login+json'}
  r = requests.post(url, data=json.dumps(data), headers=headers)
  return r.cookies['NITRO_AUTH_TOKEN']

def logout(host, port):
  if VERBOSE:
    print 'netscalar: %s: logging out' % host

  global AUTH_TOKEN

  if AUTH_TOKEN is None:
    if VERBOSE:
      print 'netscalar: %s: not logged in' % host
    return None

  url = "http://%s:%s/nitro/v1/config/logout" % (host, port)
  data = {
    'logout': {}
  }
  headers = {'Content-Type': 'application/vnd.com.citrix.netscaler.logout+json'}
  cookies = {'NITRO_AUTH_TOKEN': AUTH_TOKEN}
  r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
  return r.status_code


def collect_data(cfg):
  host = cfg['cmdline']['host']
  port = cfg['cmdline']['port']
  username = cfg['cmdline']['username']
  password = cfg['cmdline']['password']

  global AUTH_TOKEN
  AUTH_TOKEN = login(host, port, username, password)

  if VERBOSE:
    print 'netscalar: %s: fetching load balancer data' % host

  url = "http://%s:%s/nitro/v1/config/lbvserver" % (host, port)
  cookies = {'NITRO_AUTH_TOKEN': AUTH_TOKEN}
  r = requests.get(url, cookies=cookies)
  ns_data = r.json()

  count = 1
  view_data = {}
  n_lbvservers = len(ns_data['lbvserver'])

  for lbvserver in ns_data['lbvserver']:
    lb_name = lbvserver['name']
    lb_ip = lbvserver['ipv46']

    view_data[lb_ip] = {
      'lbvserver': lbvserver,
      'lbvserver_binding': {}
    }

    if VERBOSE:
      print 'netscalar: %s: %d/%d: fetching binding data for %s' %\
            (host, count, n_lbvservers, lb_name)

    url = "http://10.100.1.101/nitro/v1/config/lbvserver_binding/%s" % lb_name
    cookies = {'NITRO_AUTH_TOKEN': AUTH_TOKEN}
    r = requests.get(url, cookies=cookies)
    binding_data = r.json()

    binding_data = binding_data['lbvserver_binding'][0]

    balanced_services = binding_data['lbvserver_service_binding']
    for balanced_service in balanced_services:
      service_port = balanced_service['port']
      if service_port not in view_data[lb_ip]['lbvserver_binding']:
        view_data[lb_ip]['lbvserver_binding'][service_port] = []
      view_data[lb_ip]['lbvserver_binding'][service_port].append(balanced_service)
    if cfg['cmdline']['max_records'] and \
       count == cfg['cmdline']['max_records']:
      break
    count += 1

  if cfg['cmdline']['dump_ds']:
    print json.dumps(view_data, indent=4)

  return view_data

def parse_cmdline(args, cfg):
  ''' Parse user cmdline '''
  desc = 'Get netscalar info'
  parser = argparse.ArgumentParser(description=desc)

  parser.add_argument('-H', '--host',
                      help='netscalar host',
                      type=str, default=cfg['mod_cfg']['host'])
  parser.add_argument('-P', '--port',
                      help='netscalar host port',
                      type=str, default=cfg['mod_cfg']['port'])
  parser.add_argument('-u', '--username',
                      help='netscalar login username',
                      type=str, default=cfg['mod_cfg']['username'])
  parser.add_argument('-p', '--password',
                      help='netscalar login password',
                      type=str, required=True)
  parser.add_argument('--view',
                      help='lbvserver',
                      type=str, default=cfg['mod_cfg']['view'])
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
  atexit.register(logout, opts.host, opts.port)

  global VERBOSE
  if opts.verbose:
    VERBOSE = True

  return dict(vars(opts))
