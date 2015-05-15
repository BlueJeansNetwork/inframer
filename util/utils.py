#!/usr/bin/env python

import os
import ConfigParser
import importlib
from collections import OrderedDict

def load_store(cfg):
  store_mod_name = 'stores.%s_store' % cfg['store']['name']
  store_mod = importlib.import_module(store_mod_name)
  return store_mod.Store(cfg)

def get_dict_subset(ds, target_key_str, sep):
  target_ds = {}
  tmp_target_ds = target_ds

  tmp_orig_ds = ds
  target_key_tokens = target_key_str.split(sep)

  for k in target_key_tokens[:-1]:
    if not isinstance(tmp_orig_ds, dict):
      k = int(k)
    if k in tmp_orig_ds or (isinstance(tmp_orig_ds,list) and k < len(tmp_orig_ds)):
      tmp_orig_ds = tmp_orig_ds[k]
      tmp_target_ds[k] = {}
      tmp_target_ds = tmp_target_ds[k]
    else:
      return {}

  last_token = target_key_tokens[-1]
  if not isinstance(tmp_orig_ds, dict):
    last_token = int(last_token)
  else:
    if last_token not in tmp_orig_ds:
      return {}

  tmp_target_ds[last_token] = tmp_orig_ds[last_token]

  return target_ds

def merge_dicts(ds1, ds2):
  if not isinstance(ds1, dict) or not isinstance(ds2, dict):
    return ds2
  for k, v in ds2.iteritems():
    if k not in ds1:
      ds1[k] = ds2[k]
    else:
      ds1[k] = merge_dicts(ds1[k], ds2[k])
  return ds1

def unflatten_ds(ds, sep='/'):
  new_ds = {}
  for ds_key in ds.keys():
    tokens = ds_key.split(sep)
    curr_ds = {}
    tmp_ds = curr_ds
    for token in tokens[:-1]:
      if token != '':
        tmp_ds[token] = {}
        tmp_ds = tmp_ds[token]
    tmp_ds[tokens[-1]] = ds[ds_key]
    new_ds = merge_dicts(new_ds, curr_ds)
  return new_ds

def flatten_ds(ds, key="", path="", flattened=None, sep='|'):
  key = str(key)
  if flattened is None:
    flattened = OrderedDict()
  if type(ds) not in(dict, list):
    flattened[((path + sep) if path else "") + key] = ds
  elif isinstance(ds, list):
    for i, item in enumerate(ds):
      flatten_ds(item, "%d" % i, (path + sep + key if path else key),
                 flattened, sep=sep)
  else:
    for new_key, value in ds.items():
      flatten_ds(value, new_key, (path + sep + key if path else key),
                 flattened, sep=sep)
  return flattened

def load_cfg(cfg_dir, cfg_filename='config/cfg.ini'):
  cfg_file = os.path.join(cfg_dir, cfg_filename)
  if not os.path.exists(cfg_file):
    raise ValueError('ERROR: Failed to find cfg file: %s' % cfg_file)
  parser = ConfigParser.SafeConfigParser()
  parser.read(cfg_file)
  cfg_ds = {}
  for section in parser.sections():
    cfg_ds[section] = dict(parser.items(section))
  return cfg_ds

def load_base_cfg(component, cfg_filename='config/cfg.ini'):
  curr_dir = os.path.dirname(os.path.abspath(__file__))
  target_dir = os.path.join(curr_dir, component)
  return load_cfg(target_dir, cfg_filename)
