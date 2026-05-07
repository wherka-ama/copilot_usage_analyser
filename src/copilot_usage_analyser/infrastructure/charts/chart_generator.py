"""Chart generator using matplotlib."""

import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


class ChartType(Enum):
    """Types of charts."""

    PIE = "pie"
    BAR = "bar"
    STACKED_BAR = "stacked_bar"
    LINE = "line"
    AREA = "area"
    TIMELINE = "timeline"


class ChartGenerator:
    """Generator for static charts using matplotlib."""

    def __init__(self, output_dir: str):
        """Initialize chart generator with output directory."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_pie_chart(
        self, data: Dict[str, int], title: str, filename: str = None
    ) -> str:
        """Generate a pie chart."""
        if not filename:
            filename = f"{title.replace(' ', '_').lower()}_pie.png"

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(data.values(), labels=data.keys(), autopct="%1.1f%%", startangle=90)
        ax.set_title(title)

        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()

        return path

    def generate_bar_chart(
        self,
        data: Dict[str, int],
        title: str,
        x_label: str = None,
        y_label: str = None,
        filename: str = None,
    ) -> str:
        """Generate a bar chart."""
        if not filename:
            filename = f"{title.replace(' ', '_').lower()}_bar.png"

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(data.keys(), data.values())
        ax.set_title(title)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)

        # Rotate x-axis labels if needed
        if len(data) > 5:
            plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()

        return path

    def generate_line_chart(
        self,
        data: List[Tuple[str, int]],
        title: str,
        x_label: str = None,
        y_label: str = None,
        filename: str = None,
    ) -> str:
        """Generate a line chart."""
        if not filename:
            filename = f"{title.replace(' ', '_').lower()}_line.png"

        x_values = [item[0] for item in data]
        y_values = [item[1] for item in data]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(x_values, y_values, marker="o")
        ax.set_title(title)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)

        # Rotate x-axis labels if needed
        if len(data) > 10:
            plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()

        return path

    def generate_stacked_bar_chart(
        self,
        data: Dict[str, Dict[str, int]],
        title: str,
        x_label: str = None,
        y_label: str = None,
        filename: str = None,
    ) -> str:
        """Generate a stacked bar chart."""
        if not filename:
            filename = f"{title.replace(' ', '_').lower()}_stacked_bar.png"

        categories = list(data.keys())
        subcategories = list(data[categories[0]].keys()) if categories else []

        fig, ax = plt.subplots(figsize=(12, 6))

        bottoms = [0] * len(categories)
        colors = plt.cm.Set3(range(len(subcategories)))

        for i, subcat in enumerate(subcategories):
            values = [data[cat].get(subcat, 0) for cat in categories]
            ax.bar(categories, values, bottom=bottoms, label=subcat, color=colors[i])
            bottoms = [bottoms[j] + values[j] for j in range(len(categories))]

        ax.set_title(title)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        ax.legend()

        if len(categories) > 5:
            plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()

        return path

    def generate_timeline_chart(
        self,
        events: List,
        title: str = "Token Usage Timeline",
        filename: str = None,
    ) -> str:
        """Generate a timeline chart showing token usage over time with labeled datapoints."""
        if not filename:
            filename = f"{title.replace(' ', '_').lower()}_timeline.png"

        # Extract timestamp and token data from events
        data_points = []
        for i, event in enumerate(events):
            if event.timestamp and event.token_usage:
                total_tokens = event.token_usage.input + event.token_usage.output + event.token_usage.cached
                if total_tokens > 0:
                    # Create short label (event index)
                    short_label = str(i + 1)
                    # Create expanded label for legend
                    event_type = event.event_type if event.event_type else "unknown"
                    model = event.details.get("model", "") if event.details else ""
                    expanded_label = f"#{i+1}: {event_type}"
                    if model:
                        expanded_label += f" ({model})"
                    
                    data_points.append({
                        "timestamp": event.timestamp,
                        "total_tokens": total_tokens,
                        "input_tokens": event.token_usage.input,
                        "output_tokens": event.token_usage.output,
                        "cached_tokens": event.token_usage.cached,
                        "short_label": short_label,
                        "expanded_label": expanded_label,
                    })

        if not data_points:
            # Generate empty chart
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.text(0.5, 0.5, "No token data available", ha="center", va="center")
            ax.set_title(title)
            path = os.path.join(self.output_dir, filename)
            plt.savefig(path, dpi=150, bbox_inches="tight")
            plt.close()
            return path

        # Sort by timestamp
        data_points.sort(key=lambda x: x["timestamp"])

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))

        # Extract data for plotting
        timestamps = [dp["timestamp"] for dp in data_points]
        total_tokens = [dp["total_tokens"] for dp in data_points]
        short_labels = [dp["short_label"] for dp in data_points]

        # Plot line
        ax.plot(timestamps, total_tokens, marker="o", linewidth=2, markersize=6, color="#2563eb")

        # Add labels to datapoints
        for i, (ts, tokens, label) in enumerate(zip(timestamps, total_tokens, short_labels)):
            # Only label significant points to avoid overcrowding
            if i % max(1, len(data_points) // 20) == 0 or tokens == max(total_tokens):
                ax.annotate(label, (ts, tokens), textcoords="offset points",
                           xytext=(0, 10), ha="center", fontsize=8, alpha=0.7)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Time", fontsize=11)
        ax.set_ylabel("Total Tokens", fontsize=11)
        ax.grid(True, alpha=0.3)

        # Format x-axis
        fig.autofmt_xdate(rotation=45, ha="right")

        # Create legend with expanded labels (sample to avoid overcrowding)
        legend_samples = data_points[::max(1, len(data_points) // 10)]
        legend_handles = []
        legend_labels = []
        for dp in legend_samples:
            handle = plt.Line2D([], [], marker="o", color="#2563eb", 
                               markersize=6, linestyle="None")
            legend_handles.append(handle)
            # Truncate label if too long
            label = dp["expanded_label"]
            if len(label) > 40:
                label = label[:37] + "..."
            legend_labels.append(label)
        
        if legend_labels:
            ax.legend(legend_handles, legend_labels, loc="upper left", 
                     bbox_to_anchor=(1.02, 1), fontsize=9)

        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()

        return path
