# requires pip install redis-dump-load
import redisdl

with open('redis-dump.json') as f:
    redisdl.load(f)
