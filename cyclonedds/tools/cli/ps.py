import sys
import csv
from threading import Thread
import rich_click as click
from rich.console import Console

from .utils import TimeDeltaParamType, LiveData, background_progress_viewer
from .discovery.main import ps_discovery
from .discovery.ps_discoverables import PSystem


@click.command(short_help="Scan and display DDS applications in your network")
@click.option(
    "-i", "--id", "--domain-id", type=int, default=0, help="DDS Domain to inspect."
)
@click.option(
    "-r",
    "--runtime",
    type=TimeDeltaParamType(),
    default="1s",
    help="Duration of discovery scan.",
)
@click.option(
    "-t",
    "--topic",
    type=str,
    help="Filter which entity types to display by topic name (supports regex)",
    default=".*",
)
@click.option(
    "--show-self", type=bool, is_flag=True, help="Show the tools own application."
)
@click.option(
    "--suppress-progress-bar",
    type=bool,
    is_flag=True,
    help="Suppress the output of the progress bar",
)
@click.option(
    "--color",
    type=click.Choice(["auto", "standard", "256", "truecolor", "windows", "none"]),
    default="auto",
    help="""Force the command to output with/without terminal colors. By default output colours if the terminal supports it."
See the [underline blue][link=https://rich.readthedocs.io/en/stable/console.html#color-systems]Rich documentation[/link][/] for more info on what the options mean.""",
)
@click.option(
    "-m",
    "--machine-readable",
    type=bool,
    is_flag=True,
    help="Disable fancy output format and just print CSV. '--suppress-progress-bar' and '--color=none` are implied.",
    default=False,
)
def ps(id, runtime, topic, show_self, suppress_progress_bar, color, machine_readable):
    """Scan and display DDS applications in your network"""

    if machine_readable:
        color = None
        suppress_progress_bar = True

    console = Console(color_system=None if color == "none" else color)
    live = LiveData(console)

    thread = Thread(target=ps_discovery, args=(live, id, runtime, show_self, topic))
    thread.start()

    background_progress_viewer(runtime, live, suppress_progress_bar)

    thread.join()

    result: PSystem = live.result

    if machine_readable:
        writer = csv.DictWriter(
            f=sys.stdout,
            fieldnames=["Host", "Application", "Pid", "Participants", "Topics"],
            dialect='unix',
            quoting=csv.QUOTE_NONNUMERIC
        )

        writer.writeheader()

        for application in result.applications:
            writer.writerow(application.asdict())
    else:
        console.print(live.result)
