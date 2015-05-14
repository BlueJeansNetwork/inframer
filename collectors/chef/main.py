#!/usr/bin/env python

import os
import sys
import argparse
import ConfigParser
import json
import requests
import chef

from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()

VERBOSE = False

def node_collect_data(api, max_records):
  if VERBOSE:
    print 'collecting data'
  all_nodes = list(chef.Node.list())
  total_nodes = len(all_nodes)
  if VERBOSE:
    print 'found %d nodes' % total_nodes
  count = 1
  node_data = {}
  for node in all_nodes:
    if VERBOSE:
      print 'loading node %d/%d' % (count, total_nodes)
    curr_node_data = chef.Node(node).attributes.to_dict()
    if 'ipaddress' in curr_node_data:
      node_data[curr_node_data['ipaddress']] = curr_node_data
    else:
      if 'no_ipaddress' not in node_data:
        node_data['no_ipaddress'] = {}
      node_data['no_ipaddress'][node] = curr_node_data
    if max_records and count == max_records:
      break
    count += 1
  return node_data

def env_collect_data(api, max_records):
  if VERBOSE:
    print 'collecting data'
  all_envs = list(chef.Environment.list())
  total_envs = len(all_envs)
  if VERBOSE:
    print 'found %d environments' % total_envs

  count = 1
  env_data = {}

  for env in all_envs:
    if VERBOSE:
      print "loading env %d/%d" % (count, total_envs)
    env_data[env] = chef.Environment(env).to_dict()

    if max_records and count == max_records:
      break

    count += 1
  return env_data

def collect_data(cfg):
  api = chef.autoconfigure()

  # get env or node data depending on user input
  if cfg['cmdline']['view'] == 'env':
    view_data = env_collect_data(api, cfg['cmdline']['max_records'])
  else:
    view_data = node_collect_data(api, cfg['cmdline']['max_records'])

  if cfg['cmdline']['dump_ds']:
    print json.dumps(view_data, indent=4)

  return view_data

def parse_cmdline(args, cfg):
  ''' Parse user cmdline '''
  desc = 'Get infra data from chef'
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--view',
                      help='node|env',
                      type=str, default=cfg['mod_cfg']['view'])
  parser.add_argument('-H', '--host',
                      help='the chef host against whom this info will be stored',
                      type=str, default=cfg['mod_cfg']['host'])
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
  if opts.view != 'node' and opts.view != 'env':
    print 'ERROR: Invalid view specified'
    sys.exit(1)

  global VERBOSE
  if opts.verbose:
    VERBOSE = True

  return dict(vars(opts))
