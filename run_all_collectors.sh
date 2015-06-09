#!/bin/bash
echo flushdb | redis-cli
python run_collectors.py chef.main --view env $*
python run_collectors.py nagios.host_status $*
python run_collectors.py chef.main --view node $*
python run_collectors.py aws.main --view region --region us-west-1 $*
python run_collectors.py aws.main --view region --region us-west-2 $*
python run_collectors.py aws.main --view region --region us-east-1 $*
python run_collectors.py device42.main -p $DEVICE42_PASSWD --service_levels Stage Production $*
