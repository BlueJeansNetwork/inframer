#!/usr/bin/env python

import os
import sys
import json
import flask
import requests
import re
from util import utils

# load the cfg
cfg = utils.load_base_cfg('config')

# create the store obj
store_obj = utils.load_store(cfg)

# create base uris and urls to be used
base_url = 'http://%s:%s' % (cfg['api']['host'], cfg['api']['port'])
base_uri = '/inframer/api/v1'
base_uri_db = base_uri + '/db'

app = flask.Flask(__name__)

@app.route(base_uri_db + '/<db>/<view>/<path:varargs>', methods = ['GET'])
def get_db_target_data(db, view, varargs):
  # load the search key and values
  search_key = '/'.join([base_uri_db, db, view, varargs])
  search_key = search_key.rstrip('/')

  # get the value
  output = json.loads(store_obj.get_key(search_key))

  # get the key separator
  key_sep = flask.request.args.get('key_sep')
  if not key_sep:
    key_sep = '/'

  # check if we need a subset of the ds
  qkey = flask.request.args.get('key')
  if qkey:
    output = utils.get_dict_subset(output, qkey, key_sep)

  # flatten ds if required
  flatten = flask.request.args.get('flatten')
  if flatten and flatten == 'true':
    output = utils.flatten_ds(output, sep=key_sep)

  return flask.jsonify({varargs: output})

@app.route(base_uri_db + '/<db>/<view>/', methods = ['GET'])
def get_db_data(db, view):
  # load the search key and values
  search_pattern = '/'.join([base_uri_db, db, view])

  # add filter if any
  key_pattern_str = flask.request.args.get('key_pattern')
  if key_pattern_str is None:
    key_pattern_str = '*'

  if not key_pattern_str.startswith('/'):
    key_pattern_str = '/*' + key_pattern_str + '*'
  search_pattern += key_pattern_str
  search_vals = store_obj.search_keys(search_pattern)

  target_params = {
    'target_keys': [],
    'target_filters': {},
  }

  target_keys_arg = flask.request.args.get('target_keys')
  if target_keys_arg is None:
    target_params['target_keys'] = None
  else:
    target_params['target_keys'] = [x.strip() for x in target_keys_arg.split(',')]

  target_filters_arg = flask.request.args.get('target_filters')
  target_filters = {}
  if target_filters_arg is not None:
    for target_filter_kv in target_filters_arg.split(','):
      target_filter_kv = str(target_filter_kv.strip())
      filter_key, filter_regex = [str(x) for x in target_filter_kv.split(':')]
      target_filters[filter_key] = re.compile(filter_regex)

  responses = []
  response_http_code = 200

  for search_val in search_vals:
    target_url = base_url + search_val

    # if no keys specified - just send the urls
    if target_params['target_keys'] is None:
      responses.append({'url': target_url})
      continue

    # load the response
    response = json.loads(store_obj.get_key(search_val))

    # check if this response matches the filter
    if target_filters:
      response_matches = False
      for filter_key, filter_regex in target_filters.iteritems():
        if filter_key not in response:
          continue

        response_value = response[filter_key]
        if not re.match(filter_regex, response_value):
          continue

        response_matches = True # reached here - at least one filter matched
        break

      if not response_matches:
        continue

    if '*' not in target_params['target_keys']:
      # get specific keys
      culled_response = {}
      invalid_keys = []

      for target_key in target_params['target_keys']:
        # handle nested keys
        # country.state.city = e.g. {'country': {'state': {'city': 'X'}}}
        nesting = target_key.split('.')
        invalid_key = None

        if len(nesting) == 1:
          if target_key not in response:
            invalid_key = target_key
          if invalid_key is None:
            culled_response[target_key] = response[target_key]
        else:
          final_value = None
          depth_reached = None
          nested_response = response

          for nested_key in nesting:
            if depth_reached is None:
              depth_reached = nested_key
            else:
              depth_reached += '.' + nested_key

            if nested_key not in nested_response:
              invalid_key = depth_reached
              break

            final_value = nested_response[nested_key]
            nested_response = final_value

          if invalid_key is None:
            culled_response[target_key] = final_value

        if invalid_key is not None:
          invalid_keys.append(invalid_key)

      if invalid_keys:
        response_http_code = 400
        culled_response['error'] = 'invalid_keys: %s' % str(invalid_keys)

      responses.append({'data': culled_response, 'url': target_url})
    else:
      responses.append({'data': response, 'url': target_url})

  print json.dumps(responses, indent=2)
  http_response = flask.jsonify({'output': responses})
  http_response.status_code = response_http_code
  return http_response

@app.route(base_uri_db + '/<db>/', methods = ['GET'])
def get_db_views(db):
  # get unique views for this db
  output = {db: []}
  db_views = store_obj.get_db_views(db)

  # construct url for each view
  for view in db_views:
    uri = '/'.join([base_uri_db, db, view])
    output[db].append(base_url + uri)

  return flask.jsonify(output)

@app.route(base_uri_db + '/', methods = ['GET'])
def get_dbs():
  # get all database names
  dbs = store_obj.get_all_dbs()
  output = {}
  for db in dbs:
    uri = '/'.join([base_uri_db, db])
    output[db] = base_url + uri
  return flask.jsonify(output)

@app.route(base_uri + '/', methods = ['GET'])
def get_base_views():
  views = store_obj.get_inframer_views()
  output = {'inframer': []}
  for view in views:
    output['inframer'].append(base_url + base_uri + '/' + view)
  return flask.jsonify(output)

if __name__ == '__main__':
  debug = False
  if cfg['api']['debug'] == 'true':
    debug = True
  app.run(host=cfg['api']['host'], port=int(cfg['api']['port']), debug=debug)
