import git
from collections import defaultdict
import os
import json


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
        commits = list(repo.iter_commits('HEAD'))
        commit_summary = defaultdict(int)
        commit_dates = []
        
        repo_title = os.path.basename(repo_dir)

        for commit in commits:
            author = commit.author.name
            commit_summary[author] += 1
            commit_dates.append((author, commit.committed_datetime))

        commit_dates.sort(key=lambda x: x[1])

        return {
            "repository": repo_title,
            "total_commits": len(commits),
            "commits_per_member": dict(commit_summary),
            "commit_dates": commit_dates
        }

    except Exception as e:
        print(f"Error analyzing commits in '{repo_dir}': {e}")
        return {}


def analyze_multiple_repos_from_json(json_file_path):
    """
    Analyze commits for multiple repositories listed in a JSON file.

    Parameters:
    - json_file_path (str): Path to the JSON file containing repository paths.
    
    Returns:
    - list: A summary of commit activity for all repositories.
    """
    try:
        with open(json_file_path, 'r') as file:
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
    # json_file_path = "data/cloned_repos.json"
    json_file_path = "./data/cloned_repos.json"

    print("Analyzing repositories listed in the JSON file...")
    all_analysis = analyze_multiple_repos_from_json(json_file_path)

    for repo_analysis in all_analysis:
        print("\nRepository:", repo_analysis["repository"])
        print("  Total Commits:", repo_analysis["total_commits"])
        print("  Commits Per Member:")
        for author, count in repo_analysis["commits_per_member"].items():
            print(f"    - {author}: {count} commits")
