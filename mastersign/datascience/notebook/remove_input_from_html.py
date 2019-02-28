# -*- coding: utf-8 -*-

import click
from bs4 import BeautifulSoup, Tag


def remove_input_from_html(file):
    """
    Remove input blocks from Jupyter notebook HTML output.

    :param file: A path to the HTML file to process.
    """
    with open(file, 'r', encoding='utf8') as f:
        html_text = f.read()
    doc = BeautifulSoup(html_text, 'html.parser')
    for tag in doc.select('div.input'):
        tag.decompose()
    for tag in doc.select('div.code_cell'):
        if not list(filter(lambda t: type(t) is Tag, tag.contents)):
            tag.decompose()
    with open(file, 'w', encoding='utf8') as f:
        f.write(str(doc))


@click.command(help='Remove input blocks from Jupyter notebook HTML output.'
                    'The given HTML file will be changed in place.')
@click.argument('file', type=click.Path(exists=True,
                                        file_okay=True, dir_okay=False,
                                        readable=True, writable=True))
def cli(file):
    remove_input_from_html(file)


if __name__ == '__main__':
    cli()
