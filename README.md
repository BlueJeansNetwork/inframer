Inframer - collect, store, analyze - your infrastructure information

### Layout

* collectors: collect information from various infrastructure databases

* stores: store collected information

* api: inframer REST API built on top of stored information - start api by running api.py

* analyzers: consume the REST APIs and analyze the information

* helpers: internal - misc helper scripts

* bin: main working engine - start collection by running run\_collectors.py

### Trial run

* Install Redis on your machine - run it on localhost:6379

* Install the required python modules (temporary fix till we make this project installable via pip)

```
# pip install requests flask redis pychef boto
```

* Ensure that PYTHONPATH contains this project - assuming you cloned this repo in /home/user/inframer

```
export PYTHONPATH="$PYTHONPATH:/home/user/"
```


* Update api/cfg.ini section

```
[redis]
host: localhost
port: 6379
db: 1
```

* Run the following command to load dummy data in redis:

```
python inframer/helpers/dummy-data/load_dummy_data.py
```

* Start the api server. By default it runs on - localhost:8081:

```
python inframer/api/api.py
```

### Examples

* Assumption: trial run setup done

* Get list of available infrastructure databases:

```
curl -L "http://localhost:8081/inframer/api/v1/db/"
```

* For an environment, get the list of views

```
curl -L "http://localhost:8081/inframer/api/v1/db/aws/"
curl -L "http://localhost:8081/inframer/api/v1/db/chef/"
```

* For a view, get the list of all of its targets

```
curl -L "http://localhost:8081/inframer/api/v1/db/aws/region/"
curl -L "http://localhost:8081/inframer/api/v1/db/chef/env/"
```

* For a view, filter out keys on a pattern

```
curl -L "http://localhost:8081/inframer/api/v1/db/aws/region/?key_pattern=*us-west*"
```

* For a view, expand/flatten the keys

```
curl -L "http://localhost:8081/inframer/api/v1/db/aws/region/?flatten=false&key_pattern=*us-west*"
curl -L "http://localhost:8081/inframer/api/v1/db/chef/env/?flatten=false"
curl -L "http://localhost:8081/inframer/api/v1/db/chef/env/?key_pattern=*qa*&flatten=true"
```

* For a target, find its attributes

```
curl -L "http://localhost:8081/inframer/api/v1/db/chef/env/chef_host/qa/"
curl -L "http://localhost:8081/inframer/api/v1/db/aws/region/us-east-1/i-inst4"
```

* For a target, flatten its data structure

```
curl -L "http://localhost:8081/inframer/api/v1/db/chef/env/chef_host/qa?flatten=true"
```

* For a target, find a specific key

```
curl -L "http://localhost:8081/inframer/api/v1/db/aws/region/us-east-1/i-inst4?key=private_ip_address"
```

* Find a specific key for multiple targets - go the view and then specify same key as above as - target\_key.

```
curl -L "http://localhost:8081/inframer/api/v1/db/aws/region/?key_pattern=*us-west*&target_key=state"
```

* Find a specific key with a specific value for multiple targets - go the view and then specify same key as above as - target\_key
and its corresponding value as target\_val
```
curl -L "http://localhost:8081/inframer/api/v1/db/aws/region/?key_pattern=*us-west*&target_key=state&target_val=running"
```

* For flattening - if you want a separator other than / - use the query string parameter - key\_sep

```
curl -L "http://localhost:8081/inframer/api/v1/db/chef/env/chef_host/qa?flatten=true&key_sep=|"
```

### Actual run

* Run the collectors via run_collector.py and view the collected infro through the API

### More details

* Check https://github.com/saurabh-hirani/inframer/tree/master/docs
