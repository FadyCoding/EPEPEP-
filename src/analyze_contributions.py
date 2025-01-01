import os
import subprocess
import json
from collections import defaultdict


def analyze_total_loc(repo_path):
    loc_data = defaultdict(lambda: {"added": 0, "deleted": 0})
    result = subprocess.run(
        ["git", "log", "--numstat", "--pretty=%H", "-C", repo_path], stdout=subprocess.PIPE, text=True
    )
    lines = result.stdout.splitlines()

    current_commit = None
    for line in lines:
        if len(line) == 40:  # SHA length (commit hash)
            current_commit = line
        elif "\t" in line and current_commit:
            added, deleted, _ = line.split("\t")
            try:
                loc_data[current_commit]["added"] += int(added) if added.isdigit() else 0
                loc_data[current_commit]["deleted"] += int(deleted) if deleted.isdigit() else 0
            except ValueError:
                print(f"Skipping binary file entry in commit {current_commit}: {line}")

    return loc_data


def analyze_final_loc(repo_path):
    # Get all tracked files without changing directories
    result = subprocess.run(
        ["git", "-C", repo_path, "ls-files"], stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
    )
    files = result.stdout.splitlines()

    final_loc = defaultdict(int)
    for file in files:
        blame_result = subprocess.run(
            ["git", "-C", repo_path, "blame", "-w", "--line-porcelain", file],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        lines = blame_result.stdout.splitlines()

        for line in lines:
            if line.startswith("author "):
                author = line.split(" ", 1)[1]
                final_loc[author] += 1

    return final_loc


def merge_accounts(final_loc, account_mapping):
    merged_final_loc = defaultdict(int)
    for account, loc in final_loc.items():
        main_account = account_mapping.get(account, account)
        merged_final_loc[main_account] += loc

    return merged_final_loc


def generate_report(repos, account_mapping=None, output_dir="."):
    """
    Generate LOC reports for repositories and save them in the specified directory.

    Args:
        repos (dict): Dictionary mapping repo URLs to their local paths.
        account_mapping (dict): Optional mapping of account names to a unified name.
        output_dir (str): Directory where the reports will be saved.
    """
    # Ensure output directory exists
    output_dir = os.path.abspath(output_dir)

    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    for repo_url, repo_path in repos.items():
        print(f"Analyzing repository: {repo_url}")
        
        # Analyze LOC
        total_loc = analyze_total_loc(repo_path)
        final_loc = analyze_final_loc(repo_path)

        # Merge accounts if mapping is provided
        if account_mapping:
            final_loc = merge_accounts(final_loc, account_mapping)

        # Prepare report data
        report = {
            "Total LOC": total_loc,
            "Final LOC": final_loc,
        }

        # Build the file name for the report
        report_filename = f"{os.path.basename(repo_path)}_loc_report.json"
        report_path = os.path.join(output_dir, report_filename)

        # Debug: Show where the file will be saved
        print(f"Saving report to: {os.path.abspath(report_path)}")

        # Write the report to the file
        try:
            with open(report_path, "w") as report_file:
                json.dump(report, report_file, indent=4)
            print(f"Report successfully saved: {report_path}")
        except Exception as e:
            print(f"Error saving report for {repo_url}: {e}")


if __name__ == "__main__":
    # Load the JSON file containing cloned repos
    with open("./data/cloned_repos.json", "r") as file:
        repos = json.load(file)

    # Optional account mapping
    account_mapping = {
        "FadyCoding": "Fady B.",
        "DebiAI Author": "DebiAI Contributor",
        # Add more mappings if necessary
    }

    # Specify the output directory
    output_directory = "./loc_reports"

    # Ensure the directory exists (if needed)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Generate reports
    generate_report(repos, account_mapping, output_dir=output_directory)
