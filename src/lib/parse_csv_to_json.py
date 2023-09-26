import json
import argparse

from pathlib import Path
from typing import List, Tuple

import pandas as pd


def get_input_output_path(args) -> Tuple[Path, Path]:
    input_path = args.input_file.resolve()
    if not input_path.exists():
        raise ValueError(f"The input path '{input_path}' did not exist!")
    if args.output_file is None:
        output_path = input_path.with_name("all_codes.json")
    else:
        output_path = args.output_file.resolve()
    return input_path, output_path

def get_test_manifest(args):
    test_manifest = None
    if args.test_manifest is not None:
        manifest_path = args.test_manifest.resolve()
        with open(manifest_path) as f:
            test_manifest = json.load(f)
    return test_manifest

def get_df(input_fpath: Path, ignore_cols: List[str], test_manifest) -> pd.DataFrame:
    df = pd.read_csv(input_fpath)
    if len(ignore_cols) > 0:
        df.drop(columns=ignore_cols, inplace=True)
    number_of_nan = df.isna().sum()
    if number_of_nan.sum() > 0:
        print(
            f"WARNING! For each column NaN values were found in the csv file!",
            f"\n{number_of_nan}\n"
            "Replacing those values with the empty string."
        )
    df.fillna("", inplace=True)

    if test_manifest is not None:
        df.index = test_manifest

    index = pd.MultiIndex.from_product([df.index, df.columns])
    path_index = ["/".join(idx) for idx in index]
    codes = pd.Series([df.loc[idx] for idx in index], index=path_index)

    def clean_codes(code):
        return code.replace("`", "").strip()

    return codes.map(clean_codes)
    
def output_df(df: pd.DataFrame, output_fpath: Path):
    # Get rid of extra backslashes when using pd.to_json()
    json_str = df.to_json()
    parsed = json.loads(json_str)
    print(f"Output file to {output_fpath}")
    with open(output_fpath, "w") as f:
        json.dump(parsed, f, indent=4)

def main(args):
    input_path, output_path = get_input_output_path(args)
    test_manifest = get_test_manifest(args)
    codes = get_df(input_path, args.ignore_cols, test_manifest)
    output_df(codes, output_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_file', type=Path,
        help="Path to the input csv file."
    )
    parser.add_argument(
        '-o', '--output_file', type=Path,
        help=(
            "Path to the output file. If not provided the output will be "
            "created in the same dir as the input file with the name all_codes.json"
        )
    )
    parser.add_argument(
        '-t', '--test_manifest', type=Path,
        help=(
            "Path to a json file that has the list of APPS question tested. "
            "This list MUST be in the same order as the csv file. "
            "The entires in the list MUST be the full path to the APPS problem "
            "directory where the 'input_output.json' file that contains the unit test is."
        )
    )
    parser.add_argument(
        '-i', '--ignore_cols', nargs='+',
        help="Which columns to ignore in .csv file when creating json file."
    )
    args = parser.parse_args()
    print(args)

    main(args)