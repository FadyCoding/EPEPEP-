import os
import subprocess
import json
from collections import defaultdict
from git import Repo


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
    print("  Analyzing total LOC...")
    total_loc = {"added": 0, "deleted": 0}
    per_member_data = {}

    repo = Repo(repo_path)

    # Iterate over all commits
    for commit in repo.iter_commits():
        # Store the total LOC changes
        total_loc["added"] += commit.stats.total["insertions"]
        total_loc["deleted"] += commit.stats.total["deletions"]

        # Store the LOC changes per member
        author = commit.author.name
        author = account_mapping.get(author, None)
        if author is None:
            continue

        if author not in per_member_data:
            per_member_data[author] = {
                "added": 0,
                "deleted": 0,
                "total": 0,
                "nb_commits": 0,
                "messages": [],
            }

        per_member_data[author]["added"] += commit.stats.total["insertions"]
        per_member_data[author]["deleted"] += commit.stats.total["deletions"]
        per_member_data[author]["total"] += commit.stats.total["lines"]
        per_member_data[author]["nb_commits"] += 1
        per_member_data[author]["messages"].append(commit.message)

    # Sort the data by number of commits
    per_member_data = dict(
        sorted(
            per_member_data.items(),
            key=lambda item: item[1]["nb_commits"],
            reverse=True,
        )
    )

    return {"total": total_loc, "data": per_member_data}


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

    # Add members that are in the mapping
    # (so that even members with no LOC are included in the final report)
    for author in account_mapping.values():
        final_loc[author] = 0

    # Calculate LOC for each file
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
                author = account_mapping.get(author, None)
                if author is not None:
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
        mapped_contributor_name = account_mapping.get(contributor_name, None)
        if mapped_contributor_name is None:
            print(f"Skipping unmapped contributor: {contributor_name}")
            continue
        if mapped_contributor_name not in root_folder_contributions:
            root_folder_contributions[mapped_contributor_name] = {}

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
                if (
                    root_folder
                    not in root_folder_contributions[mapped_contributor_name]
                ):
                    root_folder_contributions[mapped_contributor_name][root_folder] = {
                        "contributions": 0,
                        "percentage": 0,
                    }
                root_folder_contributions[mapped_contributor_name][root_folder][
                    "contributions"
                ] += 1
                total_root_folder_commits[root_folder] += 1

    for contributor_name, folders in root_folder_contributions.items():
        for root_folder, contrib in folders.items():
            total_commits = total_root_folder_commits[root_folder]
            contrib["percentage"] = (
                (contrib["contributions"] / total_commits) * 100
                if total_commits > 0
                else 0
            )
            contrib["total_commits"] = total_commits

    for contributor_name, folders in root_folder_contributions.items():
        root_folder_contributions[contributor_name] = dict(
            sorted(
                folders.items(), key=lambda item: item[1]["contributions"], reverse=True
            )
        )

    return root_folder_contributions


def generate_loc_report(repo_path, account_mapping):
    total_loc = analyze_total_loc(repo_path, account_mapping)
    final_loc = analyze_final_loc(repo_path, account_mapping)
    root_folder_loc = analyze_contribution_per_root_folder(repo_path, account_mapping)

    return {
        "Total LOC": total_loc,
        "Final LOC": final_loc,
        "Root Folder LOC": root_folder_loc,
    }


def generate_reports(repos, account_mapping, output_dir="."):
    """
    Generate LOC reports for repositories and save them in the specified directory.
    """
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    for repo_url, repo_path in repos.items():
        print(f"Analyzing repository: {repo_url}")

        report = generate_loc_report(repo_path, account_mapping)
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

    generate_reports(repos, account_mapping, output_dir=output_directory)
