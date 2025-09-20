#!/usr/bin/env python3
# test_bench.py
#
# A script to automate testing for the scheduler-gpt.py process scheduler.

import sys
import os
import subprocess
import difflib

# --- Configuration ---
# The name of the scheduler script to be tested.
SCHEDULER_SCRIPT = "scheduler-gpt.py"

def compare_files(file1_path, file2_path):
    """
    Compares two files line by line, ignoring leading/trailing whitespace.

    Args:
        file1_path (str): Path to the first file.
        file2_path (str): Path to the second file.

    Returns:
        bool: True if the files are identical after stripping lines, False otherwise.
    """
    try:
        with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
            # Read all lines and strip whitespace from each line for comparison
            lines1 = [line.strip() for line in f1.readlines()]
            lines2 = [line.strip() for line in f2.readlines()]
            return lines1 == lines2
    except FileNotFoundError:
        return False

def print_diff(reference_path, generated_path):
    """
    Prints a unified diff of two files to the console.

    Args:
        reference_path (str): Path to the reference (expected) file.
        generated_path (str): Path to the generated (actual) file.
    """
    print("-" * 70)
    print(f"DIFFERENCES for {os.path.basename(generated_path)}:")
    try:
        with open(reference_path, 'r') as f1, open(generated_path, 'r') as f2:
            reference_lines = f1.readlines()
            generated_lines = f2.readlines()

        diff = difflib.unified_diff(
            reference_lines,
            generated_lines,
            fromfile=f"Reference: {reference_path}",
            tofile=f"Generated: {generated_path}",
            lineterm=''
        )
        
        # Print each line of the generated diff
        for line in diff:
            print(line)
            
    except FileNotFoundError:
        print(f"Error: Could not open one of the files for diffing.")
    print("-" * 70)


def main():
    """
    Main function to drive the test bench. Discovers, runs, and evaluates tests.
    """
    # 1. Command-Line Argument Check
    if len(sys.argv) != 2:
        print(f"Usage: python3 {os.path.basename(sys.argv[0])} <test_case_directory>")
        sys.exit(1)

    test_dir = sys.argv[1]

    if not os.path.isdir(test_dir):
        print(f"Error: Directory not found at '{test_dir}'")
        sys.exit(1)

    if not os.path.isfile(SCHEDULER_SCRIPT):
        print(f"Error: Scheduler script '{SCHEDULER_SCRIPT}' not found in the current directory.")
        sys.exit(1)

    print("Starting scheduler test bench...")

    # 2. Test Discovery
    test_files = sorted([f for f in os.listdir(test_dir) if f.endswith('.in')])

    if not test_files:
        print(f"No test cases (.in files) found in '{test_dir}'.")
        sys.exit(0)

    pass_count = 0
    fail_count = 0

    for input_filename in test_files:
        base_name = os.path.splitext(input_filename)[0]
        output_filename = f"{base_name}.out"

        input_filepath = os.path.join(test_dir, input_filename)
        reference_output_filepath = os.path.join(test_dir, output_filename)
        
        # The scheduler generates its output in the current working directory
        generated_output_filepath = os.path.join(os.getcwd(), output_filename)

        # Ensure no old generated file exists before the test run
        if os.path.exists(generated_output_filepath):
             os.remove(generated_output_filepath)

        try:
            # 3. Execution
            # CORRECTION: Use sys.executable to ensure we use the same Python
            # interpreter that is running this test script. This is more robust
            # than hardcoding 'python3'.
            command = [sys.executable, SCHEDULER_SCRIPT, input_filepath]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10 # Add a timeout to prevent hanging
            )

            if result.returncode != 0:
                print(f"[FAIL] Test: {input_filename} (Scheduler script exited with an error)")
                print("--- STDERR ---")
                print(result.stderr or "No stderr output.")
                print("--- STDOUT ---")
                print(result.stdout or "No stdout output.")
                fail_count += 1
                continue

            if not os.path.exists(generated_output_filepath):
                print(f"[FAIL] Test: {input_filename} (Scheduler did not generate an output file)")
                fail_count += 1
                continue
            
            # 4. Comparison
            if compare_files(reference_output_filepath, generated_output_filepath):
                # 5. Reporting - PASS
                print(f"[PASS] Test: {input_filename}")
                pass_count += 1
            else:
                # 5. Reporting - FAIL
                print(f"[FAIL] Test: {input_filename}")
                fail_count += 1
                print_diff(reference_output_filepath, generated_output_filepath)

        except subprocess.TimeoutExpired:
            print(f"[FAIL] Test: {input_filename} (Execution timed out)")
            fail_count += 1
        except Exception as e:
            print(f"[FAIL] Test: {input_filename} (An unexpected error occurred)")
            print(e)
            fail_count += 1
        finally:
            # 6. Cleanup
            if os.path.exists(generated_output_filepath):
                os.remove(generated_output_filepath)
    
    print("\n" + "="*30)
    print("        Test Summary")
    print("="*30)
    print(f"Passed: {pass_count}")
    print(f"Failed: {fail_count}")
    print("="*30)

if __name__ == "__main__":
    main()