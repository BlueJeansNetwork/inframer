#!/usr/bin/env python

import redis
import json

class Store(object):

  def __init__(self, cfg):
    self.cfg = cfg
    self.conn = redis.StrictRedis(cfg['redis']['host'],
                                  cfg['redis']['port'],
                                  cfg['redis']['db'])
    #self.namespace = '/inframer/db'
    self.namespace = '/inframer/api/v1/db'

  def search_keys(self, key_pattern):
    return self.conn.keys(key_pattern)

  def get_key(self, key_name):
    return self.conn.get(key_name)

  def _get_namespace_keys(self):
    pattern = '/'.join([self.namespace, '*'])
    return self.conn.keys(pattern)

  def get_inframer_views(self):
    return set(x.split('/')[4] for x in self._get_namespace_keys())

  def get_all_dbs(self):
    pattern = '/'.join([self.namespace, '*'])
    return set(x.split('/')[5] for x in self._get_namespace_keys())

  def get_db_views(self, db_name):
    pattern = '/'.join([self.namespace, db_name, '*'])
    return set(x.split('/')[6] for x in self.conn.keys(pattern))

  def store_data(self, view_data):
    db_name = self.cfg['mod_cfg']['name']
    view_name = self.cfg['cmdline']['view']

    view_val = []

    if 'host' in self.cfg['cmdline']:
      view_val.append(self.cfg['cmdline']['host'])
    if view_name in self.cfg['cmdline']:
      view_val.append(self.cfg['cmdline'][view_name])

    db_key = '%s/%s' % (self.namespace, db_name)
    view_key = '%s/%s' % (db_key, view_name)

    if view_val:
      view_key += '/' + '/'.join(view_val)

    pipe = self.conn.pipeline()

    for token in view_data.keys():
      k = '/'.join([view_key, token])
      k = k.replace('//', '/')
      pipe.set(k, json.dumps(view_data[token]))

    pipe.execute()
    return True
