import click


@click.command()
@click.option('--name', default='World', help='Name to greet.')
def main(name):
    click.echo(f'Hello, {name}! This is Graphrag WebUI.')


if __name__ == '__main__':
    main()
