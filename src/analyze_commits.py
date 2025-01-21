import git
from collections import defaultdict
import os
import json


def fetch_branches(repo):
    """
    Fetch all branches (local and remote) for a repository.
    """
    try:
        repo.git.fetch("--all", "--prune")
        branches = [ref.name for ref in repo.branches]
        branches.extend([ref.name for ref in repo.remote().refs])
        branches = [
            branch.replace("remotes/origin/", "origin/") for branch in sorted(set(branches))
            if not branch.startswith("remotes/origin/HEAD")
        ]
        return branches
    except Exception as e:
        print(f"Error fetching branches: {e}")
        return []


def count_unique_commits(repo, branches):
    """
    Count the total number of unique commits across all branches.
    """
    unique_commits = set()
    for branch in branches:
        try:
            branch_commits = repo.iter_commits(branch)
            unique_commits.update(commit.hexsha for commit in branch_commits)
        except Exception as e:
            print(f"Skipping branch '{branch}' due to error: {e}")
    return len(unique_commits)


def count_commits_per_branch(repo, branches):
    """
    Count the number of commits for each branch.
    """
    branch_commit_counts = {}
    for branch in branches:
        try:
            commit_count = sum(1 for _ in repo.iter_commits(branch))
            branch_commit_counts[branch] = commit_count
        except Exception as e:
            print(f"Skipping branch '{branch}' due to error: {e}")
    return branch_commit_counts


def count_commits_per_member_per_branch(repo, branches, account_mapping):
    """
    Count commits per member per branch, applying account mapping.
    """
    TM_commits_by_branch = {}
    for branch in branches:
        try:
            branch_commits = defaultdict(int)
            for commit in repo.iter_commits(branch):
                author = commit.author.name
                mapped_author = account_mapping.get(author, author)
                branch_commits[mapped_author] += 1
            TM_commits_by_branch[branch] = dict(branch_commits)
        except Exception as e:
            print(f"Skipping branch '{branch}' due to error: {e}")
    for branch in TM_commits_by_branch:
        TM_commits_by_branch[branch] = dict(sorted(TM_commits_by_branch[branch].items(),
                                                   key=lambda x: x[1], reverse=True))
    return TM_commits_by_branch


def get_commit_per_member(repo, account_mapping):
    """
    Analyze commits per member, applying account mapping.
    """
    members_commits = {}
    origin = repo.remotes.origin.url.split(".git")[0]
    for commit in repo.iter_commits("HEAD"):
        author = commit.author.name
        mapped_author = account_mapping.get(author, author)
        if len(commit.parents) > 1 or "merge" in commit.message.lower():
            continue
        if mapped_author not in members_commits:
            members_commits[mapped_author] = []
        diff_stats = commit.stats
        members_commits[mapped_author].append({
            "commit": commit.hexsha,
            "date": str(commit.committed_datetime),
            "lines_added": diff_stats.total['insertions'],
            "lines_deleted": diff_stats.total['deletions'],
            "lines": diff_stats.total['lines'],
            "message": commit.message,
            "link": f"{origin}/commit/{commit.hexsha}"
        })
    for member in members_commits:
        members_commits[member].sort(key=lambda x: x["lines_added"], reverse=True)
    return members_commits


def analyze_commits(repo_dir, account_mapping):
    """
    Analyze commit activity for a given repository, applying account mapping.
    """
    not_found_members = set()
    try:
        repo = git.Repo(repo_dir)
        repo_title = os.path.basename(repo_dir)

        commits = list(repo.iter_commits("HEAD"))
        commit_summary = defaultdict(int)
        commit_dates = []
        for commit in commits:
            author = account_mapping.get(commit.author.name, None)
            if author is None:
                not_found_members.add(commit.author.name)
            else:
                commit_summary[author] += 1
                commit_dates.append((author, str(commit.committed_datetime)))

        commit_dates.sort(key=lambda x: x[1])

        branches = fetch_branches(repo)
        branch_commit_counts = count_commits_per_branch(repo, branches)
        TM_commits_by_branch = count_commits_per_member_per_branch(repo, branches, account_mapping)
        members_commits = get_commit_per_member(repo, account_mapping)

        total_unique_commits = count_unique_commits(repo, branches)

        excluded_branches = {"main", "master", "dev", "develop"}
        filtered_branches = [
            branch for branch in branches
            if branch.replace("origin/", "") not in excluded_branches
        ]
        avg_commits = total_unique_commits // len(filtered_branches) if filtered_branches else 0

        if not_found_members:
            print(f"   Account mapping not found for: {', '.join(not_found_members)}")

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


def analyze_multiple_repos_from_json(repo_data_json_file_path: str, account_mapping, output_dir: str = None):
    """
    Analyze commits for multiple repositories listed in a JSON file, applying account mapping.
    """
    try:
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(repo_data_json_file_path, "r") as file:
            repo_data = json.load(file)

        repo_dirs = list(repo_data.values())
        print(f"Found {len(repo_dirs)} repositories to analyze.")

        all_repo_analysis = []

        for repo_dir in repo_dirs:
            if os.path.exists(repo_dir) and os.path.isdir(repo_dir):
                print(f"Analyzing repository: {repo_dir}")
                analysis = analyze_commits(repo_dir, account_mapping)
                if analysis:
                    all_repo_analysis.append(analysis)
            else:
                print(f"Invalid repository path: {repo_dir}")

            if output_dir:
                output_file = os.path.join(output_dir, f"{os.path.basename(repo_dir)}_report.json")
                with open(output_file, "w") as f:
                    json.dump(analysis, f, indent=2)

        return all_repo_analysis
    except Exception as e:
        print(f"Error reading JSON file or analyzing repositories: {e}")
        raise


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


if __name__ == "__main__":
    repo_data_json_file_path = "./my_repos_info.json"
    account_mapping_path = "./account_mapping.json"
    output_directory = "./commits_reports"

    # Load account mapping from a JSON file
    account_mapping = load_account_mapping(account_mapping_path)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    print("Starting commit analysis...")
    try:
        all_analysis = analyze_multiple_repos_from_json(
            repo_data_json_file_path,
            account_mapping=account_mapping,
            output_dir=output_directory
        )
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
    except Exception as e:
        print(f"Unexpected error: {e}")
