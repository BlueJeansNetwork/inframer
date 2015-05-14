#!/bin/bash

# Test the urls mentioned in the main README.md

>test_demo_urls.out
cat ../README.md | grep curl | awk '{ print $3 }' | tr -d '"' | while read url; do
  echo $url
  curl -s -D - $url | tee test_demo_urls.out
  echo "----------------"
done
