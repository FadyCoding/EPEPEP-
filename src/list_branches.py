import subprocess

def list_git_branches(repo_path):
    """
    List all branches in a Git repository.

    Parameters:
    - repo_path (str): Path to the Git repository.

    Returns:
    - branches (list): List of branch names.
    """
    try:
        # Navigate to the repository and fetch all branches
        result = subprocess.run(
            ["git", "-C", repo_path, "branch", "-a"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        # Extract branch names from the output
        branches = [branch.strip() for branch in result.stdout.splitlines()]
        return branches
    except subprocess.CalledProcessError as e:
        print(f"Error listing branches: {e.stderr}")
        return []

# Example usage
if __name__ == "__main__":
    repo_path = "./my_repos/DebiAI"
    branches = list_git_branches(repo_path)
    print("Branches in repository:")
    for branch in branches:
        print(branch)
