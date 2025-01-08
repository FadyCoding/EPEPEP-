import argparse
from src.clone_repo import clone_repos
from src.analyze_commits import analyze_multiple_repos_from_json
from src.analyze_contributions import generate_report
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
    
    # Subcommand: Generate LOC reports
    loc_parser = subparsers.add_parser("loc", help="Generate LOC reports for repositories.")
    loc_parser.add_argument(
        "-j", "--json-file", required=True, help="Path to the JSON file containing repository paths."
    )
    loc_parser.add_argument(
        "-o", "--output-dir", default="./loc_reports", help="Directory to save LOC reports."
    ) 
    
    args = parser.parse_args()   
    
    if args.command == "clone":
        print("Starting repository cloning...")
        clone_repos(args.repo_list, args.base_dir, args.output_file, args.threads)
    elif args.command == "analyze":
        print("Starting commit analysis...")
        analysis = analyze_multiple_repos_from_json(args.json_file)
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
        with open(args.json_file, 'r') as file:
            repos = json.load(file)
        
        # Generate reports
        generate_report(repos, args.output_dir)

if __name__ == "__main__":
    main()
