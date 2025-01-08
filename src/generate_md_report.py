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
        report += "### Count:\n"
        report += (
            f"- **Final LOC:** {loc_data.get('Final LOC', {}).get('total', 'N/A')}\n"
        )
        report += "\n"
        report += "### Total committed:\n"
        report += f"- **Total Added:** {total.get('added', 'N/A')}\n"
        report += f"- **Total removed:** {total.get('deleted', 'N/A')}\n"
        report += f"- **Total LOC:** {total.get('total', 'N/A')}\n"
        report += "\n"

        if "Final LOC" in loc_data and isinstance(loc_data["Final LOC"], dict):
            # Add a section for each contributor
            report += "### Contribution\n"
            report += f"**Total Contributors:** {len(loc_data['Final LOC'])}\n\n"
            report += "| Contributor | Lines | Percent |\n"
            report += "|----------|-------|---------|\n"

            for contributor in loc_data["Final LOC"].get("data", {}):
                final_loc_data = loc_data["Final LOC"]["data"]
                lines = final_loc_data[contributor].get("lines", "N/A")
                percent = final_loc_data[contributor].get("percentage", None)

                # Round the percentage to two decimal places
                percent = f"{percent:.2f}" if percent is not None else "N/A"

                # Link to the contributor's detailed report
                contributor_report_file = (
                    f"./contributors/{contributor.replace(' ', '_')}_report.md"
                )

                report += f"| [{contributor}]({contributor_report_file}) | {lines} | {percent}% |\n"
            report += "\n"

    return report


def generate_contributor_report(repo_data: dict, contributor: str):
    """
    Generate a detailed Markdown report for a specific contributor.
    """
    loc_data = repo_data["loc_data"]
    final_loc_data = loc_data.get("Final LOC", {}).get("data", {}).get(contributor, {})

    if not final_loc_data:
        return None

    report = f"# {contributor} Contribution Report\n"
    report += f"**Repository:** {repo_data['repository']}\n\n"
    report += "## Line of codes\n"
    report += f"**Total Lines:** {final_loc_data.get('lines', 'N/A')}\n"
    report += f"**Percentage:** {final_loc_data.get('percentage', 'N/A'):.2f}%\n\n"

    # Add per root folder contribution
    report += "### Contribution by Root Folder\n"
    per_folder_data = repo_data["loc_data"]["Root Folder LOC"].get(contributor, {})
    report += "| Folder | Commits | Percent |\n"
    report += "|--------|-------|---------|\n"
    for folder, data in per_folder_data.items():
        lines = data.get("contributions", "N/A")
        percent = data.get("percentage", None)
        # Round the percentage to two decimal places
        percent = f"{percent:.2f}" if percent is not None else "N/A"
        report += f"| {folder} | {lines} | {percent}% |\n"
    report += "\nThe folder percentage is calculated based on the total Commits of each contributor that has contributed to the said folder.\n"

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

        # Generate the report for the repository
        report = generate_report(repo_data)

        # Write the report to the output directory
        output_file = os.path.join(repo_dir, f"{repo_name}_report.md")
        with open(output_file, "w") as file:
            file.write(report)

        # Generate detailed reports for each contributor
        contributors = repo_data["loc_data"].get("Final LOC", {}).get("data", {})
        if contributors:
            # Create a folder for contributor reports
            contributors_dir = os.path.join(repo_dir, "contributors")
            if not os.path.exists(contributors_dir):
                os.makedirs(contributors_dir)

            # Generate a report for each contributor
            for contributor in contributors:
                print(f" - Generating report for {contributor}...")
                contributor_report = generate_contributor_report(repo_data, contributor)
                if contributor_report:
                    contributor_file = os.path.join(
                        contributors_dir, f"{contributor.replace(' ', '_')}_report.md"
                    )
                    with open(contributor_file, "w") as f:
                        f.write(contributor_report)
