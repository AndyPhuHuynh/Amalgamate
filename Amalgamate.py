import os
import re
import argparse

from typing import List, TextIO, Set

script_dir = os.path.dirname(os.path.abspath(__file__))

def is_pragma_once(line: str) -> bool:
    return bool(re.match(r'^\s*#\s*pragma\s*once\b', line))


def is_local_include(line: str) -> bool:
    return bool(re.match(r'\s*#include\s*"(.+)"', line))


def get_include_filename(line: str) -> str:
    match = re.match(r'\s*#include\s*"(.+)"', line)
    if match:
        return match.group(1)
    else:
        return ""


def get_include_filepath(input_filepath: str, include_dirs: List[str], include_name: str) -> str:
    base_directory = os.path.dirname(input_filepath)
    base_input: str = os.path.join(base_directory, include_name)
    if (os.path.exists(os.path.join(base_directory, include_name))):
        return base_input
    
    for dir in include_dirs:
        include_path = os.path.join(dir, include_name)
        if (os.path.exists(include_path)):
            return include_path
    
    raise FileNotFoundError("Include not found: " + include_name + " inside file: " + input_filepath)


def expand_include(output_file : TextIO, input_filepath: str, line : str, include_dirs: List[str], dont_include : Set[str]) -> None:
    include_name: str = get_include_filename(line)
    if include_name == "":
        print(f"Invalid include: {line}")
        return

    full_include_path: str = get_include_filepath(input_filepath, include_dirs, include_name)
    if full_include_path not in dont_include:
        process_file(output_file, full_include_path, include_dirs, dont_include)
    else:
        print(f"Skipping {full_include_path}")


def process_file(output_file : TextIO, input_file_full_path : str, include_dirs: List[str], dont_include : Set[str]) -> None:
    with open(input_file_full_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            # Include directive
            if is_local_include(line):
                expand_include(output_file, input_file_full_path, line, include_dirs, dont_include)
            # Pragma once
            elif is_pragma_once(line):
                print(f"Pragma once {input_file_full_path}")
                dont_include.add(os.path.abspath(input_file_full_path))
            # Other
            else:
                output_file.write(line)
        output_file.write("\n")


def process_directory(output: TextIO, directory: str, skip_files: Set[str], include_dirs: List[str]) -> None:
    output.write("#pragma once\n")
    dont_include = set()

    for filename in os.listdir(directory):
        filepath: str = os.path.abspath(os.path.join(directory, filename))
        if filepath in skip_files or filepath in dont_include:
            continue

        # Hpp file
        isHeader: bool = filepath.endswith(".h") or\
                        filepath.endswith(".hpp")
        if os.path.isfile(filepath) and isHeader:
            print(f"Found file: {filepath}")
            process_file(output, filepath, include_dirs, dont_include)


def main():
    parser = argparse.ArgumentParser(description="Header preprocessor")
    parser.add_argument("-D", "--directory", action="append", default=[], help="Directory containing header files")
    parser.add_argument("-I", "--include",   action="append", default=[], help="Additional include directories")
    args = parser.parse_args()

    error_msgs: List[str] = []

    for dir in args.directory:
        if not os.path.isdir(dir):
            error_msgs.append(f"'{dir}' is not a valid directory.")
        
    for dir in args.include:
        if not os.path.isdir(dir):
            error_msgs.append(f"'{dir}' is not a valid directory.")

    if len(error_msgs) > 0:
        for err in error_msgs:
            print(err)
        return
        

    abs_output_path = os.path.abspath("Output.txt")
    with open(abs_output_path, "w") as output:
        for directory in args.directory:
            process_directory(output, directory, {abs_output_path}, args.include)


if __name__ == "__main__":
    main()