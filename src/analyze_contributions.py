import os
import subprocess
import json
from collections import defaultdict


def load_account_mapping(account_mapping_path):
    """
    Load account mapping from a JSON file.
    """
    try:
        with open(account_mapping_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading account mapping: {e}")
        return {}


def analyze_total_loc(repo_path, account_mapping):
    """
    Analyze total lines of code (LOC) added, deleted, and total changes.
    """
    print("Analyzing total LOC...")
    total_loc = {"added": 0, "deleted": 0, "total": 0}
    loc_data = defaultdict(lambda: {"added": 0, "deleted": 0})

    git_dir = os.path.join(repo_path, ".git")
    command = ["git", "--git-dir", git_dir, "log", "--numstat", "--pretty=%H"]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    lines = result.stdout.splitlines()

    current_commit = None
    for line in lines:
        if len(line) == 40:  # SHA length (commit hash)
            current_commit = line
        elif "\t" in line and current_commit:
            added, deleted, _ = line.split("\t")
            added = int(added) if added.isdigit() else 0
            deleted = int(deleted) if deleted.isdigit() else 0
            try:
                loc_data[current_commit]["added"] += added
                loc_data[current_commit]["deleted"] += deleted
                total_loc["added"] += added
                total_loc["deleted"] += deleted
                total_loc["total"] += added - deleted
            except ValueError:
                print(f"Skipping binary file entry in commit {current_commit}: {line}")

    # Apply account mapping
    mapped_loc_data = defaultdict(lambda: {"added": 0, "deleted": 0})
    for commit, stats in loc_data.items():
        author = account_mapping.get(commit, commit)
        mapped_loc_data[author]["added"] += stats["added"]
        mapped_loc_data[author]["deleted"] += stats["deleted"]

    return {"total": total_loc, "data": mapped_loc_data}


def analyze_final_loc(repo_path, account_mapping):
    """
    Analyze the final state of the repository and map contributions.
    """
    result = subprocess.run(
        ["git", "-C", repo_path, "ls-files"],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
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
                author = account_mapping.get(author, author)
                final_loc[author] += 1

    total_lines = sum(final_loc.values())
    final_loc_with_percentage = {
        author: {
            "lines": loc,
            "percentage": (loc / total_lines) * 100 if total_lines > 0 else 0,
        }
        for author, loc in final_loc.items()
    }

    final_loc_with_percentage = dict(
        sorted(
            final_loc_with_percentage.items(),
            key=lambda item: item[1]["lines"],
            reverse=True,
        )
    )

    return {"total": total_lines, "data": final_loc_with_percentage}


def analyze_contribution_per_root_folder(repo_path, account_mapping):
    """
    Analyze contributions per root folder by author.
    """
    result = subprocess.run(
        ["git", "-C", repo_path, "shortlog", "-sne"],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    contributors = result.stdout.splitlines()

    root_folder_contributions = {}
    total_root_folder_commits = defaultdict(int)

    for contributor in contributors:
        contributor_name = contributor.split("\t")[-1].strip()
        contributor_name = contributor_name.split("<")[0].strip()
        contributor_name = account_mapping.get(contributor_name, contributor_name)
        root_folder_contributions[contributor_name] = {}

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
            files = result.stdout.splitlines()[1:]

            for file in files:
                root_folder = file.split("/", 1)[0]
                if not root_folder:
                    continue

                this_commit_root_folders.add(root_folder)

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

    for contributor_name, folders in root_folder_contributions.items():
        for root_folder, contrib in folders.items():
            total_commits = total_root_folder_commits[root_folder]
            contrib["percentage"] = (contrib["contributions"] / total_commits) * 100 if total_commits > 0 else 0
            contrib["total_commits"] = total_commits

    for contributor_name, folders in root_folder_contributions.items():
        root_folder_contributions[contributor_name] = dict(
            sorted(folders.items(), key=lambda item: item[1]["contributions"], reverse=True)
        )

    return root_folder_contributions


def generate_report(repos, account_mapping, output_dir="."):
    """
    Generate LOC reports for repositories and save them in the specified directory.
    """
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    for repo_url, repo_path in repos.items():
        print(f"Analyzing repository: {repo_url}")

        total_loc = analyze_total_loc(repo_path, account_mapping)
        final_loc = analyze_final_loc(repo_path, account_mapping)
        root_folder_loc = analyze_contribution_per_root_folder(repo_path, account_mapping)

        report = {
            "Total LOC": total_loc,
            "Final LOC": final_loc,
            "Root Folder LOC": root_folder_loc,
        }

        report_filename = f"{os.path.basename(repo_path)}_loc_report.json"
        report_path = os.path.join(output_dir, report_filename)

        try:
            with open(report_path, "w") as report_file:
                json.dump(report, report_file, indent=4)
            print(f"Report successfully saved: {report_path}")
        except Exception as e:
            print(f"Error saving report for {repo_url}: {e}")


if __name__ == "__main__":
    with open("./my_repos_info.json", "r") as file:
        repos = json.load(file)

    account_mapping_path = "./account_mapping.json"
    account_mapping = load_account_mapping(account_mapping_path)

    output_directory = "./loc_reports"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    generate_report(repos, account_mapping, output_dir=output_directory)
