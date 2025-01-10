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
        # Local branches
        branches = [ref.name for ref in repo.branches]
        # Remote branches
        branches.extend([ref.name for ref in repo.remote().refs])

        # Clean branch names and remove invalid entries
        branches = [
            branch.replace("remotes/origin/", "origin/") for branch in sorted(set(branches))
            # Skip HEAD references
            if not branch.startswith("remotes/origin/HEAD")
        ]
        return branches
    except Exception as e:
        print(f"Error fetching branches: {e}")
        return []


def count_unique_commits(repo, branches):
    """
    Count the total number of unique commits
    across all branches in a repository.

    Parameters:
    - repo (git.Repo): The Git repository object.
    - branches (list): A list of branch names.

    Returns:
    - int: Total number of unique commits across all branches.
    """
    unique_commits = set()  # Use a set to track unique commit hashes

    for branch in branches:
        try:
            branch_commits = repo.iter_commits(branch)
            unique_commits.update(commit.hexsha for commit in branch_commits)
        except Exception as e:
            print(f"Skipping branch '{branch}' due to error: {e}")

    return len(unique_commits)


def count_commits_per_branch(repo, branches):
    """
    Count the number of commits for each branch in a repository.

    Parameters:
    - repo (git.Repo): The Git repository object.
    - branches (list): A list of branch names.

    Returns:
    - dict: A dictionary with branch names as keys and commit counts as values.
    """
    branch_commit_counts = {}

    for branch in branches:
        try:
            commit_count = sum(1 for _ in repo.iter_commits(branch))
            branch_commit_counts[branch] = commit_count
        except Exception as e:
            print(f"Skipping branch '{branch}' due to error: {e}")

    return branch_commit_counts


def calculate_average_commits_per_branch(repo_dir):
    """
    Calculate the average number of unique commits per branch in a repository,
    excluding specified branches.

    Parameters:
    - repo_dir (str): Path to the local Git repository.

    Returns:
    - int: Average unique commits per branch (excluding specified branches).
    """
    excluded_branches = {"main", "master", "dev", "develop"}

    try:
        repo = git.Repo(repo_dir)
        branches = fetch_branches(repo)

        # Normalize branch names and filter excluded ones
        filtered_branches = [
            branch for branch in branches
            if branch.replace("origin/", "") not in excluded_branches
        ]

        if not filtered_branches:
            print("No branches left for average calculation after filtering.")
            return 0

        # Count unique commits across the filtered branches
        total_unique_commits = count_unique_commits(repo, filtered_branches)

        # Calculate and return the average
        return total_unique_commits // len(filtered_branches)

    except Exception as e:
        print(f"Error calculating average commits for branches in '{repo_dir}': {e}")
        return 0


def count_commits_per_member_per_branch(repo, branches):
    """
    Count the number of commits per team member per branch in a repository.

    Parameters:
    - repo (git.Repo): The Git repository object.
    - branches (list): A list of branch names.

    Returns:
    - dict: A nested dictionary where keys are branch names, and values
      are dictionaries with team members as keys and their
      commit counts as values.
    """
    TM_commits_by_branch = {}

    for branch in branches:
        try:
            branch_commits = defaultdict(int)

            for commit in repo.iter_commits(branch):
                author = commit.author.name
                branch_commits[author] += 1

            TM_commits_by_branch[branch] = dict(branch_commits)

        except Exception as e:
            print(f"Skipping branch '{branch}' due to error: {e}")
    
    # Sort the list by number of commits
    for branch in TM_commits_by_branch:
        TM_commits_by_branch[branch] = dict(sorted(TM_commits_by_branch[branch].items(),
                                                   key=lambda x: x[1], reverse=True))

    return TM_commits_by_branch


def get_commit_per_member(repo):
    """
    Save for each member their commits, the number of lines added and the number of lines deleted,
    the date, the lines of the commit and the commit message.

    Return the list sorted by number of lines added.
    """

    members_commits = {}
    origin = repo.remotes.origin.url.split(".git")[0]
    for commit in repo.iter_commits("HEAD"):
        author = commit.author.name
        # TODO: mapping

        # Ignore merge commits
        if len(commit.parents) > 1 or "merge" in commit.message.lower():
            continue
        
        if author not in members_commits:
            members_commits[author] = []  # Commits

        diff_stats = commit.stats
        members_commits[author].append({
            "commit": commit.hexsha,
            "date": str(commit.committed_datetime),
            "lines_added": diff_stats.total['insertions'],
            "lines_deleted": diff_stats.total['deletions'],
            "lines": diff_stats.total['lines'],
            "message": commit.message,
            "link": f"{origin}/commit/{commit.hexsha}"
        })

    # Sort the list by number of lines added
    for member in members_commits:
        members_commits[member].sort(key=lambda x: x["lines_added"], reverse=True)

    return members_commits


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

        commits = list(repo.iter_commits("HEAD"))
        commit_summary = defaultdict(int)
        commit_dates = []
        for commit in commits:
            author = commit.author.name
            commit_summary[author] += 1
            commit_dates.append((author, str(commit.committed_datetime)))

        commit_dates.sort(key=lambda x: x[1])

        branches = fetch_branches(repo)
        branch_commit_counts = count_commits_per_branch(repo, branches)
        TM_commits_by_branch = count_commits_per_member_per_branch(repo, branches)
        members_commits = get_commit_per_member(repo)

        total_unique_commits = count_unique_commits(repo, branches)

        excluded_branches = {"main", "master", "dev", "develop"}
        filtered_branches = [
            branch for branch in branches
            if branch.replace("origin/", "") not in excluded_branches
        ]
        avg_commits = total_unique_commits // len(filtered_branches) if filtered_branches else 0

        return {
            "repository": repo_title,
            "repository_url": repo.remotes.origin.url,
            "total_commits": len(commits),
            "total_unique_commits": total_unique_commits,
            "avg_commits": avg_commits,
            "commits_per_member": dict(commit_summary),
            "commit_dates": commit_dates,
            "branches_commit_counts": branch_commit_counts,
            "TM_commits_by_branch": TM_commits_by_branch,
            "members_commits": members_commits
        }

    except Exception as e:
        print(f"Error analyzing commits in '{repo_dir}': {e}")
        return {}


def analyze_multiple_repos_from_json(json_file_path: str, output_dir: str = None):
    """
    Analyze commits for multiple repositories listed in a JSON file.

    Parameters:
    - json_file_path (str): Path to the JSON file containing repository paths.
    - output_dir (str): Optional directory to save analysis results.

    Returns:
    - list: A summary of commit activity for all repositories.
    """
    try:
        # Create the output directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Load repository paths from the JSON file
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

            # Save analysis results to output directory
            if output_dir:
                output_file = os.path.join(output_dir, f"{os.path.basename(repo_dir)}_report.json")
                with open(output_file, "w") as f:
                    json.dump(analysis, f, indent=2)

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
        for branch, commit_count in repo_analysis["branches_commit_counts"].items():
            print(f"    - {branch:<40} Commits: {commit_count}")

        print("  Commits Per Member Per Branch:")
        for branch, members in repo_analysis["TM_commits_by_branch"].items():
            print(f"    - Branch: {branch}")
            for member, count in members.items():
                print(f"        {member:<30} Commits: {count}")

        print("  Average Commits Per Branch:", repo_analysis["avg_commits"])
