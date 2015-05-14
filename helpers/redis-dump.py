# requires pip install redis-dump-load
import redisdl

json_text = redisdl.dumps()

with open('redis-dump.json', 'w') as f:
    redisdl.dump(f)
