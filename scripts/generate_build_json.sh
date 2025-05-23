#!/bin/bash
# This script takes the code repo as the input and generates a build.json file.
git describe --tags | jq -R '{"open5e-api-version":.}' > build.json
