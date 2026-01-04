import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import random
import os
import numpy as np


def get_member_colors(members: list) -> dict:
    """
    Generate consistent colors for members based on alphabetically sorted names.
    
    Args:
        members: List of member names
        
    Returns:
        dict: Mapping of member names to colors
    """
    sorted_members = sorted(set(members))
    color_palette = plt.cm.tab10(np.linspace(0, 1, max(10, len(sorted_members))))
    return {
        member: color_palette[i % len(color_palette)]
        for i, member in enumerate(sorted_members)
    }


def generate_commit_timeline(
    repo_data: dict,
    account_mapping: dict,
    output_path: str,
    figsize: tuple = (16, 4),
    dpi: int = 150,
):
    """
    Generate a horizontal timeline image from git commit history.

    Args:
        repo_data: Dictionary containing repository analysis data with members_commits
        account_mapping: Dictionary mapping git usernames to display names
        output_path: Path where the image will be saved
        figsize: Figure size (width, height) in inches
        dpi: Image resolution

    Returns:
        str: Path to the generated image, or None if generation failed
    """
    members_commits = repo_data.get("members_commits", {})

    if not members_commits:
        print("No commit data available for timeline generation")
        return None

    # Collect all commits with their data
    all_commits = []
    for member, commits in members_commits.items():
        mapped_member = account_mapping.get(member, member)
        for commit in commits:
            try:
                # Parse the date string
                date_str = commit.get("date", "")
                if date_str:
                    # Handle timezone-aware datetime strings
                    if "+" in date_str or date_str.endswith("Z"):
                        # Remove timezone info for simplicity
                        date_str = date_str.split("+")[0].split("Z")[0].strip()
                    commit_date = datetime.fromisoformat(date_str)

                    lines_changed = commit.get("lines_added", 0) + commit.get(
                        "lines_deleted", 0
                    )
                    all_commits.append(
                        {
                            "date": commit_date,
                            "member": mapped_member,
                            "lines_changed": lines_changed,
                            "lines_added": commit.get("lines_added", 0),
                            "lines_deleted": commit.get("lines_deleted", 0),
                            "message": commit.get("message", "")[:50],
                        }
                    )
            except Exception as e:
                print(f"Error parsing commit date: {e}")
                continue

    if not all_commits:
        print("No valid commits found for timeline generation")
        return None

    # Sort commits by date
    all_commits.sort(key=lambda x: x["date"])

    # Get unique members and assign colors consistently
    unique_members = list(set(c["member"] for c in all_commits))
    unique_members.sort()
    member_colors = get_member_colors(unique_members)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)

    # Set random seed for reproducibility of y positions
    random.seed(42)

    # Calculate point sizes based on lines changed
    # Normalize sizes to a reasonable range (20-500)
    max_lines = max(c["lines_changed"] for c in all_commits) if all_commits else 1
    min_size = 20
    max_size = 500

    # Assign consistent random y positions per member to create lanes with jitter
    member_base_y = {
        member: i / (len(unique_members) - 1) if len(unique_members) > 1 else 0.5
        for i, member in enumerate(unique_members)
    }

    # Plot each commit
    for commit in all_commits:
        member = commit["member"]
        date = commit["date"]
        lines = commit["lines_changed"]

        # Calculate size (logarithmic scale for better visualization)
        if lines > 0:
            size = min_size + (np.log1p(lines) / np.log1p(max_lines)) * (
                max_size - min_size
            )
        else:
            size = min_size

        # Y position: base position for member + random jitter
        base_y = member_base_y[member]
        jitter = random.uniform(-0.08, 0.08)
        y_pos = base_y + jitter

        # Clamp y position to valid range
        y_pos = max(0.05, min(0.95, y_pos))

        ax.scatter(
            date,
            y_pos,
            s=size,
            c=[member_colors[member]],
            alpha=0.7,
            edgecolors="white",
            linewidths=0.5,
            zorder=3,
        )

    # Format the x-axis for dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    # Rotate date labels for better readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Set y-axis limits and hide y-axis labels (since y is just for visual separation)
    ax.set_ylim(-0.1, 1.1)
    ax.set_yticks([])
    ax.set_ylabel("")

    # Add grid for x-axis only
    ax.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Set title
    ax.set_xlabel("Date", fontsize=11)

    # Create legend for members (colors)
    legend_handles = [
        plt.scatter(
            [],
            [],
            c=[member_colors[member]],
            s=100,
            label=member,
            alpha=0.7,
            edgecolors="white",
        )
        for member in unique_members
    ]

    # Create size legend
    size_examples = [10, 100, 1000, 5000]
    size_handles = []
    for lines in size_examples:
        if lines <= max_lines:
            size = min_size + (np.log1p(lines) / np.log1p(max_lines)) * (
                max_size - min_size
            )
            size_handles.append(
                plt.scatter(
                    [],
                    [],
                    c="gray",
                    s=size,
                    label=f"{lines} lines",
                    alpha=0.5,
                    edgecolors="white",
                )
            )

    # Add both legends
    first_legend = ax.legend(
        handles=legend_handles,
        title="Contributors",
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        framealpha=0.9,
    )
    ax.add_artist(first_legend)

    if size_handles:
        ax.legend(
            handles=size_handles,
            title="Commit Size",
            loc="lower left",
            bbox_to_anchor=(1.01, 0),
            framealpha=0.9,
        )

    # Adjust layout to fit legends
    plt.tight_layout()
    plt.subplots_adjust(right=0.82)

    # Add some statistics text
    earliest = min(c["date"] for c in all_commits)
    latest = max(c["date"] for c in all_commits)
    total_commits = len(all_commits)

    stats_text = f"Period: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')} | Total commits: {total_commits}"
    fig.text(0.5, 0.02, stats_text, ha="center", fontsize=9, style="italic", alpha=0.7)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the figure
    plt.savefig(
        output_path, dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close(fig)

    print(f"Timeline image saved to: {output_path}")
    return output_path


def generate_contribution_summary(
    repo_data: dict,
    account_mapping: dict,
    output_path: str,
    figsize: tuple = (14, 6),
    dpi: int = 150,
):
    """
    Generate a contribution summary chart showing member contributions.

    Args:
        repo_data: Dictionary containing repository analysis data
        account_mapping: Dictionary mapping git usernames to display names
        output_path: Path where the image will be saved
        figsize: Figure size (width, height) in inches
        dpi: Image resolution

    Returns:
        str: Path to the generated image, or None if generation failed
    """
    members_commits = repo_data.get("members_commits", {})

    if not members_commits:
        print("No commit data available for contribution summary")
        return None

    # Aggregate data per member
    member_stats = {}
    for member, commits in members_commits.items():
        mapped_member = account_mapping.get(member, member)
        if mapped_member not in member_stats:
            member_stats[mapped_member] = {
                "commits": 0,
                "lines_added": 0,
                "lines_deleted": 0,
            }
        member_stats[mapped_member]["commits"] += len(commits)
        for commit in commits:
            member_stats[mapped_member]["lines_added"] += commit.get("lines_added", 0)
            member_stats[mapped_member]["lines_deleted"] += commit.get(
                "lines_deleted", 0
            )

    if not member_stats:
        print("No member statistics available")
        return None

    # Sort members by total lines contributed
    sorted_members = sorted(
        member_stats.keys(),
        key=lambda m: member_stats[m]["lines_added"] + member_stats[m]["lines_deleted"],
        reverse=True,
    )

    # Prepare data for plotting
    members = sorted_members
    commits = [member_stats[m]["commits"] for m in members]
    lines_added = [member_stats[m]["lines_added"] for m in members]
    lines_deleted = [member_stats[m]["lines_deleted"] for m in members]

    # Use consistent colors based on alphabetically sorted members
    member_colors_dict = get_member_colors(members)
    member_colors = [member_colors_dict[m] for m in members]

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # 1. Pie chart for commits distribution
    ax1 = axes[0, 0]
    wedges, texts, autotexts = ax1.pie(
        commits,
        labels=members,
        autopct=lambda pct: f"{pct:.1f}%" if pct > 5 else "",
        colors=member_colors,
        startangle=90,
        explode=[0.02] * len(members),
    )
    ax1.set_title("Commits Distribution", fontsize=12, fontweight="bold")

    # 2. Horizontal bar chart for lines added/deleted
    ax2 = axes[0, 1]
    y_pos = np.arange(len(members))
    bar_height = 0.35

    bars_added = ax2.barh(
        y_pos - bar_height / 2,
        lines_added,
        bar_height,
        label="Lines Added",
        color="green",
        alpha=0.7,
    )
    bars_deleted = ax2.barh(
        y_pos + bar_height / 2,
        lines_deleted,
        bar_height,
        label="Lines Deleted",
        color="red",
        alpha=0.7,
    )

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(members)
    ax2.set_xlabel("Lines")
    ax2.set_title("Lines Added vs Deleted", fontsize=12, fontweight="bold")
    ax2.legend(loc="lower right")
    ax2.grid(True, axis="x", alpha=0.3, linestyle="--")

    # 3. Bar chart for number of commits
    ax3 = axes[1, 0]
    bars = ax3.bar(members, commits, color=member_colors, alpha=0.8, edgecolor="white")
    ax3.set_ylabel("Number of Commits")
    ax3.set_title("Commits per Contributor", fontsize=12, fontweight="bold")
    ax3.tick_params(axis="x", rotation=45)
    ax3.grid(True, axis="y", alpha=0.3, linestyle="--")

    # Add value labels on bars
    for bar, val in zip(bars, commits):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(commits) * 0.01,
            str(val),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # 4. Stacked bar chart for total contribution
    ax4 = axes[1, 1]
    total_lines = [a + d for a, d in zip(lines_added, lines_deleted)]

    bars_total = ax4.bar(
        members,
        lines_added,
        label="Added",
        color="green",
        alpha=0.7,
        edgecolor="white",
    )
    ax4.bar(
        members,
        lines_deleted,
        bottom=lines_added,
        label="Deleted",
        color="red",
        alpha=0.7,
        edgecolor="white",
    )

    ax4.set_ylabel("Total Lines Changed")
    ax4.set_title("Total Lines Changed per Contributor", fontsize=12, fontweight="bold")
    ax4.tick_params(axis="x", rotation=45)
    ax4.legend(loc="upper right")
    ax4.grid(True, axis="y", alpha=0.3, linestyle="--")

    # Add total labels on top
    for i, (bar, total) in enumerate(zip(bars_total, total_lines)):
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            total + max(total_lines) * 0.01,
            f"{total:,}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the figure
    plt.savefig(
        output_path, dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close(fig)

    print(f"Contribution summary saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test with sample data
    import json

    # Load sample data if available
    sample_commits_file = "./commits_reports/RTT-Labyrinth-Project_report.json"
    if os.path.exists(sample_commits_file):
        with open(sample_commits_file, "r") as f:
            repo_data = json.load(f)

        # Create a simple account mapping (identity mapping)
        members = list(repo_data.get("members_commits", {}).keys())
        account_mapping = {m: m for m in members}

        generate_commit_timeline(repo_data, account_mapping, "./test_timeline.png")
        generate_contribution_summary(
            repo_data, account_mapping, "./test_contribution_summary.png"
        )
    else:
        print(f"Sample file not found: {sample_commits_file}")
