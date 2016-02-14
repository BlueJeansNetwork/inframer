#!/usr/bin/env python

import os
import re
import ConfigParser
import importlib
from collections import OrderedDict

import jmespath

def _jmespath_match_filters_str(target_ds, filters, **kwargs):
  """ Do jmespath match for str - todo - add doctests """
  opt_attrs = {
    'str_filter_sep': ',',
    'str_filter_kv_sep': ':'
  }
  opt_attrs.update(kwargs)

  filters_arr = filters.split(opt_attrs['str_filter_sep'])
  match_results = []

  for filter_kv in filters_arr:
    filter_key, filter_val = filter_kv.split(opt_attrs['str_filter_kv_sep'])
    filter_val = filter_val.strip()
    search_val = jmespath.search(filter_key, target_ds)

    if isinstance(search_val, list):
      search_val = [str(x) for x in search_val]
      if filter_val in search_val:
        match_results.append(True)
    elif not isinstance(search_val, dict):
      search_val = str(search_val)
      if re.search(re.compile(filter_val, re.IGNORECASE), str(search_val)):
        match_results.append(True)
      else:
        match_results.append(False)
    else:
      match_results.append(False)

  return match_results

def _jmespath_match_filters_list(target_ds, filters, **kwargs):
  """ Do jmespath match for list - todo - add doctests """

  #all_match_results = []
  match_results = {}
  for filter_data in filters:
    if isinstance(filter_data, str):
      results = _jmespath_match_filters_str(target_ds, filter_data, **kwargs)
      match_results[filter_data['id']] = results[0]
    else:
      filter_key = filter_data['key']
      search_val = jmespath.search(filter_key, target_ds)

      if 'exists' in filter_data:
        match_results[filter_data['id']] = False

        if not filter_data['exists']:
          if search_val is None:
            match_results[filter_data['id']] = True
        else:
          if search_val is not None:
            match_results[filter_data['id']] = True

        continue

      chk_op_keys = []
      matches_chk_result = False
      not_matches_chk_result = False

      if 'matches' in filter_data:
        chk_op_keys.append('matches')
      else:
        matches_chk_result = True

      if 'not_matches' in filter_data:
        chk_op_keys.append('not_matches')
      else:
        not_matches_chk_result = True

      for op_key in chk_op_keys:
        if op_key in filter_data:
          result = False
          if isinstance(search_val, list):
            search_val = [str(x) for x in search_val]
            if not filter_data['regex']:
              if any(x for x in filter_data[op_key] if str(x) in search_val):
                result = True 
            else:
              # for a list match regex against all elements of the list
              for val in search_val:
                if any(x for x in filter_data[op_key] if re.search(re.compile(str(x), re.IGNORECASE), 
                                                                   val)):
                  result = True
                  break
          else:
            search_val = str(search_val)
            if not filter_data['regex']:
              if any(x for x in filter_data[op_key] if x == search_val):
                result = True
            else:
              if any(x for x in filter_data[op_key] if re.search(re.compile(x, re.IGNORECASE),
                                                                 search_val)):
                result = True

          if op_key == 'matches':
            matches_chk_result = result
          elif op_key == 'not_matches':
            not_matches_chk_result = not result

      match_results[filter_data['id']] = matches_chk_result and not_matches_chk_result

  return match_results

def jmespath_match(target_ds, filters, **kwargs): 
  if isinstance(filters, list):
    return _jmespath_match_filters_list(target_ds, filters, **kwargs) 
  return None

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

def load_cfg(cfg_dir, cfg_filename='cfg.ini'):
  cfg_file = os.path.join(cfg_dir, cfg_filename)
  if not os.path.exists(cfg_file):
    raise ValueError('ERROR: Failed to find cfg file: %s' % cfg_file)
  parser = ConfigParser.SafeConfigParser()
  parser.read(cfg_file)
  cfg_ds = {}
  for section in parser.sections():
    cfg_ds[section] = dict(parser.items(section))
  return cfg_ds

def load_base_cfg(component, cfg_filename='cfg.ini'):
  curr_dir = os.path.dirname(os.path.abspath(__file__))
  target_dir = os.path.join(curr_dir, component)
  return load_cfg(target_dir, cfg_filename)
