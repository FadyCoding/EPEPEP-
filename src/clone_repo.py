import os
import git
from concurrent.futures import ThreadPoolExecutor

def clone_repo(repo_url, repo_dir):
    """
    Clone a single repository into the specified directory.
    """
    try:
        if os.path.exists(repo_dir):
            print(f"Directory {repo_dir} already exists. Skipping clone for {repo_url}.")
            return False

        git.Repo.clone_from(repo_url, repo_dir)
        print(f"Successfully cloned {repo_url} to {repo_dir}")
        return True
    except git.exc.GitCommandError as e:
        print(f"Error cloning {repo_url}: {e}")
        return False

def clone_repos(repo_list, base_dir, max_threads=4):
    """
    Clone multiple repositories listed in repo_list into base_dir using multithreading.
    """
    os.makedirs(base_dir, exist_ok=True)
    
    with ThreadPoolExecutor(max_threads) as executor:
        futures = []
        for repo_url in repo_list:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            repo_dir = os.path.join(base_dir, repo_name)
            futures.append(executor.submit(clone_repo, repo_url, repo_dir))

        # Wait for all tasks to complete
        for future in futures:
            future.result()

if __name__ == "__main__":
    # Example repository list
    repositories = [
        "https://github.com/FadyCoding/NBA_webApp.git",
        "https://github.com/FadyCoding/Unity-Queue-System.git"
    ]
    base_directory = "./cloned_repos"  # Directory to store cloned repositories
    
    clone_repos(repositories, base_directory, max_threads=4)

