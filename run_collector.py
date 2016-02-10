#!/usr/bin/env python

import os
import sys
import argparse
import importlib
import inframer.utils as utils

def usage():
  return '''
usage: %s collector_name

DESC: call the appropriate inframer collector

arguments:
  collector_name - collector to call
'''

def _dict_args_to_list(args):
  output = []
  for k, v in args.iteritems():
    output.append(k)

    if isinstance(v, list):
      for item in v:
        output.append(item)
      continue

    if v == 'true':
      continue

    output.append(v)
  return output

def load_collector_mod(collector_name):
  collector_mod_name = 'collectors.%s' % collector_name
  return importlib.import_module(collector_mod_name)

def run_collector(collector_name, args):

  if isinstance(args, dict):
    args = _dict_args_to_list(args)

  collector_mod = load_collector_mod(collector_name)
  mod_dir = os.path.dirname(collector_mod.__file__)

  collectors_base_cfg = utils.load_base_cfg('collectors')
  collector_cfg = utils.load_cfg(mod_dir)
  collector_cfg.update(collectors_base_cfg)

  mod_name = os.path.basename(collector_mod.__file__).split('.')[0]
  collector_cfg['mod_cfg'] = collector_cfg[mod_name]
  del collector_cfg[mod_name]

  cmdline_opts = collector_mod.parse_cmdline(args, collector_cfg)
  collector_cfg['cmdline'] = cmdline_opts

  view_data = collector_mod.collect_data(collector_cfg)

  if 'name' in collector_cfg['store']:
    if hasattr(collector_mod, 'store_data'):
      collector_mod.store_data(collector_cfg, view_data)
    else:
      store_name = collector_cfg['store']['name']
      store_obj = utils.load_store(collector_cfg)
      store_obj.store_data(view_data)
  return view_data

def validate_input(argv):
  if len(argv) < 2:
    print 'ERROR: Collector not specified'
    print usage()
    sys.exit(1)

def main(argv):
  validate_input(argv)
  run_collector(sys.argv[1], argv[2:])

if __name__ == '__main__':
  # test comment
  main(sys.argv)
