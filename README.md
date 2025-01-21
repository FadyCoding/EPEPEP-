# EPEPEP, a Git repository analysis tool

## Getting Started

### Installation

```bash
git clone https://github.com/FadyCoding/EPEPEP-.git

cd EPEPEP-

pip install -r requirements.txt
```

### Running the tool

_Configure the tool by editing the [config.yaml](.config.yaml) file_

```yaml
projects:
  debiai:
    url: https://github.com/debiai/DebiAI.git
    members_mapping:
      Fady:
        - FadyCoding
        - Fady BEKKAR
      Tom:
        - tom.mansion
        - Tom Mansion
        - ToMansion
      Macaire:
        - MacaireM
      Nicolas:
        - Nicolas Leroux
        - 0xNi
      Theo:
        - Theochelim
      Raphael:
        - raphaelbraud
folders:
  cloned_projects: cloned_repos
  commit_reports: commits_reports
  line_of_code_reports: loc_reports
  markdown_reports: markdown_reports

```

_Run the following command:_

```bash
python main.py run -c ./config.yaml
```

The markdown reports will be generated in the [markdown_reports](./markdown_reports) directory.

### Individual commands

You can also run the tool in steps:

_Run the following command:_

```bash
python main.py clone -r https://github.com/project/project1.git -d ./directory_to_clone_the_repo  -o ./my_repos_info.json
python main.py analyze -j ./my_repos_info.json
python main.py loc -j ./my_repos_info.json -o ./loc_reports
python main.py markdown -j ./my_repos_info.json -l ./loc_reports -o ./markdown_reports
```

_Run the helper:_

```bash
python main.py clone -h
python main.py analyze -h
python main.py loc -h
python main.py markdown -h
```
