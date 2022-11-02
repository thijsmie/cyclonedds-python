import rich_click as click

from .settings import CONTEXT_SETTINGS
from .ls import ls
from .ps import ps
from .typeof import typeof
from .sub import subscribe
from .pub import publish
from .ddsperf import performance
from .whc import whc


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    # Initialize the CLI group
    pass


cli.add_command(ls)
cli.add_command(ps)
cli.add_command(typeof)
cli.add_command(subscribe)
cli.add_command(publish)
cli.add_command(performance)
cli.add_command(whc)

if __name__ == "__main__":
    cli()
