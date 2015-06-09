#!/bin/bash

env_file='collectors_env_vars.sh'

if ! [ -f $env_file ]; then
  echo "ERROR: Did not find env file $env_file. Create one export vars used in this script"
  exit 1
fi

. $env_file

echo flushdb | redis-cli

python run_collector.py chef.main --view env $*

python run_collector.py nagios.host_status $*

python run_collector.py chef.main --view node $*

python run_collector.py aws.main --view region --region us-west-1 $*

python run_collector.py aws.main --view region --region us-west-2 $*

python run_collector.py aws.main --view region --region us-east-1 $*

python run_collector.py device42.main --username $DEVICE42_USERNAME --password $DEVICE42_PASSWD --service_levels Stage Production $*

python run_collector.py netscalar.main --view lbvserver --username $NETSCALAR_USERNAME --password $NETSCALAR_PASSWD --host $DEVICE42_HOST $*
