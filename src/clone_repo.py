import git

def clone_repo(repo_url, repo_dir):
    try:
        git.Repo.clone_from(repo_url, repo_dir)
        print(f'Repo {repo_url} cloned to {repo_dir}')
    except git.exc.GitCommandError as e:
        print(f'Error: {e}')
        return False

