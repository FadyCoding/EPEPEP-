import os
import subprocess
import json
import math
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


def calculate_grades(per_member_commits_data, per_member_lines_data):
    """
    Calculate grades based on the per member commits data.

    Grade calculation:
    The expected number of commits and lines added are calculated
    based on the number of members and the total number of commits.
    The grades are assigned as follows:
    If a member nb_commits >= expected_nb_commits: commit_grade = 20
    else: commit_grade = 20 * (nb_commits / expected_nb_commits)
    If a member total >= expected_total: loc_grade = 20
    else: loc_grade = 20 * (total / expected_total)
    """

    nb_members = len(per_member_commits_data)

    # Calculate total number of commits
    total_commits = sum(data["nb_commits"] for data in per_member_commits_data.values())

    # Get total LOC
    total = sum(data["lines"] for data in per_member_lines_data.values())

    # Calculate expected number of commits and total LOC
    expected_nb_commits = total_commits / nb_members
    expected_total = total / nb_members

    # Calculate grades
    grades = {}
    for member, data in per_member_commits_data.items():
        loc_data = per_member_lines_data.get(member)
        commit_grade = 20
        loc_grade = 20

        if data["nb_commits"] < expected_nb_commits:
            commit_grade = 20 * (data["nb_commits"] / expected_nb_commits)

        if loc_data["lines"] < expected_total:
            loc_grade = 20 * (loc_data["lines"] / expected_total)

        grades[member] = {
            "nb_commits": data["nb_commits"],
            "expected_nb_commits": round(expected_nb_commits, 2),
            "commit_grade": round(commit_grade, 2),
            "total": loc_data["lines"],
            "expected_total": round(expected_total, 2),
            "loc_grade": round(loc_grade, 2),
            "final_grade": round((commit_grade + loc_grade) / 2, 2),
        }

    return grades


def analyze_total_loc(repo_path, account_mapping):
    """
    Analyze total lines of code (LOC) added, deleted, and total changes.
    """
    print("  Analyzing total LOC...")
    total_loc = {"added": 0, "deleted": 0}
    per_member_data = {}

    repo = Repo(repo_path)

    IGNORED_COMMITS_MESSAGES_KEYWORDS = [
        "merge",
        "Merge",
        "Merged",
    ]

    # Iterate over all commits
    for commit in repo.iter_commits():
        # Skip ignored commits
        if any(
            keyword in commit.message for keyword in IGNORED_COMMITS_MESSAGES_KEYWORDS
        ):
            continue

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

        # if commit.stats.total["lines"] > 3000:
        #     print(f"      - {author}: {commit.hexsha}")
        #     print(f"        Added: {commit.stats.total['insertions']}")
        #     print(f"        Deleted: {commit.stats.total['deletions']}")
        #     print(f"        Total: {commit.stats.total['lines']}")
        #     print(f"        Message: {commit.message}")
        #     print()

    # Sort the data by number of commits
    per_member_data = dict(
        sorted(
            per_member_data.items(),
            key=lambda item: item[1]["nb_commits"],
            reverse=True,
        )
    )

    return {
        "total": total_loc,
        "data": per_member_data,
    }


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
    contributed_files = {}
    ignored_files = {}

    # Add members that are in the mapping
    # (so that even members with no LOC are included in the final report)
    for author in account_mapping.values():
        final_loc[author] = 0
        contributed_files[author] = {}

    # Calculate LOC for each file
    unknown_authors = set()
    files_extension = set()
    EXCLUDED_EXTENSIONS = [
        "json",
        "yml",
        "yaml",
        "lock",
        "mjs",
        "txt",
        "jpg",
        "webp",
        "jpeg",
        "svg",
        "ico",
        "png",
        "gif",
        "jpeg",
        "less",
        "map",
        "xml",
        "bat",
        "csv",
        "pkl",
        "xls",
        "docx",
        "ppt",
        "pptx",
        "pdf",
        "zip",
        "tar",
        "gz",
        "7z",
        "rar",
        "bin",
        "exe",
        "ttf",
        "woff",
        "woff2",
        "ipynb",
        "LICENSE",
        "mp3",
        "mp4",
        "avi",
        "mov",
        "wav",
        "avif",
    ]
    EXCLUDED_PATH = [
        "node_modules",
        "public/",
        "venv",
        "env/",
        "dist",
        "build",
        ".vs",
        ".avif",
        "__pycache__/",
        "assets/img/icon/",
    ]
    files_sizes = {}
    for file in files:
        # Check if the file is excluded from the analysis
        file_extension = file.split(".")[-1]
        if file_extension in EXCLUDED_EXTENSIONS:
            if file_extension not in ignored_files:
                ignored_files[file_extension] = {
                    "files": set(),
                    "reason": "Extension",
                }
            ignored_files[file_extension]["files"].add(file)
            continue

        # Check if the file is in an excluded folder
        excluded_folder = None
        for folder in EXCLUDED_PATH:
            if folder in file:
                excluded_folder = folder
                break

        if excluded_folder:
            if "path" not in ignored_files:
                ignored_files[excluded_folder] = {
                    "files": set(),
                    "reason": "Path",
                }
            ignored_files[excluded_folder]["files"].add(file)
            continue

        # Count the LOC for each file
        files_sizes[file] = 0
        files_extension.add(file_extension)
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
                    if file not in contributed_files[author]:
                        contributed_files[author][file] = 0
                    contributed_files[author][file] += 1
                else:
                    unknown_authors.add(author)
                files_sizes[file] += 1

    if unknown_authors:
        print(f"Unmapped authors: {unknown_authors}")

    # Display some data about the files:
    # Sort files by size
    # files_sizes = dict(sorted(files_sizes.items(), key=lambda item: item[1], reverse=True))
    # for file, size in files_sizes.items():
    #     print(f"{file}: {size}")
    # print(f"Files extensions: {files_extension}")

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

    # Add the percentage of LOC for each file
    for author, files in contributed_files.items():
        for file, loc in files.items():
            contributed_files[author][file] = {
                "lines": loc,
                "percentage": (
                    math.ceil((loc / files_sizes[file]) * 100) if files_sizes[file] > 0 else 0
                ),
            }

        # Sort contributed files by the number of lines
        contributed_files[author] = dict(
            sorted(
                contributed_files[author].items(),
                key=lambda item: item[1]["lines"],
                reverse=True,
            )
        )

    # Sort ignored files and extensions by the number of files
    ignored_files = dict(
        sorted(
            ignored_files.items(),
            key=lambda item: len(item[1]["files"]),
            reverse=True,
        )
    )
    # Convert sets to lists
    for key, value in ignored_files.items():
        ignored_files[key]["files"] = list(value["files"])

    return {
        "total": total_lines,
        "data": final_loc_with_percentage,
        "contributed_files": contributed_files,
        "ignored_files": ignored_files,
    }


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
        "Grades": calculate_grades(total_loc["data"], final_loc["data"]),
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
