import re
import time
from typing import Any
from queue import Queue
from datetime import timedelta, datetime

import rich_click as click
from rich import print
from rich.pretty import Pretty
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn


class TimeDeltaParamType(click.ParamType):
    name = "timedelta"

    _wordy_format = re.compile(
        r"^\s*((?P<hours>\d+)h(?:r|rs|ours|our)?)?\s*((?P<minutes>\d+)m(?:i|in|inutes|inute)?)?\s*((?P<seconds>\d+)s(?:e|ec|econds|econd)?)?\s*$"
    )
    _colon_format = re.compile(
        r"^\s*((?P<hours>\d+)\s*:)?(\s*(?P<minutes>\d+)\s*:)?\s*(?P<seconds>\d+)\s*$"
    )

    def convert(self, value, param, ctx):
        if isinstance(value, timedelta):
            return value

        for regex in [self._wordy_format, self._colon_format]:
            m = regex.match(value)
            if m:
                return timedelta(
                    hours=int(m.group("hours") or 0),
                    minutes=int(m.group("minutes") or 0),
                    seconds=int(m.group("seconds") or 0),
                )

        self.fail(f"{value} is not a valid timedelta", param, ctx)


class LiveData:
    def __init__(self) -> None:
        self.delivered: bool = False
        self.terminate: bool = False
        self.entities: int = 0
        self.result: Any = None
        self.printables: Queue = Queue()


progress = Progress(
    TextColumn("  "),
    TimeElapsedColumn(),
    BarColumn(),
    TextColumn("[blue]Entities discovered:[/] [bold purple]{task.fields[entities]}[/]"),
)


def background_progress_viewer(runtime: timedelta, data: LiveData):
    start = datetime.now()
    end = start + runtime
    with progress:
        try:
            task = progress.add_task("", entities=0, total=1)
            while end > datetime.now() and not data.terminate:
                time.sleep(0.2)
                progress.update(
                    task,
                    completed=((datetime.now() - start) / runtime),
                    entities=data.entities,
                )
            progress.update(task, completed=1)
            time.sleep(0.1)
        except KeyboardInterrupt:
            data.terminate = True
            return


def background_printer(data: LiveData):
    try:
        while not data.terminate:
            time.sleep(0.2)
            while data.printables:
                print(Pretty(data.printables.get()))
        time.sleep(0.1)
    except KeyboardInterrupt:
        data.terminate = True
        return
