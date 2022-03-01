#!/bin/bash
manifest_file="${1:?You must provide a manifest file}"
output_dir="${2:-agave_data}"
files="$(jq '.[]' ${manifest_file})"
mkdir -p ${output_dir}

for full_file in ${files}; do
    # strip leading "
    full_file="${full_file#\"}"
    # split by the data directory and return last half
    file=${full_file#*"data/"}
    dir="$(dirname ${file})"
    full_dir="$(dirname ${full_file})"
    mkdir -p "${output_dir}/${dir}"
    [[ -f "${full_dir}/starter_code.py" ]] && cp "${full_dir}/starter_code.py" "${output_dir}/${dir}/."
    [[ -f "${full_dir}/input_output.json" ]] && cp "${full_dir}/input_output.json" "${output_dir}/${dir}"
done
