#!/usr/bin/env bash
DATA=`lpass show pypi.org -j`
export TWINE_USERNAME=`echo $DATA | jq -r ".[].username"`
export TWINE_PASSWORD=`echo $DATA | jq -r ".[].password"`