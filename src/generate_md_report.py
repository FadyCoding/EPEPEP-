import json
import os


def load_loc_data(loc_dir):
    """
    Load LOC data from the specified directory.
    """
    loc_data = {}
    for root, _, files in os.walk(loc_dir):
        for file in files:
            if file.endswith(".json"):
                try:
                    with open(os.path.join(root, file), "r") as f:
                        data = json.load(f)
                        loc_data.update(data)
                except Exception as e:
                    print(f"Error reading LOC data from '{file}': {e}")
    return loc_data


def generate_report(repo_data: dict):
    """
    Generate a Markdown report from the analysis data and LOC data.
    """
    report = f"# {repo_data['repository']} Analysis Report\n"
    report += f"**Repository URL:** {repo_data.get('repository_url', 'N/A')}\n\n"
    report += "## Commits\n"
    report += f"**Total Commits:** {repo_data.get('total_commits', 'N/A')}\n\n"

    if "loc_data" in repo_data:
        loc_data = repo_data["loc_data"]
        total = loc_data.get("Total LOC", {}).get("total", {})
        report += "## Line of codes\n"
        report += f"- **Total LOC:** {total.get('total', 'N/A')}\n"
        report += f"- **Total Added:** {total.get('added', 'N/A')}\n"
        report += f"- **Total removed:** {total.get('deleted', 'N/A')}\n"
        report += "\n"

        if "Final LOC" in loc_data and isinstance(loc_data["Final LOC"], dict):
            # Add a section for each contributor
            report += "### Contribution\n"
            report += f"**Total Contributors:** {len(loc_data['Final LOC'])}\n\n"
            report += "| Contributor | Lines | Percent |\n"
            report += "|----------|-------|---------|\n"

            for contributor in loc_data["Final LOC"]:
                lines = loc_data["Final LOC"][contributor].get("lines", "N/A")
                percent = loc_data["Final LOC"][contributor].get("percentage", None)
                # Round the percentage to two decimal places
                percent = f"{percent:.2f}" if percent is not None else "N/A"
                contributor_report_file = f"./{contributor.replace(' ', '_')}_report.md"

                report += f"| [{contributor}]({contributor_report_file}) | {lines} | {percent}% |\n"
            report += "\n"

    return report


def generate_md_report(
    repository_data: list[dict], account_mapping: dict, output_dir: str
):
    """
    Generate a Markdown report from the JSON analysis file and LOC directory.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate the report for each repository
    for repo_data in repository_data:
        repo_name = repo_data["repository"]
        print(f"Generating report for {repo_name}...")

        # Create a folder for the repository
        repo_dir = os.path.join(output_dir, repo_name)
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir)

        report = generate_report(repo_data)

        # Write the report to the output directory
        output_file = os.path.join(repo_dir, f"{repo_name}_report.md")
        with open(output_file, "w") as file:
            file.write(report)

        print(f" - Markdown report generated: {output_file}")
