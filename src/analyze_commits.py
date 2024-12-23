import git
from collections import defaultdict

def analyze_commits(repo_dir):
    """
    Analyze commit activity for a given Git repository.
    
    Parameters:
    - repo_dir (str): Path to the local Git repository.
    
    Returns:
    - dict: A summary of commit activity.
    """
    try:
        repo = git.Repo(repo_dir)
        commits = list(repo.iter_commits('HEAD'))  # Fetch all commits
        commit_summary = defaultdict(int)
        commit_dates = []

        for commit in commits:
            author = commit.author.name
            commit_summary[author] += 1
            commit_dates.append((author, commit.committed_datetime))

        # Sort commits by date for chronological display
        commit_dates.sort(key=lambda x: x[1])

        return {
            "total_commits": len(commits),
            "commits_per_member": dict(commit_summary),
            "commit_dates": commit_dates
        }

    except Exception as e:
        print(f"Error analyzing commits in '{repo_dir}': {e}")
        return {}


def analyze_branches(repo_dir):
    """
    Analyze branch activity for a given Git repository.
    
    Parameters:
    - repo_dir (str): Path to the local Git repository.
    
    Returns:
    - dict: A summary of branch activity.
    """
    try:
        repo = git.Repo(repo_dir)
        branches = repo.branches
        branch_summary = {}

        for branch in branches:
            branch_name = branch.name
            branch_commits = list(repo.iter_commits(branch))
            commits_per_member = defaultdict(int)

            for commit in branch_commits:
                author = commit.author.name
                commits_per_member[author] += 1

            branch_summary[branch_name] = {
                "total_commits": len(branch_commits),
                "commits_per_member": dict(commits_per_member)
            }

        return branch_summary

    except Exception as e:
        print(f"Error analyzing branches in '{repo_dir}': {e}")
        return {}

if __name__ == "__main__":
    # Example usage
    repo_directory = "./cloned_repos/NBA_webApp"  # Change this path to analyze another repo
    branch_data = analyze_branches(repo_directory)

    print("\nBranch Activity Analysis:")
    for branch, stats in branch_data.items():
        print(f"Branch: {branch}")
        print(f"  Total commits: {stats['total_commits']}")
        print(f"  Commits per team member:")
        for author, count in stats["commits_per_member"].items():
            print(f"    - {author}: {count} commits")
