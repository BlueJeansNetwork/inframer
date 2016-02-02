#!/usr/bin/env python

import json
import re

import jmespath
import flask
import inframer.utils as utils

# load the cfg
CFG = utils.load_base_cfg('config')

# create the store obj
STORE_OBJ = utils.load_store(CFG)

# create base uris and urls to be used
BASE_URL = 'http://%s:%s' % (CFG['api']['host'], CFG['api']['port'])
BASE_URI = '/inframer/api/v1'
BASE_URI_DB = BASE_URI + '/db'

app = flask.Flask(__name__)

@app.route(BASE_URI_DB + '/<db>/<view>/<path:varargs>', methods=['GET'])
def get_db_target_data(db, view, varargs):
  # load the search key and values
  search_key = '/'.join([BASE_URI_DB, db, view, varargs])
  search_key = search_key.rstrip('/')

  # get the value
  output = json.loads(STORE_OBJ.get_key(search_key))

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

@app.route(BASE_URI_DB + '/<db>/<view>/', methods = ['GET'])
def get_db_data(db, view):
  # load the search key and values
  search_pattern = '/'.join([BASE_URI_DB, db, view])

  search_results = STORE_OBJ.search_keys(search_pattern + '/*')

  # extract and prep the target params
  target_params = {
    'keys': [],
    'filters': {},
    'maxrecords': -1,
    'reverse_match': False,
    'sort_on': None
  }

  keys_arg = flask.request.args.get('keys')
  if keys_arg is None:
    target_params['keys'] = None
  else:
    target_params['keys'] = [str(x.strip()) for x in keys_arg.split(',')]

  filters_arg = flask.request.args.get('filters')
  filters = {}
  if filters_arg is not None:
    for filter_kv in filters_arg.split(','):
      filter_kv = str(filter_kv.strip())
      filter_key, filter_regex = [str(x) for x in filter_kv.split(':')]
      filters[filter_key] = re.compile(filter_regex)

  maxrecords_arg = flask.request.args.get('maxrecords')
  if maxrecords_arg is not None:
    target_params['maxrecords'] = int(maxrecords_arg)

  reverse_match_arg = flask.request.args.get('reverse_match')
  if reverse_match_arg is not None:
    if reverse_match_arg == 'true':
      target_params['reverse_match'] = True

  sort_on_arg = flask.request.args.get('sort_on')
  if sort_on_arg is not None:
    target_params['sort_on'] = sort_on_arg

  responses = []
  response_http_code = 200
  count = 0

  for search_result in search_results:
    # iterate through search results, filter out wanted, extract out required keys
    if target_params['maxrecords'] != -1 and count >= target_params['maxrecords']:
      break

    target_url = BASE_URL + search_result

    # if no keys specified - just send the urls
    if target_params['keys'] is None:
      responses.append({'url': target_url})
      count += 1
      continue

    # load the response
    response = json.loads(STORE_OBJ.get_key(search_result))

    # check if this response matches the filter
    errors = {}
    if filters:
      # filters provided - check matches
      response_matches = False
      for filter_key, filter_regex in filters.iteritems():
        response_value = jmespath.search(filter_key, response)

        if response_value is None:
          continue
        if not re.search(filter_regex, response_value):
          continue

        response_matches = True # reached here - at least one filter matched
        break

      # if reverse_match is true - skip this record if it matches
      if target_params['reverse_match']:
        if response_matches:
          continue
      else:
        # if reverse match is false - skip this record if it does not match
        if not response_matches:
          continue

    # get the required keys
    if '*' not in target_params['keys']:
      # get specific keys
      culled_response = {}
      invalid_keys = []

      for target_key in target_params['keys']:
        target_value = jmespath.search(target_key, response)
        if target_value is None:
          if 'invalid_keys' not in errors:
            errors['invalid_keys'] = []
          errors['invalid_keys'].append(target_key)
        else:
          culled_response[target_key] = target_value

      responses.append({
        'url': target_url,
        'data': culled_response
      })
    else:
      # get all keys
      responses.append({
        'url': target_url,
        'data': response
      })

    count += 1

    if errors:
      response_http_code = 400
      responses[count]['errors'] = errors

  # sort the output if sort_on provided
  if target_params['sort_on'] is not None:
    responses = sorted(responses,
                       key=lambda k: k['data'][target_params['sort_on']])

  http_response = flask.jsonify({'output': responses})
  http_response.status_code = response_http_code
  return http_response

@app.route(BASE_URI_DB + '/<db>/', methods = ['GET'])
def get_db_views(db):
  # get unique views for this db
  output = {db: []}
  db_views = STORE_OBJ.get_db_views(db)

  # construct url for each view
  for view in db_views:
    uri = '/'.join([BASE_URI_DB, db, view])
    output[db].append(BASE_URL + uri)

  return flask.jsonify(output)

@app.route(BASE_URI_DB + '/', methods = ['GET'])
def get_dbs():
  # get all database names
  dbs = STORE_OBJ.get_all_dbs()
  output = {}
  for db in dbs:
    uri = '/'.join([BASE_URI_DB, db])
    output[db] = BASE_URL + uri
  return flask.jsonify(output)

@app.route(BASE_URI + '/', methods = ['GET'])
def get_base_views():
  views = STORE_OBJ.get_inframer_views()
  output = {'inframer': []}
  for view in views:
    output['inframer'].append(BASE_URL + BASE_URI + '/' + view)
  return flask.jsonify(output)

if __name__ == '__main__':
  debug = False
  if CFG['api']['debug'] == 'true':
    debug = True
  app.run(host=CFG['api']['host'], port=int(CFG['api']['port']), debug=debug)
