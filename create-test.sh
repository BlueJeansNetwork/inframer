#!/bin/bash

testscript='test.sh'
echo "#!/bin/bash -e" > $testscript

cat README.md | grep '# add to test cases' -A1 | grep -v 'add to test cases' | grep '^curl' | while read cmd; do 
  echo "echo executing - $cmd"; 
  echo "$cmd -v --fail || echo failed: $cmd";
  echo "echo"; 
  echo "echo -e ---------------"; 
done >> $testscript && chmod +x $testscript
