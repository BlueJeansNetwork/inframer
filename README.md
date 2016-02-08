Inframer - collect, store, analyze - your infrastructure information

### Introduction

* Rootconf talk: http://www.youtube.com/watch?v=qB1bGUNzRb4

* More info: https://github.com/BlueJeansNetwork/inframer/tree/master/docs

### Layout

* collectors: collect information from various infrastructure databases

* stores: store collected information

* api: inframer REST API built on top of stored information - start api by running api.py

* analyzers: consume the REST APIs and analyze the information

* helpers: internal - misc helper scripts

* start collection by running run\_collectors.sh

### Trial run

* Install Redis on your machine - run it on localhost:6379

* Install the required python modules (temporary fix till we make this project installable via pip)

```
# make deps
```


* Configure your redis config in config/cfg.ini 

```
[redis]
host: localhost
port: 6379
db: 1
```

* Run the following command to load dummy data in redis:

```
make dummy
```

* Start the api server. By default it runs on - localhost:8081:

```
make run
```

### Basic usage examples

* Assumption: dummy data loaded. All of the below examples produce the right results against it.

* Get list of available infrastructure databases:

```
curl "http://localhost:8081/inframer/api/v1/db/"
```

* For an environment, get the list of views

```
curl "http://localhost:8081/inframer/api/v1/db/aws/"
curl "http://localhost:8081/inframer/api/v1/db/chef/"
```

* For a view, get the list of all of its targets

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/"
curl "http://localhost:8081/inframer/api/v1/db/chef/env/"
```

* View all the data captured for a view. This will load all of the data for that view. So use it only when you need it.

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=*"
```

* You can limit the maximum no. of records to be shown also.

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=*&maxrecords=2"
```

* View specific keys for a view. e.g. find nodes with regions and id info in AWS

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=region,id"
```

* Add a basic filter to match key values e.g. find nodes with regions matching west

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=region,id&filters=region:west"
```

* Multiple filters can also be added. Multiple filters are 'OR'd by default e.g. find nodes with regions matching west or instance id matching inst4

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=region,id&filters=region:west,id:inst4"
```

* You can change default filter type from OR to AND.

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=region,id&filters=region:west,id:inst3&filter_type=AND"
```

* For the returned list, you can sort the results by fields in the list. e.g. sort by id

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=region,id&filters=region:west,id:inst3&sort_on=id"
```

* Reverse the list of results

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=region,id&filters=region:west,id:inst3&sort_on=id&reverse=true"
```

* Sometimes you are just interested in the summary and not the results per-se. For that use the summary query field.

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=region,id&filters=region:west,id:inst3&summary=true"
```

The error count in the above result are the records for which the query failed e.g you queried for a field which was present in some but not all of the matched records, etc.

* Detailed information of each url in the search result can be flattened out also:

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/us-west-2/i-inst2?flatten=true&sep=|" # default separator is '.'
```

### Advanced usage examples

* Inframer is powered by [jmespath](http://jmespath.org/) which means that you can query nested data structures like so:

```
curl "http://localhost:8081/inframer/api/v1/db/aws/region/?keys=tags.Name
```

where tags.Name actually queries:

```
tags: {
  Name: "dummy-vm-2",
  Project: "testproj",
  env: "qa"
},
```

* With all the query parameters the URLs do get ugly - you can send your query parameters in POST requests also:

```
curl -X POST 'http://localhost:8081/inframer/api/v1/db/aws/region/' -d @docs/queries/aws.json --header 'Content-Type: application/json'
```

where [docs/queries/aws.json](https://github.com/BlueJeansNetwork/inframer/tree/master/docs/queries/aws.json) contains

```
{
  "keys": ["tags.Name", "instance_type", "state"],
  "filters": [
      {"id": "stopped", "key": "state",  "not_matches": ["running", "terminated"], "regex": false},
      {"id": "is_east_2", "key": "region", "matches": ["east"], "not_matches": ["east-1"], "regex": true}
    ],
  "filter_type": "AND",
  "maxrecords": -1,
  "reverse_match": false,
  "sort_on": "tags.Name",
  "reverse": false,
  "summary": false
}
```

which says:

```
Give me tags.Name, instance_type, state for those records where filter query is 

(("records where key 'state' should not match 'running' and should not match 'terminated' and do not interpret value of 'state' as a regex) 
 AND 
(("records where key 'region' should match 'east' and not match 'east1' and interpret the value of 'region' as regex"))

Sort the result on tags.Name

Show me all the records

There is no need to reverse the results or print only the summary
```

Individiual filter expression in a filter are ANDed i.e. matches should be true (if specified) AND not\_matches should be true (if specified). 

The overall filter expression can be AND or OR depending on filter_type.

### Actual run

* Run the collectors via run_collector.py and view the collected infro through the API
