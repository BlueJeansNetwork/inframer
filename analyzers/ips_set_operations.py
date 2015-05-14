#!/usr/bin/env python

# dirty script to show an example of an analyzer

import os
import sys
import json
import requests
import argparse

def chef_env_ips(url):
  #print 'getting %s' % url
  rs = requests.get(url)
  data = rs.json()
  return set([k.split('/')[0] for k in data.keys() if '/url' in k])

def chef_node_ips(url):
  #print 'getting %s' % url
  rs = requests.get(url)
  data = rs.json()
  return set([str(k.split('/')[1]) for k in data.keys() if '/url' in k])

def device42_ips(url):
  #print 'getting %s' % url
  rs = requests.get(url)
  data = rs.json()
  return set([str(k.split('/')[1]) for k in data.keys() if '/url' in k])

def aws_region_ips(url):
  #print 'getting %s' % url
  rs = requests.get(url)
  data = rs.json()
  ips = set()
  urls = [data[k] for k in data.keys() if '/url' in k]
  for inst_url in urls:
    #print 'getting %s' % inst_url
    rs = requests.get(inst_url)
    data = rs.json()
    for inst_data in data.values():
      ips.add(str(inst_data['private_ip_address']))
  return ips

def nagios_host_status_ips(url):
  #print 'getting %s' % url
  rs = requests.get(url)
  data = rs.json()
  return set([str(k.split('/')[1]) for k in data.keys()])

def get_ips(base_url, target_uri):
  tokens = target_uri.split('/')
  if tokens <= 2:
    print '%s: Provide at least the db and the view name' % target_uri
  else:
    url = base_url + '/' + target_uri

  func_name = '_'.join([tokens[0], tokens[1], 'ips'])
  curr_module = sys.modules[__name__]
  ips = getattr(curr_module, func_name)(url)
  return ips

def print_result(target1_data, target2_data=None, result=None):
  if target1_data:
    print '%s elements: %d' % (target1_data['path'],
                               len(target1_data['ips']))
  if target2_data:
    print '%s elements: %d' % (target2_data['path'],
                               len(target2_data['ips']))
  if result:
    print 'result elements: %d' % len(result)
    print json.dumps(list(result), indent=4)

def parse_cmdline(args):
  desc = 'Perform set operations on inframer db views'
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--base_url',
                      help='base url where api is running',
                      default='http://localhost:8081/inframer/api/v1/db',
                      type=str)
  parser.add_argument('--target1',
                      help='first target uri/file',
                      required = True,
                      type=str)
  parser.add_argument('--target2',
                      help='second target uri/file',
                      default=None,
                      type=str)
  parser.add_argument('--output_file',
                      help='output file for storing results json',
                      default=None,
                      type=str)
  parser.add_argument('--operation',
                      help='set operation to perform - any of python set module ops',
                      default=None,
                      type=str)
  return parser.parse_args(args=args)

def main(args):
  opts = parse_cmdline(args[1:])
  target1_ips = None
  if os.path.exists(opts.target1):
    # assume that the path is a file
    target1_ips = set(json.loads(open(opts.target1).read()))
  else:
    # if not a file - assume it is a uri
    target1_ips = get_ips(opts.base_url, opts.target1)

  if opts.target1 and opts.target2:
    if not opts.operation:
      print 'ERROR: target1 target2 specified - provide set operation to perform'
      sys.exit(1)

  result = None
  if not opts.target2:
    result = target1_ips
    print_result({'path': opts.target1, 'ips': target1_ips}, result=result)
  else:
    target2_ips = None
    if os.path.exists(opts.target2):
      # assume that the path is a file
      target2_ips = set(json.loads(open(opts.target2).read()))
    else:
      # if not a file - assume it is a uri
      target2_ips = get_ips(opts.base_url, opts.target2)

    set_method = getattr(set, opts.operation)
    result = set_method(target1_ips, target2_ips)
    print_result({'path': opts.target1, 'ips': target1_ips},
                 {'path': opts.target2, 'ips': target2_ips},
                 result)

  # dump if output specified
  if opts.output_file:
    with open(opts.output_file, 'w') as f:
      f.write(json.dumps(list(result)))

if __name__ == '__main__':
  main(sys.argv)
