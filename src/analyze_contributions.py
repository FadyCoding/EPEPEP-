import os
import subprocess
import json
from collections import defaultdict


def analyze_total_loc(repo_path):
    loc_data = defaultdict(lambda: {"added": 0, "deleted": 0})
    result = subprocess.run(
        ["git", "log", "--numstat", "--pretty=%H", "-C", repo_path],
        stdout=subprocess.PIPE,
        text=True,
    )
    lines = result.stdout.splitlines()

    current_commit = None
    for line in lines:
        if len(line) == 40:  # SHA length (commit hash)
            current_commit = line
        elif "\t" in line and current_commit:
            added, deleted, _ = line.split("\t")
            try:
                loc_data[current_commit]["added"] += (
                    int(added) if added.isdigit() else 0
                )
                loc_data[current_commit]["deleted"] += (
                    int(deleted) if deleted.isdigit() else 0
                )
            except ValueError:
                print(f"Skipping binary file entry in commit {current_commit}: {line}")

    return loc_data


def analyze_final_loc(repo_path):
    # Get all tracked files without changing directories
    result = subprocess.run(
        ["git", "-C", repo_path, "ls-files"],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    files = result.stdout.splitlines()

    # Collect the final LOC for each author
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

    # Calculate the total LOC across all authors
    total_lines = sum(final_loc.values())

    # Build the final LOC data structure with percentage
    final_loc_with_percentage = {
        author: {
            "lines": loc,
            "percentage": (loc / total_lines) * 100 if total_lines > 0 else 0
        }
        for author, loc in final_loc.items()
    }

    return final_loc_with_percentage



def analyze_contribution_per_root_folder(repo_path):
    # For each contributor commits
    # List the modified file path
    # Get the root folder
    # Add +1 to root folder
    # Display the % of root folder contribution for the contributor

    # Get all contributors
    result = subprocess.run(
        ["git", "-C", repo_path, "shortlog", "-sne"],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    contributors = result.stdout.splitlines()

    root_folder_contributions = (
        {}
    )  # Contributor -> Root Folder -> { Contrib. count, contrib. % }
    total_root_folder_commits = defaultdict(int)  # Root Folder -> Total Commits count

    # Process each contributor
    for contributor in contributors:

        # Get the contributor name
        contributor_name = contributor.split("\t")[-1].strip()
        contributor_name = contributor_name.split("<")[0].strip()
        root_folder_contributions[contributor_name] = {}

        # Get the contributor commits
        result = subprocess.run(
            [
                "git",
                "-C",
                repo_path,
                "log",
                "--author=" + contributor_name,
                "--pretty=%H",
            ],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        commits = result.stdout.splitlines()

        # Process each commit
        for commit in commits:
            this_commit_root_folders = set()
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    repo_path,
                    "show",
                    "--name-only",
                    "--pretty=",
                    "--oneline",
                    commit,
                ],
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            files = result.stdout.splitlines()

            # Ignore the commit message (first line)
            files = files[1:]

            # Get the root folder for each modified file
            for file in files:
                root_folder = file.split("/", 1)[0]
                if not root_folder:
                    continue

                # Add the root folder to the set (so that we only count it once per commit)
                this_commit_root_folders.add(root_folder)

            # Add +1 to each root folder and update the total commits for that root folder
            for root_folder in this_commit_root_folders:
                if root_folder not in root_folder_contributions[contributor_name]:
                    root_folder_contributions[contributor_name][root_folder] = {
                        "contributions": 0,
                        "percentage": 0,
                    }
                root_folder_contributions[contributor_name][root_folder][
                    "contributions"
                ] += 1
                total_root_folder_commits[root_folder] += 1

    # Calculate the percentage of contribution for each root folder
    for contributor_name, folders in root_folder_contributions.items():
        # Get the root folder contributions with percentage
        for root_folder, contrib in folders.items():
            total_commits = total_root_folder_commits[root_folder]
            if total_commits > 0:
                percentage_contribution = (
                    contrib["contributions"] / total_commits
                ) * 100
            else:
                percentage_contribution = 0

            root_folder_contributions[contributor_name][root_folder][
                "percentage"
            ] = percentage_contribution

    # Sort the root folders by contribution
    for contributor_name, folders in root_folder_contributions.items():
        root_folder_contributions[contributor_name] = dict(
            sorted(
                folders.items(),
                key=lambda item: item[1]["contributions"],
                reverse=True,
            )
        )

    return root_folder_contributions


def merge_accounts(final_loc, account_mapping):
    merged_final_loc = defaultdict(lambda: {"lines": 0, "percentage": 0})

    # Merge LOC values
    for account, data in final_loc.items():
        main_account = account_mapping.get(account, account)
        merged_final_loc[main_account]["lines"] += data["lines"]

    # Recalculate percentages after merging
    total_lines = sum(data["lines"] for data in merged_final_loc.values())
    for account, data in merged_final_loc.items():
        data["percentage"] = (data["lines"] / total_lines * 100) if total_lines > 0 else 0

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

        # Analyze contribution per root folder
        root_folder_loc = analyze_contribution_per_root_folder(repo_path)

        # Merge accounts if mapping is provided
        if account_mapping:
            final_loc = merge_accounts(final_loc, account_mapping)

        # Prepare report data
        report = {
            "Total LOC": total_loc,
            "Final LOC": final_loc,
            "Root Folder LOC": root_folder_loc,
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
    with open("./my_repos_info.json", "r") as file:
        repos = json.load(file)

    # Optional account mapping
    account_mapping = {
        "FadyCoding": "Fady B.",
        "DebiAI Author": "DebiAI Contributor",
        # Add more mappings if necessary
    }

    output_directory = "./loc_reports"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    generate_report(repos, account_mapping, output_dir=output_directory)
