#!/bin/bash

# us-west-2 running nodes
python ips_set_operations.py  --target1 'aws/region/?key_pattern=*us-west-2*&target_key=state&target_value=running' --output_file us-west-2.running

# all monitored nodes
python ips_set_operations.py --target1 'nagios/host_status' --output nagios.all

# all chef nodes
python ips_set_operations.py --target1 'chef/node' --output chef.all

# us-west-2 running nodes which are monitored
python ips_set_operations.py --target1 us-west-2.running --target2 nagios.all --operation intersection --output us-west-2.running_and_monitored

# us-west-2 running nodes which are monitored and cheffed
python ips_set_operations.py --target1 us-west-2.running_and_monitored --target2 chef.all --operation intersection --output us-west-2.running_and_monitored_and_cheffed

# us-west-2 running nodes which are monitored but not cheffed
python ips_set_operations.py --target1 us-west-2.running_and_monitored --target2 chef.all --operation difference --output us-west-2.running_and_monitored_not_cheffed
