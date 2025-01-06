# EPEPEP, a Git repository analysis tool

## Getting Started

### Installation

```bash
git clone https://github.com/FadyCoding/EPEPEP-.git

cd EPEPEP-

pip install -r requirements.txt
```

### Standard Usage

*Run the following command:*

```bash
python main.py clone -r https://github.com/project/project1.git -d ./directory_to_clone_the_repo  -o ./my_repos_info.json
python main.py analyze -j ./my_repos_info.json
python main.py loc -j ./my_repos_info.json -o ./loc_reports
```

*Run the helper:*

```bash
python main.py clone -h
python main.py analyze -h
python main.py loc -h
```

----------------------------------------------------------------------------------------------------------------------
### Alternative Usage

Edit the repository to clone in the [scr/clone_repo.py](src/clone_repo.py) file:

```python
    repositories = [
        "https://github.com/project/project1.git",
        "https://github.com/project/project2.git",
        "https://github.com/project/project3.git"
    ]
```

Then run the following command:

```bash
python src/clone_repo.py
python src/analyze_commits.py
python src/analyze_contributions.py
```
