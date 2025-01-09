# import os
import subprocess
import shutil


def run_cspell_on_git():
    try:
        # Dynamically find the cspell executable
        cspell_path = shutil.which("cspell")
        if not cspell_path:
            raise FileNotFoundError("cspell executable not found in PATH.")

        # Get branch names
        with open("branches.txt", "w") as branch_file:
            subprocess.run(["git", "branch", "-a"], stdout=branch_file, check=True)

        # Check spelling on branches
        subprocess.run([cspell_path, "branches.txt", "--config",
                        "cspell-config.json"], check=True)

        # Get commit messages
        with open("commit_messages.txt", "w") as commit_file:
            subprocess.run(["git", "log", "--pretty=format:%s"], stdout=commit_file, check=True)

        # Check spelling on commit messages
        subprocess.run([cspell_path, "commit_messages.txt", "--config",
                        "cspell-config.json"], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
    except FileNotFoundError as e:
        print("Executable not found:", e)


if __name__ == "__main__":
    run_cspell_on_git()
