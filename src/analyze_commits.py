import git
from collections import defaultdict
import os
import json


def fetch_branches(repo):
    """
    Fetch all branches (local and remote) for a repository.

    Parameters:
    - repo (git.Repo): The Git repository object.

    Returns:
    - list: A list of unique branch names.
    """
    try:
        repo.git.fetch("--all", "--prune")
        branches = [ref.name for ref in repo.branches]  # Local branches
        branches.extend([ref.name for ref in repo.remote().refs])  # Remote branches

        # Clean branch names and remove invalid entries
        branches = [
            branch for branch in sorted(set(branches))
            if not branch.startswith("remotes/origin/HEAD")  # Skip HEAD references
        ]
        return branches
    except Exception as e:
        print(f"Error fetching branches: {e}")
        return []


def count_unique_commits_for_branches(repo, branches):
    """
    Count the total number of unique commits across all branches in a repository.

    Parameters:
    - repo (git.Repo): The Git repository object.
    - branches (list): A list of branch names.

    Returns:
    - int: Total number of unique commits across all branches.
    """
    unique_commits = set()  # Use a set to store unique commit hashes

    for branch in branches:
        try:
            branch_commits = repo.iter_commits(branch)
            unique_commits.update(commit.hexsha for commit in branch_commits)
        except Exception as e:
            print(f"Skipping branch '{branch}' due to error: {e}")

    return len(unique_commits)


def analyze_commits(repo_dir):
    """
    Analyze commit activity for a given Git repository.

    Parameters:
    - repo_dir (str): Path to the local Git repository.

    Returns:
    - dict: A summary of commit activity including the repository name.
    """
    try:
        repo = git.Repo(repo_dir)
        repo_title = os.path.basename(repo_dir)

        # Count commits per author and store commit dates
        commits = list(repo.iter_commits("HEAD"))
        commit_summary = defaultdict(int)
        commit_dates = []
        for commit in commits:
            author = commit.author.name
            commit_summary[author] += 1
            commit_dates.append((author, commit.committed_datetime))

        commit_dates.sort(key=lambda x: x[1])

        branches = fetch_branches(repo)

        return {
            "repository": repo_title,
            "total_commits": len(commits),
            "commits_per_member": dict(commit_summary),
            "commit_dates": commit_dates,
            "branches": branches,
        }

    except Exception as e:
        print(f"Error analyzing commits in '{repo_dir}': {e}")
        return {}


def calculate_average_commits_per_branch(repo_dir):
    """
    Calculate the average number of commits per branch in a repository.

    Parameters:
    - repo_dir (str): Path to the local Git repository.

    Returns:
    - float: Average commits per branch.
    """
    try:
        repo = git.Repo(repo_dir)
        branches = fetch_branches(repo)

        if not branches:
            return 0

        total_unique_commits = count_unique_commits_for_branches(repo, branches)
        return total_unique_commits / len(branches)

    except Exception as e:
        print(f"Error calculating average commits for branches in '{repo_dir}': {e}")
        return 0


def analyze_multiple_repos_from_json(json_file_path):
    """
    Analyze commits for multiple repositories listed in a JSON file.

    Parameters:
    - json_file_path (str): Path to the JSON file containing repository paths.

    Returns:
    - list: A summary of commit activity for all repositories.
    """
    try:
        with open(json_file_path, "r") as file:
            repo_data = json.load(file)

        repo_dirs = list(repo_data.values())
        print(f"Found {len(repo_dirs)} repositories to analyze.")

        all_repo_analysis = []

        for repo_dir in repo_dirs:
            if os.path.exists(repo_dir) and os.path.isdir(repo_dir):
                print(f"Analyzing repository: {repo_dir}")
                analysis = analyze_commits(repo_dir)
                if analysis:
                    all_repo_analysis.append(analysis)
            else:
                print(f"Invalid repository path: {repo_dir}")

        return all_repo_analysis

    except Exception as e:
        print(f"Error reading JSON file or analyzing repositories: {e}")
        return []


if __name__ == "__main__":
    json_file_path = "./my_repos_info.json"

    print("Analyzing repositories listed in the JSON file...")
    all_analysis = analyze_multiple_repos_from_json(json_file_path)

    for repo_analysis in all_analysis:
        print("\nRepository:", repo_analysis["repository"])
        print("  Total Commits:", repo_analysis["total_commits"])
        print("  Commits Per Member:")
        for author, count in repo_analysis["commits_per_member"].items():
            print(f"    - {author}: {count} commits")
        print("  Branches:")
        for branch in repo_analysis["branches"]:
            print(f"    - {branch}")
