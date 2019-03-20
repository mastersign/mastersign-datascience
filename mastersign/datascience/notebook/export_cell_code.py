# -*- coding: utf-8 -*-

import click
import json
import os


def _cell_type(cell):
    if 'cell_type' not in cell:
        return None
    return cell['cell_type']


def _cell_tags(cell):
    if 'metadata' not in cell:
        return list()
    metadata = cell['metadata']
    if 'tags' not in metadata:
        return list()
    return metadata['tags']


def export_cell_code(nb_file, py_file=None, tag='production'):
    """
    Take the source of all code cells, tagged with the given tag,
    from the given notebook and write them into a Python code file.

    :param nb_file: A path to a Jupyter Notebook.
    :param py_file: A path to a Python script file as target.
    :param tag:     A tag name for the code cell selection.
                    Defaults to ``production``.
    """
    with open(nb_file, 'r', encoding='utf8') as f:
        nb = json.load(f)
    code_cells = filter(lambda cell: _cell_type(cell) == 'code', nb['cells'])
    production_cells = filter(lambda cell: tag in _cell_tags(cell), code_cells)

    with open(py_file, 'w', encoding='utf8') as f:
        f.write("# -*- coding: utf-8 -*-\n\n")
        for cell in production_cells:
            for line in cell['source']:
                f.write(line)
            f.write("\n\n")


@click.command(help='Take the source of all code cells, tagged with the given tag, '
                    'from the given notebook and write them into a Python code file.')
@click.argument('file', type=click.Path(exists=True,
                                        file_okay=True, dir_okay=False,
                                        readable=True, writable=True))
@click.option('-o', '--out-file',
              type=click.Path(file_okay=True, dir_okay=False,
                              writable=True),
              required=False,
              help='A path to the Python code file to write.')
@click.option('-t', '--tag',
              type=str, default='production', show_default=True,
              help='A tag for the cell selection.')
def cli(file, out_file, tag):
    if out_file is None:
        out_file = os.path.splitext(file)[0] + '_' + tag + '.py'
    export_cell_code(file, out_file, tag)


if __name__ == '__main__':
    cli()
