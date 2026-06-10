"""Rich-formatted terminal status helpers."""
import sys

from rich.console import Console

_out = Console()
_err = Console(stderr=True)


def success(msg: str) -> None:
    _out.print(f"[green]\\[✓][/green] {msg}")


def progress(msg: str) -> None:
    _out.print(f"[cyan]\\[→][/cyan] {msg}")


def warning(msg: str) -> None:
    _out.print(f"[yellow]\\[!][/yellow] {msg}")


def error(msg: str, likely_cause: str = "", remediation: str = "") -> None:
    _err.print(f"[red]\\[✗][/red] {msg}")
    if likely_cause:
        _err.print(f"    Likely cause: {likely_cause}")
    if remediation:
        _err.print(f"    {remediation}")
    sys.exit(1)
