import uuid
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence, Set, Dict

from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table


@dataclass
class Discoverable:
    pass


@dataclass
class WSystem(Discoverable):
    applications: List["WApplication"]

    def print(
        self, console: Console, topic: str
    ):
        for app in sorted(self.applications, key=lambda x: (x.hostname, x.pid)):
            app.print(console, topic)


def participant(console, data: dict, topic: str):
    name = data.get("name", "")
    name = f"{name} ({data['guid']})" if name != "" else data["guid"]

    if not any(wr.get('topic') == topic for wr in data.get('writers', [])):
        return

    console.print(f"--- [bold bright_magenta]{name}[/] ---------")

    for writer in data.get("writers", []):
        if writer.get("topic", "") != topic:
            continue

        wr_name = writer.get("name", "")
        wr_name = f"{name} ({writer['guid']})" if wr_name != "" else writer["guid"]

        console.print(f"[bold bright_green]{name}[/]")
        console.print(writer["whc"])


@dataclass
class WApplication(Discoverable):
    hostname: str
    appname: str
    pid: str
    debug_monitor: str
    data: List[Dict[str, Any]] = field(default_factory=lambda: {'error': 'No debug monitor'})

    def print(self, console, topic):
        console.print(f"--- [bold bright_cyan]{self.hostname}/{self.appname}:{self.pid}[/] ----------")
        if 'error' in self.data:
            console.print(f"[bold bright_red]{self.data['error']}[/]")
        else:
            for p in self.data.get('participants', []):
                participant(console, p, topic)

