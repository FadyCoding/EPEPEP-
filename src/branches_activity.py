import subprocess
from src.analyze_commits import calculate_average_commits_per_branch

def list_git_branches(repo_path):
    """
    List all branches in a Git repository.

    Parameters:
    - repo_path (str): Path to the Git repository.

    Returns:
    - branches (list): List of branch names.
    """
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "branch", "-a"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        branches = [
            branch.strip()
            for branch in result.stdout.splitlines()
            if not branch.startswith("remotes/origin/HEAD")
        ]
        return branches
    except subprocess.CalledProcessError as e:
        print(f"Error listing branches: {e.stderr}")
        return []

def display_branch_activity(repo_path):
    """
    Display branch activity for a Git repository.

    Parameters:
    - repo_path (str): Path to the Git repository.
    """
    branches = list_git_branches(repo_path)
    if branches:
        print("Branches in repository:")
        for branch in branches:
            print(f"  - {branch}")

        average_commits = calculate_average_commits_per_branch(repo_path)
        print(f"\nAverage commits per branch: {average_commits:.2f}")
    else:
        print("No branches found in the repository.")

if __name__ == "__main__":
    repo_path = "./my_repos/DebiAI"
    display_branch_activity(repo_path)
