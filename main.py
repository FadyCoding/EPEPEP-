import argparse
from src.clone_repo import clone_repo, clone_repos
from src.analyze_commits import analyze_commits, analyze_multiple_repos_from_json, generate_commits_distribution_plot
from src.analyze_contributions import generate_reports, generate_loc_report
from src.generate_md_report import generate_md_reports, generate_md_report
import os
import json
import yaml
import shutil


def analyse(json_file, output_dir):
    print("Starting commit analysis...")
    analysis = analyze_multiple_repos_from_json(json_file, output_dir)
    for repo_analysis in analysis:
        print("\nRepository:", repo_analysis["repository"])
        print("  Total Commits:", repo_analysis["total_commits"])
        print("  Commits Per Member:")
        for author, count in repo_analysis["commits_per_member"].items():
            print(f"    - {author}: {count} commits")
        print("  Branches:")
        for branch in repo_analysis["branches_commit_counts"]:
            print(f"    - {branch}")
        print("  Average Commits Per Branch", repo_analysis["avg_commits_per_branch"])
        print("  Commits Per Member Per Branch:")
        for branch, members in repo_analysis["TM_commits_by_branch"].items():
            print(f"    - Branch: {branch}")
            for member, count in members.items():
                print(f"        {member:<30} Commits: {count}")
        print("  Biggest 3 commits for each member:")
        for member in repo_analysis["members_commits"]:
            print(f"    - {member}")
            for commit in repo_analysis["members_commits"][member][:3]:
                print(
                    f"        {commit['commit']}: +{commit['lines_added']} -{commit['lines_deleted']}"
                )


def line_of_code_report(json_file, output_dir, mapping_file_path=None):
    # Load cloned repository paths
    try:
        with open(json_file, "r") as file:
            repos = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    # Load account mapping if provided
    account_mapping = {}
    if mapping_file_path:
        try:
            with open(mapping_file_path, "r") as file:
                account_mapping = json.load(file)
        except Exception as e:
            print(f"Error reading account mapping file: {e}")
            return

    # Ensure output directory exists
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate reports
    try:
        generate_reports(repos, account_mapping, output_dir=output_dir)
        print("LOC reports generated successfully.")
    except Exception as e:
        print(f"Error generating LOC reports: {e}")
        # Print the full traceback
        import traceback

        traceback.print_exc()


def generate_md(
    repo_data_json_file_path,
    mapping_file_path,
    commits_folder_path,
    loc_folder_path,
    output_dir,
):
    # Load cloned repository paths
    try:
        with open(repo_data_json_file_path, "r") as file:
            repos = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    # Load account mapping if provided
    account_mapping = {}
    if mapping_file_path:
        try:
            with open(mapping_file_path, "r") as file:
                account_mapping = json.load(file)
        except Exception as e:
            print(f"Error reading account mapping file: {e}")
            return

    # Check commits reports parameter
    commits_dir = os.path.abspath(commits_folder_path)
    if not os.path.exists(commits_dir):
        print(f"Commits directory does not exist: {commits_folder_path}")
        return

    # Check LOC reports parameter
    loc_dir = os.path.abspath(loc_folder_path)
    if not os.path.exists(loc_dir):
        print(f"LOC directory does not exist: {loc_dir}")
        return

    repository_data = []
    for repo_url, repo_path in repos.items():
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_data = {}
        # Load repository commits data
        commits_file_path = os.path.join(commits_dir, f"{repo_name}_report.json")
        if not os.path.exists(commits_file_path):
            print(f"Commits report '{commits_file_path}' not found for {repo_name}")
            continue
        try:
            with open(commits_file_path, "r") as file:
                repo_data = json.load(file)
        except Exception as e:
            print(f"Error reading commits data: {e}")
            continue

        # Load repository LOC data
        loc_file_path = os.path.join(loc_dir, f"{repo_name}_loc_report.json")
        if not os.path.exists(loc_file_path):
            print(f"LOC report '{loc_file_path}' not found for {repo_name}")
            continue
        try:
            with open(loc_file_path, "r") as file:
                loc_data = json.load(file)
                repo_data["loc_data"] = loc_data
        except Exception as e:
            print(f"Error reading LOC data: {e}")
            continue

        repository_data.append(repo_data)

    generate_md_reports(repository_data, account_mapping, output_dir)


def full_run(yaml_config_file_path: str, skip_clone: bool = False):
    # Load configuration from YAML file
    try:
        with open(yaml_config_file_path, "r") as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return

    # { # Example config
    #     "projects": {
    #         "debiai": {
    #             "url": "https://github.com/debiai/DebiAI.git",
    #             "members_mapping": {
    #                 "Fady": ["FadyCoding", "Fady BEKKAR"],
    #                 "Tom": ["Tom Mansion", "ToMansion"],
    #                 "Macaire": ["MacaireM"],
    #                 "Nicolas": ["Nicolas Leroux"],
    #             },
    #         }
    #     },
    #     "folders": {
    #         "cloned_projects": "cloned_repos",
    #         "commit_reports": "commit_reports",
    #         "line_of_code_reports": "loc_reports",
    #         "markdown_reports": "markdown_reports",
    #     },
    # }

    # Validate configuration
    if not config:
        raise ValueError("Invalid configuration file.")
    if not config.get("projects"):
        raise ValueError("No projects found in the configuration")
    if not config.get("folders"):
        raise ValueError("No folders found in the configuration")
    for folder in [
        "cloned_projects",
        "commit_reports",
        "line_of_code_reports",
        "markdown_reports",
    ]:
        if not config["folders"].get(folder):
            raise ValueError(f"No '{folder}' folder specified in the configuration")

    # Convert members mapping to a dictionary
    # From this: {
    #     "Fady": ["FadyCoding", "Fady BEKKAR"],
    #     "Tom": ["Tom Mansion", "ToMansion"],
    #     "Macaire": ["MacaireM"],
    #     "Nicolas": ["Nicolas Leroux"],
    # }
    # To this: {
    #     "FadyCoding": "Fady B.",
    #     "Fady BEKKAR": "Fady B.",
    #     "Fady": "Fady B.",
    #     "tom.mansion": "Tom Mansion",
    #     "ToMansion": "Tom Mansion"
    # }

    for project_name, project_data in config["projects"].items():
        new_members_mapping = {}
        members_mapping = project_data.get("members_mapping", {})
        for member, aliases in members_mapping.items():
            for alias in aliases:
                new_members_mapping[alias] = member
            new_members_mapping[member] = member
        config["projects"][project_name]["new_members_mapping"] = new_members_mapping

    # Clone repositories
    print("Cloning repositories...")
    cloned_repositories_dir = config["folders"]["cloned_projects"]
    os.makedirs(cloned_repositories_dir, exist_ok=True)
    repos = config.get("projects", {})
    for project_name, project_data in repos.items():
        print(f"- Project: {project_name}")
        repo_dir = os.path.join(cloned_repositories_dir, project_name)
        config["projects"][project_name]["repo_dir"] = repo_dir
        # Check if the repository is already cloned
        if os.path.exists(repo_dir) and skip_clone:
            print(f"   Repository '{project_name}' already cloned. Skipping...")
        else:
            shutil.rmtree(repo_dir, ignore_errors=True)
            clone_repo(project_data["url"], repo_dir)

    # Analyze commits
    print("Analyzing commits...")
    commits_reports_dir = config["folders"]["commit_reports"]
    os.makedirs(commits_reports_dir, exist_ok=True)
    for project_name, project_data in repos.items():
        print(f"- Project: {project_name}")
        analysis = analyze_commits(
            project_data["repo_dir"], project_data["new_members_mapping"]
        )
        output_file = os.path.join(commits_reports_dir, f"{project_name}_report.json")
        project_data["analysis"] = analysis
        with open(output_file, "w") as f:
            json.dump(analysis, f, indent=2)

        # Generate commits distribution plot
        activity_image_path = os.path.join(commits_reports_dir, f"{project_name}_plot.png")
        generate_commits_distribution_plot(analysis, activity_image_path)
        project_data["activity_image_path"] = activity_image_path

    # Generate LOC reports
    print("Analyzing lines of code...")
    loc_reports_dir = config["folders"]["line_of_code_reports"]
    os.makedirs(loc_reports_dir, exist_ok=True)
    for project_name, project_data in repos.items():
        print(f"- Project: {project_name}")
        report = generate_loc_report(
            project_data["repo_dir"], project_data["new_members_mapping"]
        )

        project_data["loc_report"] = report
        output_file = os.path.join(loc_reports_dir, f"{project_name}_loc_report.json")
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

    # Generate markdown reports
    print("Generating markdown reports...")
    markdown_reports_dir = config["folders"]["markdown_reports"]
    os.makedirs(markdown_reports_dir, exist_ok=True)
    for project_name, project_data in repos.items():
        print(f"- Project: {project_name}")
        repository_data = project_data["analysis"] | {
            "repository": project_name,
            "repository_url": project_data["url"],
            "loc_data": project_data["loc_report"],
            "activity_image_path": project_data["activity_image_path"],
        }

        report_folder_dir = os.path.join(markdown_reports_dir, project_name)
        generate_md_report(
            project_name,
            repository_data,
            project_data["new_members_mapping"],
            report_folder_dir,
        )

    print("All steps completed successfully.")
    print(f"Markdown reports saved in '{markdown_reports_dir}'")


def main():
    parser = argparse.ArgumentParser(
        description="EPEPEP: Github Analysis tool platform."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommand: Run
    run_parser = subparsers.add_parser("run", help="Run all analysis steps.")
    run_parser.add_argument(
        "-c", "--config", required=True, help="Path to yaml config file."
    )
    run_parser.add_argument(
        "--skip-clone",
        action="store_true",
        help="Skip the repository cloning step if the repository is already cloned.",
    )

    # Subcommand: Clone repositories
    clone_parser = subparsers.add_parser("clone", help="Clone GitHub repositories.")
    clone_parser.add_argument(
        "-r",
        "--repo-list",
        nargs="+",
        required=True,
        help="List of repository URLs to clone.",
    )
    clone_parser.add_argument(
        "-d",
        "--base-dir",
        default="./cloned_repos",
        help="Base directory to clone repositories into.",
    )
    clone_parser.add_argument(
        "-o",
        "--output-file",
        default="./data/cloned_repos.json",
        help="Output JSON file for cloned repository details.",
    )
    clone_parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=4,
        help="Number of threads to use for cloning.",
    )

    # Subcommand: Analyze commits
    analyze_parser = subparsers.add_parser("analyze", help="Analyze commit activity.")
    analyze_parser.add_argument(
        "-j",
        "--json-file",
        required=True,
        help="Path to the JSON file containing repository paths.",
    )
    analyze_parser.add_argument(
        "-o",
        "--output-dir",
        default="./commits_reports",
        help="Directory to save commits reports.",
    )

    # Subcommand: Generate LOC reports
    loc_parser = subparsers.add_parser(
        "loc", help="Generate LOC reports for repositories."
    )
    loc_parser.add_argument(
        "-j",
        "--json-file",
        required=True,
        help="Path to the JSON file containing repository paths.",
    )
    loc_parser.add_argument(
        "-o",
        "--output-dir",
        default="./loc_reports",
        help="Directory to save LOC reports.",
    )
    loc_parser.add_argument(
        "-m", "--mapping-file", help="Optional JSON file containing account mapping."
    )

    # Subcommand: Generate markdown report
    markdown_parser = subparsers.add_parser(
        "markdown", help="Generate markdown report."
    )
    markdown_parser.add_argument(
        "-j",
        "--json-file",
        required=True,
        help="Path to the JSON file containing repository paths.",
    )
    markdown_parser.add_argument(
        "-l",
        "--loc-dir",
        default="./loc_reports",
        help="Directory containing LOC reports.",
    )
    markdown_parser.add_argument(
        "-c",
        "--commits-dir",
        default="./commits_reports",
        help="Directory containing commits reports.",
    )
    markdown_parser.add_argument(
        "-o",
        "--output-dir",
        default="./markdown_reports",
        help="Directory to save markdown reports.",
    )
    markdown_parser.add_argument(
        "-m", "--mapping-file", help="Optional JSON file containing account mapping."
    )

    # Read user command and arguments
    args = parser.parse_args()

    # Execute the selected command
    if args.command == "run":
        full_run(args.config, args.skip_clone)
    elif args.command == "clone":
        print("Starting repository cloning...")
        clone_repos(args.repo_list, args.base_dir, args.output_file, args.threads)
    elif args.command == "analyze":
        print("Starting commit analysis...")
        analyse(args.json_file, args.output_dir)
    elif args.command == "loc":
        print("Starting LOC report generation...")
        line_of_code_report(args.json_file, args.output_dir, args.mapping_file)
    elif args.command == "markdown":
        print("Starting Markdown report generation...")
        generate_md(
            args.json_file,
            args.mapping_file,
            args.commits_dir,
            args.loc_dir,
            args.output_dir,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
