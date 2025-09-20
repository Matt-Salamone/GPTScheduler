import os

def combine_io_files(output_filename="inputs_outputs.txt"):
    """
    Finds all '.in' and '.out' files in the current directory,
    groups them by name, and combines their contents into a
    single specified output file.

    Args:
        output_filename (str): The name of the file to write the combined
                               contents to. Defaults to "inputs_outputs.txt".
    """
    try:
        # Get a list of all files in the current directory
        all_files = os.listdir('.')

        # Filter to get only the '.in' files and sort them for consistent order
        in_files = sorted([f for f in all_files if f.endswith('.in')])

        if not in_files:
            print("No '.in' files found in this directory.")
            return

        print(f"Found {len(in_files)} '.in' file(s). Processing...")

        # Open the output file in write mode, which will overwrite it if it exists
        with open(output_filename, 'w') as outfile:
            # Process each '.in' file
            for in_filename in in_files:
                # Construct the corresponding '.out' filename
                base_name = os.path.splitext(in_filename)[0]
                out_filename = f"{base_name}.out"

                # --- Write .in file content ---
                print(f"  - Processing {in_filename}...")
                outfile.write(f"--Begin {in_filename}--\n")
                with open(in_filename, 'r') as infile:
                    outfile.write(infile.read())
                # Ensure there's a newline before the end delimiter
                outfile.write("\n")
                outfile.write(f"--End {in_filename}--\n")

                # --- Write .out file content if it exists ---
                if out_filename in all_files:
                    print(f"  - Found and processing {out_filename}...")
                    outfile.write(f"--Begin {out_filename}--\n")
                    with open(out_filename, 'r') as outfile_content:
                        outfile.write(outfile_content.read())
                    # Ensure there's a newline before the end delimiter
                    outfile.write("\n")
                    outfile.write(f"--End {out_filename}--\n")
                else:
                    print(f"  - Warning: Corresponding file {out_filename} not found.")
                
                # Add a blank line for better separation between pairs
                outfile.write("\n")

        print(f"\nSuccessfully combined files into '{output_filename}'.")

    except IOError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    combine_io_files()
