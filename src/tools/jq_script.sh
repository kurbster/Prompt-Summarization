#!/bin/bash
jq '[.inputs, .outputs] | transpose | map({(.[0]): .[1]})' input_output.json
