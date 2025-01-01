# EPEPEP, a Git repository analysis tool

## Getting Started

### Installation

```bash
git clone https://github.com/FadyCoding/EPEPEP-.git

cd EPEPEP-

pip install -r requirements.txt
```

### Usage

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
