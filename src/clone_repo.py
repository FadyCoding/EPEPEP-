import os
import git
import json
from concurrent.futures import ThreadPoolExecutor


def clone_repo(repo_url, repo_dir):
    """
    Clone a single repository into the specified directory.
    """
    try:
        if os.path.exists(repo_dir):
            print(f"Directory '{repo_dir}' already exists. Skipping clone for '{repo_url}'.")
            return True

        git.Repo.clone_from(repo_url, repo_dir)
        print(f"Successfully cloned '{repo_url}' into '{repo_dir}'")
        return True
    except git.exc.GitCommandError as e:
        print(f"Error cloning '{repo_url}': {e}")
        return False


def clone_repos(repo_list, base_dir, output_file, max_threads=4):
    """
    Clone multiple repositories listed in repo_list into base_dir using multithreading,
    and store cloned repositories in a JSON file.
    """
    os.makedirs(base_dir, exist_ok=True)
    cloned_repos = {}

    with ThreadPoolExecutor(max_threads) as executor:
        futures = {}
        for repo_url in repo_list:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            repo_dir = os.path.join(base_dir, repo_name)
            futures[executor.submit(clone_repo, repo_url, repo_dir)] = (repo_url, repo_dir)

        for future in futures:
            repo_url, repo_dir = futures[future]
            if future.result():
                cloned_repos[repo_url] = repo_dir

    save_cloned_repos(output_file, cloned_repos)
    print(f"Cloned repositories stored in '{output_file}'")


def save_cloned_repos(output_file, cloned_repos):
    """
    Save cloned repositories to a JSON file.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save the data to the JSON file
        with open(output_file, 'w') as f:
            json.dump(cloned_repos, f, indent=4)
        print(f"Successfully saved cloned repository details to '{output_file}'.")
    except Exception as e:
        print(f"Error saving cloned repository details: {e}")


if __name__ == "__main__":
    repositories = [
        "https://github.com/FadyCoding/NBA_webApp.git",
        "https://github.com/FadyCoding/Unity-Queue-System.git",
        "https://github.com/debiai/DebiAI.git"
    ]
    base_directory = "./cloned_repos"
    output_file = "./data/cloned_repos.json"

    print("Cloning repositories...")
    clone_repos(repositories, base_directory, output_file, max_threads=4)
