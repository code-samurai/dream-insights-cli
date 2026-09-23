"""Output formatters — json (default), table, text."""

from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

console = Console()


def format_output(data, fmt: str = "json", columns: list | None = None, title: str | None = None):
    """Format and print data based on output format."""
    if fmt == "json":
        print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
        return

    if fmt == "text":
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    print(" | ".join(str(v) for v in item.values()))
                else:
                    print(item)
        elif isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {v}")
        else:
            print(data)
        return

    # Table format
    if isinstance(data, dict) and not columns:
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                v = json.dumps(v, default=str)
            console.print(f"[bold]{k}[/bold]: {v}")
        return

    if isinstance(data, list) and columns:
        table = Table(title=title, show_lines=False)
        for _, header in columns:
            table.add_column(header)
        for item in data:
            row = []
            for key, _ in columns:
                val = item.get(key, "") if isinstance(item, dict) else ""
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                row.append(str(val) if val is not None else "")
            table.add_row(*row)
        console.print(table)
        return

    console.print(data)
