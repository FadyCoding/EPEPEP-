import json
import os

def generate_md_report(json_file, loc_dir, output_dir, mapping_file):
    """
    Generate a Markdown report from the JSON analysis file and LOC directory.
    """
    # Load the JSON analysis file
    try:
        with open(json_file, "r") as file:
            analysis_data = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    # Load the account mapping file
    account_mapping = {}
    if mapping_file:
        try:
            with open(mapping_file, "r") as file:
                account_mapping = json.load(file)
        except Exception as e:
            print(f"Error reading account mapping file: {e}")
            return

    # Load the LOC data
    loc_data = load_loc_data(loc_dir)

    # Generate the Markdown report
    report = generate_report(analysis_data, loc_data, account_mapping)

    # Write the report to the output directory
    output_file = os.path.join(output_dir, "report.md")
    with open(output_file, "w") as file:
        file.write(report)

    print(f"Markdown report generated: {output_file}")