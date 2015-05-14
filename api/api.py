#!/usr/bin/env python

import os
import sys
import json
import flask
import requests
import inframer.utils

# load the cfg
cfg = inframer.utils.load_base_cfg('api')

# create the store obj
store_obj = inframer.utils.load_store(cfg)

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
    output = inframer.utils.get_dict_subset(output, qkey, key_sep)

  # flatten ds if required
  flatten = flask.request.args.get('flatten')
  if flatten and flatten == 'true':
    output = inframer.utils.flatten_ds(output, sep=key_sep)

  return flask.jsonify({varargs: output})

@app.route(base_uri_db + '/<db>/<view>/', methods = ['GET'])
def get_db_data(db, view):
  # load the search key and values
  search_pattern = '/'.join([base_uri_db, db, view])

  # add filter if any
  unfiltered_search_pattern = search_pattern
  key_pattern_str = flask.request.args.get('key_pattern')
  if key_pattern_str:
    if not key_pattern_str.startswith('/'):
      key_pattern_str = '/' + key_pattern_str
    search_pattern += key_pattern_str
  search_vals = store_obj.search_keys(search_pattern + '*')

  # get target_params if specified
  target_params = {
    'key': None,
    'value': None,
    'flatten': 'false',
    'key_sep': '/'
  }
  for param in target_params.keys():
    param_val = flask.request.args.get('target_' + param)
    if param_val != '':
      target_params[param] = param_val

  output = {}
  # assume that this is node data
  for search_val in search_vals:
    output_value = {'data': None, 'url': None}
    output_value['url'] = base_url + search_val
    has_filter = False
    if target_params['key']:
      has_filter = True
      # if target_key specified - show only those keys
      client = app.test_client()
      uri = search_val + '?'
      uri += '&'.join((k + '=' + v for k, v in target_params.iteritems() \
                       if v is not None))
      response = client.get(uri, headers=list(flask.request.headers),
                            follow_redirects=True)
      response_dict = json.loads(response.data).values()[0]
      if response_dict:
        if target_params['value']:
          # if target_value specified show only those keys with that value
          if response_dict.values()[0] == target_params['value']:
            output_value['data'] = response_dict
          else:
            output_value['data'] = None
        else:
          output_value['data'] = response_dict

    output_key = search_val.split(unfiltered_search_pattern)[1].replace('/', '', 1)
    output[output_key] = output_value

    if output_value['data'] is None:
      del output_value['data']
      if has_filter:
        del output[output_key]

  # expand the keys if specified
  flatten = flask.request.args.get('flatten')
  if not flatten:
    flatten = 'true'
  if flatten == 'false':
    output = inframer.utils.unflatten_ds(output)
  else:
    output = inframer.utils.flatten_ds(output, sep='/')

  return flask.jsonify(output)

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
