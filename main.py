import argparse
from src.clone_repo import clone_repos
from src.analyze_commits import analyze_multiple_repos_from_json
from src.analyze_contributions import generate_report
from src.generate_md_report import generate_md_report
import os
import json


def main():
    parser = argparse.ArgumentParser(
        description="EPEPEP: Github Analysis tool platform."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Subcommand: Clone repositories
    clone_parser = subparsers.add_parser("clone", help="Clone GitHub repositories.")
    clone_parser.add_argument(
        "-r", "--repo-list", nargs="+", required=True, help="List of repository URLs to clone."
    )
    clone_parser.add_argument(
        "-d", "--base-dir", default="./cloned_repos", help="Base directory to clone repositories into."
    )
    clone_parser.add_argument(
        "-o", "--output-file", default="./data/cloned_repos.json", help="Output JSON file for cloned repository details."
    )
    clone_parser.add_argument(
        "-t", "--threads", type=int, default=4, help="Number of threads to use for cloning."
    )
    
    # Subcommand: Analyze commits
    analyze_parser = subparsers.add_parser("analyze", help="Analyze commit activity.")
    analyze_parser.add_argument(
        "-j", "--json-file", required=True, help="Path to the JSON file containing repository paths."
    )
    analyze_parser.add_argument(
        "-o", "--output-dir", default="./commits_reports", help="Directory to save commits reports."
    )
    
    # Subcommand: Generate LOC reports
    loc_parser = subparsers.add_parser("loc", help="Generate LOC reports for repositories.")
    loc_parser.add_argument(
        "-j", "--json-file", required=True, help="Path to the JSON file containing repository paths."
    )
    loc_parser.add_argument(
        "-o", "--output-dir", default="./loc_reports", help="Directory to save LOC reports."
    )
    loc_parser.add_argument(
        "-m", "--mapping-file", help="Optional JSON file containing account mapping."
    )
    
    # Subcommand: List branches
    branches_parser = subparsers.add_parser("branches", help="List branches in a repository.")
    branches_parser.add_argument(
        "-b", "--repo-path", required=True, help="Path to the local repository to analyze."
    )
    
    # Subcommand: Generate markdown report
    markdown_parser = subparsers.add_parser("markdown", help="Generate markdown report.")
    markdown_parser.add_argument(
        "-j", "--json-file", required=True, help="Path to the JSON file containing repository paths."
    )
    markdown_parser.add_argument(
        "-l", "--loc-dir", default="./loc_reports", help="Directory containing LOC reports."
    )
    markdown_parser.add_argument(
        "-c", "--commits-dir", default="./commits_reports", help="Directory containing commits reports."
    )
    markdown_parser.add_argument(
        "-o", "--output-dir", default="./markdown_reports", help="Directory to save markdown reports."
    )
    markdown_parser.add_argument(
        "-m", "--mapping-file", help="Optional JSON file containing account mapping."
    )

    # Read user command and arguments
    args = parser.parse_args()   
    
    # Execute the selected command
    if args.command == "clone":
        print("Starting repository cloning...")
        clone_repos(args.repo_list, args.base_dir, args.output_file, args.threads)
    elif args.command == "analyze":
        print("Starting commit analysis...")
        analysis = analyze_multiple_repos_from_json(args.json_file, args.output_dir)
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
            for branch, members in repo_analysis["member_commits_by_branch"].items():
                print(f"    - Branch: {branch}")
                for member, count in members.items():
                    print(f"        {member:<30} Commits: {count}")
    elif args.command == "loc":
        print("Starting LOC report generation...")
        
        # Load cloned repository paths
        try:
            with open(args.json_file, 'r') as file:
                repos = json.load(file)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return

        # Load account mapping if provided
        account_mapping = {}
        if args.mapping_file:
            try:
                with open(args.mapping_file, 'r') as file:
                    account_mapping = json.load(file)
            except Exception as e:
                print(f"Error reading account mapping file: {e}")
                return

        # Ensure output directory exists
        output_dir = os.path.abspath(args.output_dir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generate reports
        try:
            generate_report(repos, account_mapping, output_dir=output_dir)
            print("LOC reports generated successfully.")
        except Exception as e:
            print(f"Error generating LOC reports: {e}")
    elif args.command == "markdown":
        print("Starting Markdown report generation...")

        # Load cloned repository paths
        try:
            with open(args.json_file, 'r') as file:
                repos = json.load(file)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return

        # Load account mapping if provided
        account_mapping = {}
        if args.mapping_file:
            try:
                with open(args.mapping_file, 'r') as file:
                    account_mapping = json.load(file)
            except Exception as e:
                print(f"Error reading account mapping file: {e}")
                return
            
        # Check commits reports parameter
        commits_dir = os.path.abspath(args.commits_dir)
        if not os.path.exists(commits_dir):
            print(f"Commits directory does not exist: {commits_dir}")
            return

        # Check LOC reports parameter
        loc_dir = os.path.abspath(args.loc_dir)
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
                with open(commits_file_path, 'r') as file:
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
                with open(loc_file_path, 'r') as file:
                    loc_data = json.load(file)
                    repo_data["loc_data"] = loc_data
            except Exception as e:
                print(f"Error reading LOC data: {e}")
                continue
            
            repository_data.append(repo_data)

        generate_md_report(repository_data, account_mapping, args.output_dir)
    else:
        parser.print_help()




if __name__ == "__main__":
    main()
