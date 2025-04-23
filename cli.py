import click

@click.command()
@click.argument('runs_dir', type=click.Path(exists=True, writable=True, file_okay=False))
def touch(runs_dir: str):
    """Print Directory name if the directory exists."""
    click.echo(click.format_filename(runs_dir))

if __name__ == '__main__':
    touch()