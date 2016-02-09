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
  sep = flask.request.args.get('sep')
  if not sep:
    sep = '.'

  # check if we need a subset of the ds
  qkey = flask.request.args.get('key')
  if qkey:
    output = utils.get_dict_subset(output, qkey, sep)

  # flatten ds if required
  flatten = flask.request.args.get('flatten')
  if flatten and flatten == 'true':
    output = utils.flatten_ds(output, sep=sep)

  return flask.jsonify({varargs: output})


def _db_data_extract_get_args(request_obj):

  get_params = {}

  keys_arg = flask.request.args.get('keys')
  if keys_arg is None:
    get_params['keys'] = None
  else:
    get_params['keys'] = [str(x.strip()) for x in keys_arg.split(',')]

  filters_arg = flask.request.args.get('filters')
  if filters_arg is not None:
    for filter_kv in filters_arg.split(','):
      filter_kv = str(filter_kv.strip())
      filter_key, filter_regex = [str(x) for x in filter_kv.split(':')]

      if 'filters' not in get_params:
        get_params['filters'] = []

      get_params['filters'].append({
        "id": filter_key, 
        "key": filter_key,
        "matches": [filter_regex],
        "regex": True
      })

  filter_type_arg = flask.request.args.get('filter_type')
  if filter_type_arg is not None:
    get_params['filter_type'] = filter_type_arg

  maxrecords_arg = flask.request.args.get('maxrecords')
  if maxrecords_arg is not None:
    get_params['maxrecords'] = int(maxrecords_arg)

  reverse_match_arg = flask.request.args.get('reverse_match')
  if reverse_match_arg is not None:
    if reverse_match_arg == 'true':
      get_params['reverse_match'] = True

  sort_on_arg = flask.request.args.get('sort_on')
  if sort_on_arg is not None:
    get_params['sort_on'] = sort_on_arg

  reverse_arg = flask.request.args.get('reverse')
  if reverse_arg is not None:
    if reverse_arg == 'true':
      get_params['reverse'] = True

  summary_arg = flask.request.args.get('summary')
  if summary_arg is not None:
    if summary_arg == 'true':
      get_params['summary'] = True

  return get_params

@app.route(BASE_URI_DB + '/<db>/<view>/', methods = ['GET', 'POST'])
def db_data(db, view):

  get_data = True

  # find the action to perform
  if flask.request.method == 'GET':
    get_data = True
  elif flask.request.method == 'POST':
    method = flask.request.headers.get('X-HTTP-Method-Override')
    if method == 'GET':
      get_data = True
    else:
      get_data = False

  if not get_data:
    return flask.jsonify({})

  # extract and prep the target params
  default_get_params = {
    'keys': [],
    'filters': {},
    'filter_type': 'OR',
    'maxrecords': -1,
    'reverse_match': False,
    'sort_on': None,
    'reverse': False,
    'summary': False
  }

  get_params = default_get_params

  if flask.request.method == 'GET':
    get_params.update(_db_data_extract_get_args(flask.request))
  elif flask.request.method == 'POST':
    get_params.update(flask.request.get_json())
    
  filters = get_params['filters']

  # load the search key and values
  search_pattern = '/'.join([BASE_URI_DB, db, view])
  search_results = STORE_OBJ.search_keys(search_pattern + '/*')

  responses = []
  response_http_code = 200
  record_count = 0
  err_count = 0

  for search_result in search_results:
    # iterate through search results, filter out wanted, extract out required keys
    if get_params['maxrecords'] != -1 and record_count >= get_params['maxrecords']:
      break

    target_url = BASE_URL + search_result

    # if no keys specified - just send the urls
    if get_params['keys'] is None:
      responses.append({'url': target_url})
      record_count += 1
      continue

    # load the response
    response = json.loads(STORE_OBJ.get_key(search_result))

    # check if this response matches the filter
    errors = {}
    if filters:
      include_this_record = False

      match_results = utils.jmespath_match(response, filters)
      print match_results
      any_true = any(match_results.values())
      all_true = all(match_results.values())

      if get_params['reverse_match'] is False:
        if get_params['filter_type'] == 'OR':
          if any_true:
            include_this_record = True
        else:
          if all_true:
            include_this_record = True
      else:
        if get_params['filter_type'] == 'OR':
          if not any_true:
            include_this_record = True
        else:
          if not all_true:
            include_this_record = True
      
      if not include_this_record:
        continue

    # get the required keys
    if '*' not in get_params['keys']:
      # get specific keys
      culled_response = {}
      invalid_keys = []

      for target_key in get_params['keys']:
        target_value = jmespath.search(target_key, response)
        if target_value is None:
          if 'invalid_keys' not in errors:
            errors['invalid_keys'] = []
          errors['invalid_keys'].append(target_key)
          err_count += 1
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

    if errors:
      response_http_code = 400
      responses[record_count]['errors'] = errors

    record_count += 1

  # sort the output if sort_on provided
  if get_params['sort_on'] is not None:
    if all(get_params['sort_on'] in x['data'] for x in responses):
      responses = sorted(responses,
                         key=lambda k: k['data'][get_params['sort_on']])

  if get_params['reverse']:
    responses = responses[::-1]

  summary = {
    'total': len(responses),
    'errors': err_count,
    'success': len(responses) - err_count
  }
  if get_params['summary']:
    return flask.jsonify({'summary': summary})

  http_response = flask.jsonify({'output': responses, 'summary': summary})
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
