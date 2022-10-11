import csv
import json
import sys
from threading import Thread
from typing import Optional, List
import rich_click as click
from rich.console import Console

from .utils import TimeDeltaParamType, LiveData, background_progress_viewer
from .discovery.main import ls_discovery
from .discovery.ls_discoverables import DParticipant, fmt_ident


@click.command(short_help="Scan and display DDS entities in your network")
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
    "--show-self",
    type=bool,
    is_flag=True,
    help="Show the tools own participant and subscriptions.",
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
    "-q",
    "--qos",
    type=bool,
    is_flag=True,
    help="Show the QoS settings of all entities.",
    default=False,
)
@click.option(
    "-m",
    "--machine-readable",
    type=bool,
    is_flag=True,
    help="Disable fancy output format and just print CSV. '--suppress-progress-bar' and '--color=none` are implied.",
    default=False,
)
def ls(
    topic, id, runtime, show_self: bool, suppress_progress_bar: bool, color, qos: bool, machine_readable
):
    if machine_readable:
        color = None
        suppress_progress_bar = True

    """Scan and display DDS entities in your network."""
    console = Console(color_system=None if color == "none" else color)
    live = LiveData(console)

    thread = Thread(target=ls_discovery, args=(live, id, runtime, topic, qos))
    thread.start()

    background_progress_viewer(runtime, live, suppress_progress_bar)

    thread.join()

    result: Optional[List[DParticipant]] = live.result

    if result and not machine_readable:
        for p in result:
            if p.is_self and not show_self:
                continue

            console.print(p)
            console.print()
    elif machine_readable:
        csvwriter = csv.DictWriter(
            f=sys.stdout,
            fieldnames=["Pub/Sub", "Participant", "Topic", "Typename", "XTypesID"] + (["Qos"] if qos else []),
            dialect='unix',
            extrasaction='ignore',
            quoting=csv.QUOTE_NONNUMERIC
        )

        csvwriter.writeheader()

        if result:
            for participant in result:
                if participant.is_self and not show_self:
                    continue

                pname = participant.fullname()
                for topic in participant.topics:
                    for reader in topic.subscriptions:
                        csvwriter.writerow({
                            "Pub/Sub": "Sub",
                            "Participant": pname,
                            "Topic": topic.name,
                            "Typename": reader.endpoint.type_name or "",
                            "XTypesID": fmt_ident(reader.endpoint.type_id),
                            "Qos": json.dumps(reader.endpoint.qos.asdict())
                        })
                    for writer in topic.publications:
                        csvwriter.writerow({
                            "Pub/Sub": "Pub",
                            "Participant": pname,
                            "Topic": topic.name,
                            "Typename": writer.endpoint.type_name or "",
                            "XTypesID": fmt_ident(writer.endpoint.type_id),
                            "Qos": json.dumps(writer.endpoint.qos.asdict())
                        })
