from threading import Thread
import rich_click as click
from rich.console import Console
from rich.syntax import Syntax

from .utils import TimeDeltaParamType, LiveData, background_progress_viewer
from .discovery.main import whc_discovery
from .discovery.whc_discoverables import WApplication, WSystem


@click.command(short_help="Scan writer caches and reader states of a specific topic.")
@click.argument("topic")
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
def whc(topic, id, runtime, suppress_progress_bar, color):
    """Scan writer caches and reader states of a specific topic."""
    console = Console(color_system=None if color == "none" else color)
    live = LiveData(console)

    thread = Thread(target=whc_discovery, args=(live, id, runtime, topic))
    thread.start()

    background_progress_viewer(runtime, live, suppress_progress_bar)

    thread.join()

    result: WSystem = live.result
    result.print(console, topic)
