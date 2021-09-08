#!/bin/bash


kli status --name han > /dev/null 2>&1

if [ $? -eq 0 ]
then
  echo "Identifier prefix exists, launching wallet."
else
  echo "Identifier prefix does not exist, running incept"
  kli incept --name han --file tests/app/cli/holder-sample.json
  kli send --name han --target 5621
  kli query --name han --witness Bgoq68HCmYNUDgOz4Skvlu306o_NY-NrYuKAVhk3Zh9c --prefix EeS834LMlGVEOGR8WU3rzZ9M6HUv_vtF32pSXQXKP7jg
fi

kli wallet start --name han
