# -*- coding: utf-8 -*-

"""
This module contains functionality to comfortably create plots.
"""

from math import floor, ceil, pi
from itertools import islice, chain, cycle, repeat
from collections.abc import Iterable, Mapping
from typing import Union
from warnings import warn
import pandas as pd
import pandas.api.types as pd_types
import numpy as np
from scipy import interpolate
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as plt_colors
import matplotlib.cm as plt_cm
import matplotlib.lines as mlines
import mpl_toolkits.axes_grid1 as axg1
from configparser import ConfigParser
from IPython.display import HTML, display
from tabulate import tabulate

_col_labels = {
    'count': 'Anzahl'
}


def spec_col_labels(**kwargs):
    """
    Specify labels for column names to be automatically used in plots.

    :param kwargs: A map of column names and labels.
    """
    _col_labels.update(kwargs)


def spec_col_file(filename):
    """
    Specify an INI file with column names to be automatically used in plots.
    The column-label-pairs must be placed under the INI section `[Columns]`.

    :param filename: A path to the INI file.
    """
    cfg = ConfigParser()
    cfg.read(filename, encoding='utf8')
    _col_labels.update(cfg['Columns'])


def _col_label(label, column):
    if label is not None:
        return label
    if column in _col_labels:
        return _col_labels[column]
    return column


def table(data: pd.DataFrame, columns=None, labels=None,
          with_index=True, index_label=None, limit=None):
    """
    Displays an HTML table with the given data.
    A subset of columns can be selected with `columns`.
    The labels in the header can be explicitly specified with `labels`.

    Does not support multi-indexes.

    Calls `IPython.display.display()` to present the HTML table.

    :param data:        A Pandas DataFrame
    :param columns:     An iterable with column names. (optional)
    :param labels:      An iterable with column labels. (optional)
                        Must be the same size as the columns.
    :param with_index:  A switch to include or exclude the index. (optional)
    :param index_label: A string or an iterable with labels for the index.
                        (optional)
    :param limit:       A maximum number of rows to display. (optional)
    """
    if data.empty:
        display(HTML('<p>No Entries</p>'))
    columns = columns or data.columns
    if labels:
        headers = labels
    else:
        headers = [_col_labels[c] if c in _col_labels else c for c in columns]
    if with_index:
        headers.insert(0, index_label or 'index')

        def cells(r):
            return chain((r[0],), (getattr(r, c) for c in columns))
    else:
        def cells(r):
            return (getattr(r, c) for c in columns)
    rows = map(cells, data.itertuples())
    if limit:
        rows = islice(rows, limit)
    display(HTML(tabulate(rows, tablefmt='html', headers=headers)))


def _default_figure_handler(subplot, fig, ax=None,
                            title=None, pad=None,
                            file_name=None, file_dpi=None):
    if not fig:
        return
    if not subplot:
        if pad is not None:
            fig.tight_layout(pad=pad)
        if file_name:
            fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax = ax or fig.gca()
        if ax:
            ax.set_title(title)
    if not subplot:
        plt.show()


current_figure = None
current_grid = (1, 1)
_figure_handler = _default_figure_handler


def _finish_figure(fig=None, **kwargs):
    if fig is None:
        return
    _figure_handler(subplot=_in_multiplot(), fig=fig, **kwargs)


def set_figure_handler(handler):
    """
    Set a handler, which is called after rendering every plot.

    The specified handler must accept the following keyword arguments:

    - ``subplot`` A boolean flag indicating that the figure is a subplot
    - ``fig`` The figure object of the plot
    - ``ax`` The main axis or `None`
    - ``title`` A title for the main axis or `None`
    - ``pad`` A padding value for calling `tight_layout()` or `None`
    - ``file_name`` The filename for the target image file or `None`
    - ``file_dpi`` The dpi value for the target image file or `None`

    :param handler: The figure handler to use for future plots
    """
    global _figure_handler
    _figure_handler = handler


def reset_figure_handler():
    """
    Reset the handler, which is called after rendering every plot,
    to the default.
    """
    global _figure_handler
    _figure_handler = _default_figure_handler


def begin(figsize=(10, 5), grid=(1, 1)):
    """
    Begins a figure with multiple subplots.

    :param figsize: A tuple with the figure size in inches (width, height).
                    (optional)
    :param grid:    The grid size to place the subplots in (rows, columns).
                    (optional)
    """
    global current_figure, current_grid
    if current_figure is not None:
        warn("There is already an open figure. Did you use end()?")
    current_figure = plt.figure(figsize=figsize)
    current_grid = grid


def end(pad=1.5, w_pad=None, h_pad=None,
        file_name=None, file_dpi=300):
    """
    Finalizes a figure with multiple subplots.

    :param pad:       Padding around the figure. (optional)
    :param w_pad:     Horizontal space between subplots. (optional)
                      See `matplotlib.pyplot.tight_layout()`.
    :param h_pad:     Vertical space between subplots. (optional)
                      See `matplotlib.pyplot.tight_layout()`.
    :param file_name: A path to a file to save the plot in. (optional)
    :param file_dpi:  A resolution to render the saved plot. (optional)
    """
    global current_figure, current_title
    if current_figure is None:
        raise Exception("No current figure. Did you use begin()?")
    if pad is not None:
        plt.tight_layout(pad=pad, h_pad=h_pad, w_pad=w_pad)
    elif h_pad is not None or w_pad is not None:
        plt.tight_layout(h_pad=h_pad, w_pad=w_pad)

    fig = current_figure
    current_figure = None
    _finish_figure(
        fig=fig, pad=None,
        file_name=file_name, file_dpi=file_dpi)


def _in_multiplot():
    global current_figure
    return current_figure is not None


def _plt(figsize=(10, 4), pos=(0, 0), rowspan=1, colspan=1):
    global current_figure, current_grid
    if current_figure:
        ax = plt.subplot2grid(current_grid, pos,
                              rowspan=rowspan, colspan=colspan)
        return (current_figure, ax)
    else:
        fig = plt.figure(figsize=figsize)
        return (fig, plt.gca())


def subplot(pos=(0, 0), rowspan=1, colspan=1):
    """
    Prepares a sub-plot inside the current figure between calls
    of `begin()` and `end()`.

    This method is useful, if a custom plot must be integrated
    into a multiplot created with `mastersign.datasience.plot`.

    :param pos:     The position in the grid of a multiplot. (optional)
    :param rowspan: The number of rows to span in the grid
                    of a multiplot. (optional)
    :param colspan: The number of columns to span in the grid
                    of a multiplot. (optional)
    :return:        A tuple with Matplotlib figure and axes: ``(fig, ax)``.
    """
    if not _in_multiplot():
        raise Exception("No current figure. Did you use begin()?")
    return _plt(pos=pos, rowspan=rowspan, colspan=colspan)


def _build_key_colors(keys, color):
    if isinstance(color, str):
        return repeat(color, len(keys))
    elif isinstance(color, Mapping):
        return [color.get(k, None) or next(plt.gca()._get_lines.prop_cycler)['color']
                for k in keys]
    elif isinstance(color, Iterable):
        return cycle(color)
    else:
        return [next(plt.gca()._get_lines.prop_cycler)['color'] for k in keys]


def pie(data: Union[pd.DataFrame, pd.Series],
        column=None, label_column=None,
        color_column=None, color=None,
        startangle=180, counterclock=False,
        sort_by=None, title=None, pct=True,
        figsize=(4, 4), pad=1, pos=(0, 0), rowspan=1, colspan=1,
        file_name=None, file_dpi=300):
    """
    Display a pie chart with values from a column in a DataFrame
    or a Series.

    :param data:         A Pandas DataFrame or Series.
    :param column:       The column to use if `data` is a DataFrame.
    :param label_column: A column to use for the labels. (optional)
                         By default the index is used.
    :param color_column: A column with color names or RGB hex values.
                         (optional)
    :param color:        A list or dict for the colors in the pie.
                         (optional)
                         If it is a dict the keys are the labels.
                         Gets overridden by `color_column`.
    :param sort_by:      The sort mode `None`, `"label"`, or `"value"`
                         (optional)
    :param startangle:   The start angle in degrees. (optional)
    :param counterclock: A switch to control the angular order. (optional)
    :param title:        The title of the plot. (optional)
    :param pct:          A switch to display percentages. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pad:          Padding around the figure. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """

    if isinstance(data, pd.DataFrame):
        # data is a DataFrame
        if column is None:
            raise TypeError("If data is a DataFrame, column must be specified.")
        if sort_by:
            data = data.sort_values(by=label_column) \
                if label_column else data.sort_index()
        if sort_by == 'value':
            data.sort_values(by=column, ascending=False, inplace=True)
        x = data[column]
        labels = data[label_column] if label_column else data.index
    else:
        # data is assumed to be a Series
        if sort_by:
            data = data.sort_index()
        if sort_by == 'value':
            data.sort_values(ascending=False, inplace=True)

        x = data
        labels = data.index
        color_column = None  # ignore color_column for Series

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)

    if color_column:
        colors = data[color_column]
    elif isinstance(color, Mapping):
        colors = [color.get(l) or next(plt.gca()._get_lines.prop_cycler)['color']
                  for l in labels]
    elif color:
        colors = color
    else:
        colors = None

    if pct:
        ax.pie(x, labels=labels, colors=colors,
               startangle=startangle, counterclock=counterclock,
               autopct='%1.1f%%')
    else:
        ax.pie(x, labels=labels, colors=colors,
               startangle=startangle, counterclock=counterclock)
    ax.axis('equal')

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def pie_groups(data: Union[pd.DataFrame, pd.Series],
               column=None, sort_by=None,
               startangle=180, counterclock=False,
               title=None, pct=True, color=None,
               figsize=(4, 4), pad=1, pos=(0, 0), rowspan=1, colspan=1,
               file_name=None, file_dpi=300):
    """
    Display a pie chart by counting rows according to a column value
    from a DataFrame or values from a Series.

    :param data:      A Pandas DataFrame or Series.
    :param column:    The column to use for grouping.
    :param sort_by:   The sort mode `None`, `"label"`, or `"value"`
    :param startangle:   The start angle in degrees. (optional)
    :param counterclock: A switch to control the angular order. (optional)
    :param title:     The title of the plot.
    :param pct:       A switch to display percentages.
    :param color:     A list or dict for the colors in the pie.
                      (optional)
                      If it is a dict the groups are the labels.
    :param figsize:   The figure size in inches. (optional)
    :param pad:       Padding around the figure. (optional)
    :param pos:       The position in the grid of a multiplot. (optional)
    :param rowspan:   The number of rows to span in the grid
                      of a multiplot. (optional)
    :param colspan:   The number of columns to span in the grid
                      of a multiplot. (optional)
    :param file_name: A path to a file to save the plot in. (optional)
    :param file_dpi:  A resolution to render the saved plot. (optional)
    """

    if isinstance(data, pd.DataFrame):
        groups = data.groupby(column, sort=False).size()
    else:
        groups = data.groupby(by=data, sort=False).size()
    group_data = pd.DataFrame({'value': groups}, index=groups.index)
    pie(group_data, 'value', sort_by=sort_by,
        startangle=startangle, counterclock=counterclock,
        title=title, pct=pct, color=color,
        figsize=figsize, pad=pad, pos=pos, rowspan=rowspan, colspan=colspan,
        file_name=file_name, file_dpi=file_dpi)


def bar(data: Union[pd.DataFrame, pd.Series],
        value_column=None, label_column=None,
        color_column=None, cmap=None, color=None,
        xlabel=None, ylabel=None, title=None,
        figsize=(10, 4), pad=1, pos=(0, 0), rowspan=1, colspan=1,
        file_name=None, file_dpi=300):
    """
    Display a bar chart from columns in a DataFrame or a Series.

    :param data:         A Pandas DataFrame or Series.
    :param value_column: The column with the values for the bars height.
    :param label_column: The column with the labels for the bars. (optional)
    :param color_column: The column with a numeric value for choosing
                         a color from a color map or strings
                         for explicit colors. (optional)
    :param cmap:         The name of a color map to use with `color_column`.
                         (optional)
    :param color:        A color for all bars or a list with colors. (optional)
                         `color_column` superseeds `color`.
    :param xlabel:       The label for the X axis. (optional)
    :param ylabel:       The label for the Y axis. (optional)
    :param title:        The title of the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pad:          Padding around the figure. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """

    if isinstance(data, pd.DataFrame):
        all_columns = [value_column, label_column, color_column]
        columns = set(c for c in all_columns if c)
        data = data.loc[:, columns].dropna()
        values = data[value_column]
        if label_column:
            labels = data[label_column]
        else:
            labels = values.index
    else:
        values = data
        labels = data.index
        color_column = None  # ignore color_column for Series

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    bars = ax.bar(labels, values)
    if color_column:
        colors = data[color_column]
        if pd_types.is_numeric_dtype(colors.dtype):
            color_map = plt_cm.get_cmap(cmap)
            norm = plt_colors.Normalize(vmin=colors.min(), vmax=colors.max())
            for b, cv in zip(bars, colors):
                b.set_color(color_map(norm(cv)))
        else:
            for b, c in zip(bars, colors):
                b.set_color(c)
    elif color:
        if type(color) is str:
            for b in bars:
                b.set_color(color)
        else:
            for b, c in zip(bars, cycle(color)):
                b.set_color(c)
    ax.set_xlabel(_col_label(xlabel, label_column))
    ax.set_ylabel(_col_label(ylabel, value_column))

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def bar_groups(data: pd.DataFrame,
        value_column, key_column, keys=None, label_column=None,
        color_column=None, cmap=None, color=None,
        stacked=False, relative=False,
        xlabel=None, ylabel=None, title=None, legend=True,
        figsize=(10, 4), pad=1, pos=(0, 0), rowspan=1, colspan=1,
        file_name=None, file_dpi=300):
    """
    Display a bar chart with grouped bars from columns in a DataFrame.

    :param data:         A Pandas DataFrame.
    :param value_column: The column with the values for the bars height.
    :param key_column:   The column with the key to group by.
    :param keys:         A list with group keys to select. (optional)
                         By default the group keys are taken from the key
                         column and sorted alphabetically.
    :param label_column: The column with the labels for the bars. (optional)
    :param color_column: The column with a numeric value for choosing
                         a color from a color map or strings
                         for explicit colors. (optional)
    :param cmap:         The name of a color map to use with `color_column`.
                         (optional)
    :param color:        A list or dict with colors for the groups. (optional)
                         `color_column` superseeds `color`.
    :param stacked:      A switch to stack the bars. (optional)
    :param relative:     A switch to show relative portions with stacked bars.
                         (optional)
    :param legend:       A switch to control the visibility of the legend.
                         (optional)
    :param xlabel:       The label for the X axis. (optional)
    :param ylabel:       The label for the Y axis. (optional)
    :param title:        The title of the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pad:          Padding around the figure. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """

    all_columns = [value_column, key_column, label_column, color_column]
    columns = set(c for c in all_columns if c)
    data = data.loc[:, columns].dropna()
    if keys is None:
        keys = data[key_column].drop_duplicates().sort_values().values
    groups = {k: data.loc[data[key_column] == k, :] for k in keys}
    first_group = groups[keys[0]]
    first_labels = first_group[label_column] if label_column else first_group.index
    gs = len(keys)
    gd = gs + 0.5
    if stacked:
        pos = list(np.arange(0, len(first_group)))
        if relative:
            label_scale = 100.0 / sum(g[value_column].values for g in groups.values())
        else:
            label_scale = [1.0] * len(first_labels)
    else:
        pos = {k: list(np.arange(i, i + len(first_group) * gd, gd))
               for i, k in enumerate(keys)}

    if color_column:
        color_values = data[color_column]
        if pd_types.is_numeric_dtype(color_values.dtype):
            color_map = plt_cm.get_cmap(cmap)
            norm = plt_colors.Normalize(vmin=color_values.min(), vmax=color_values.max())

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)

    legend_handles = []

    last_key = None
    for k, c in zip(keys, _build_key_colors(keys, color)):
        g = groups[k]

        if stacked:
            p = pos
            if last_key:
                bars = ax.bar(p, g[value_column].values * label_scale, color=c,
                              bottom=groups[last_key][value_column].values * label_scale)
            else:
                bars = ax.bar(p, g[value_column].values * label_scale, color=c)
            last_key = k
        else:
            bars = ax.bar(pos[k], g[value_column].values, color=c, width=1)

        if color_column:
            colors = g[color_column]
            if pd_types.is_numeric_dtype(colors.dtype):
                for b, cv in zip(bars, colors):
                    b.set_color(color_map(norm(cv)))
            else:
                for b, c in zip(bars, colors):
                    b.set_color(c)
        else:
            legend_handles.append(mlines.Line2D(
                [], [], color=c, linewidth=8, label=k))

    def group_labels_unique(gl):
        ls = gl[0]
        for ls2 in gl[1:]:
            if ls != ls2:
                return False
        return True

    if stacked:
        ax.set_xticks(pos)
        ax.set_xticklabels(first_labels)
    else:
        if label_column:
            group_labels = [tuple(groups[k][label_column]) for k in keys]
            if group_labels_unique(group_labels):
                pos = list(np.arange((gs - 1) * 0.5, (gs - 1) * 0.5 + gd * len(first_group), gd))
                ax.set_xticks(pos)
                ax.set_xticklabels(first_labels)
            else:
                ax.set_xticks(list(chain(*(pos[k] for k in keys))))
                ax.set_xticklabels(list(chain(*(groups[k][label_column] for k in keys))))
        else:
            ax.set_xticks(list(chain(*(pos[k] for k in keys))))
            ax.set_xticklabels(list(chain(*(groups[k].index for k in keys))))

    ax.set_xlabel(_col_label(xlabel, label_column))
    if stacked and relative:
        ax.set_ylabel(_col_label(ylabel, value_column) + ' (%)')
    else:
        ax.set_ylabel(_col_label(ylabel, value_column))
    if legend and legend_handles:
        ax.legend(handles=legend_handles)

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def hist(data: Union[pd.DataFrame, pd.Series],
         column=None, key_column=None,
         bins=35, ticks=None, xmin=None, xmax=None, ylog=False,
         color=None, cumulative=False, stacked=False,
         xlabel=None, ylabel=None, title=None, legend=True,
         figsize=(10, 4), pad=1, pos=(0, 0), rowspan=1, colspan=1,
         file_name=None, file_dpi=300):
    """
    Display a histogram for the values of one column in a DataFrame
    or a Series.
    If using a DataFrame, optionally group the values by another key column.

    :param data:       A Pandas DataFrame or Series.
    :param column:     The column to build the histogram of.
    :param key_column: The column to group the values by. (optional)
    :param bins:       The bins of the histogram (int or sequence or str).
                       (optional)
                       See argument `bins`  of `matplotlib.axes.Axes.hist()`
                       for more details.
    :param ticks:      A sequence of tick positions on the X axis. (optional)
    :param xmin:       The lower limit for displayed values (inclusive).
                       (optional)
    :param xmax:       The upper limit for displayed values (exclusive).
                       (optional)
    :param ylog:       A switch to use a logarithmic scale on the Y axis
                       (optional)
    :param color:      A color for all bars or a list with one color
                       per key if `key_column` is used. (optional)
    :param cumulative: A switch to activate cumulative summing. (optional)
    :param stacked:    A switch to stack bars if `key_column` is used.
                       (optional)
    :param xlabel:     The label for the X axis. (optional)
    :param ylabel:     The label for the Y axis. (optional)
    :param title:      The title of the plot. (optional)
    :param legend:     A switch to control the visibility of the legend.
                       (optional)
    :param figsize:    The figure size in inches. (optional)
    :param pad:        Padding around the figure. (optional)
    :param pos:        The position in the grid of a multiplot. (optional)
    :param rowspan:    The number of rows to span in the grid
                       of a multiplot. (optional)
    :param colspan:    The number of columns to span in the grid
                       of a multiplot. (optional)
    :param file_name:  A path to a file to save the plot in. (optional)
    :param file_dpi:   A resolution to render the saved plot. (optional)
    """

    def prep_values(s):
        s = s.dropna()
        if xmin is not None:
            s = s.loc[s >= xmin]
        if xmax is not None:
            s = s.loc[s <= xmax]
        return s.values

    if isinstance(data, pd.DataFrame):
        # data is a DataFrame
        if key_column:
            grouped = data.groupby(key_column)
            labels = grouped.groups.keys()
            x = [prep_values(grouped.get_group(g)[column]) for g in labels]
        else:
            labels = None
            x = prep_values(data[column])
    else:
        # assume data is a Series
        labels = None
        x = prep_values(data)

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)

    if labels:
        if isinstance(color, str):
            color = list(repeat(color, len(labels)))
        elif isinstance(color, Mapping):
            color = [color.get(l) or next(plt.gca()._get_lines.prop_cycler)['color']
                     for l in labels]
        elif isinstance(color, Iterable):
            color = list(islice(cycle(color), len(labels)))

    ax.hist(x, label=labels, bins=bins, cumulative=cumulative,
            stacked=stacked, color=color)
    ax.set_xlim(left=xmin, right=xmax)
    if ticks is not None:
        ax.set_xticks(ticks)
    if ylog:
        ax.set_yscale('log', nonposy='clip')
    ax.set_xlabel(_col_label(xlabel, column))
    ax.set_ylabel(_col_label(ylabel, 'count'))
    if legend and key_column:
        ax.legend()

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def hist2d(data: pd.DataFrame, xcolumn, ycolumn,
           xmin=None, xmax=None, ymin=None, ymax=None,
           bins=20, xticks=None, yticks=None,
           cmap='Blues', colorbar=True,
           xlabel=None, ylabel=None, title=None,
           figsize=(7.5, 6), pad=1, pos=(0, 0), rowspan=1, colspan=1,
           file_name=None, file_dpi=300):
    """
    Displays a 2-dimensional histogram (heatmap).

    :param data:      A Pandas DataFrame.
    :param xcolumn:   The column for the horizontal dimension.
    :param ycolumn:   The column for the vertical dimension.
    :param xmin:      The lower limit for displayed values
                      in the horizontal dimension (inclusive). (optional)
    :param xmax:      The upper limit for displayed values
                      in the horizontal dimension (exclusive). (optional)
    :param ymin:      The lower limit for displayed values
                      in the vertical dimension (inclusive). (optional)
    :param ymax:      The upper limit for displayed values
                      in the vertical dimension (exclusive). (optional)
    :param bins:      None or int or [int, int] or array_like or [array, array].
                      (optional)
                      See `matplotlib.pyplot.hist2d()` for more info.
    :param xticks:    A sequence of tick positions on the X axis. (optional)
    :param yticks:    A sequence of tick positions on the Y axis. (optional)
    :param cmap:      A Matplotlib Colormap or the name of a color map.
                      (optional)
                      See `matplotlib.pyplot.hist2d()` for more info.
    :param colorbar:  A switch to control if a colorbar is shown. (optional)
    :param xlabel:    A label for the X axis. (optional)
    :param ylabel:    A label for Y axis. (optional)
    :param title:     A title for the plot. (optional)
    :param figsize:   The figure size in inches. (optional)
    :param pad:       Padding around the figure. (optional)
    :param pos:       The position in the grid of a multiplot. (optional)
    :param rowspan:   The number of rows to span in the grid
                      of a multiplot. (optional)
    :param colspan:   The number of columns to span in the grid
                      of a multiplot. (optional)
    :param file_name: A path to a file to save the plot in. (optional)
    :param file_dpi:  A resolution to render the saved plot. (optional)
    """

    data = data.loc[:, [xcolumn, ycolumn]].dropna()

    if xmin is not None:
        data = data.loc[data[xcolumn] >= xmin]
    if xmax is not None:
        data = data.loc[data[xcolumn] < xmax]
    if ymin is not None:
        data = data.loc[data[ycolumn] >= ymin]
    if ymax is not None:
        data = data.loc[data[ycolumn] < ymax]
    x = data.loc[:, xcolumn]
    y = data.loc[:, ycolumn]

    if x.empty or y.empty:
        return

    xmin = xmin if xmin is not None else x.min()
    xmax = xmax if xmax is not None else x.max()
    ymin = ymin if ymin is not None else y.min()
    ymax = ymax if ymax is not None else y.max()
    r = [[xmin, xmax], [ymin, ymax]]

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    (*_, image) = ax.hist2d(x, y, cmap=cmap, range=r, bins=bins, cmin=1)
    if xticks is not None:
        ax.set_xticks(xticks)
    if yticks is not None:
        ax.set_yticks(yticks)
    ax.set_xlabel(_col_label(xlabel, xcolumn))
    ax.set_ylabel(_col_label(ylabel, ycolumn))
    if colorbar:
        divider = axg1.make_axes_locatable(ax)
        cb_ax = divider.append_axes('right', '5%', pad='5%')
        plt.colorbar(image, cax=cb_ax)

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def scatter(data: pd.DataFrame, xcolumn, ycolumn,
            size_column=None, color_column=None,
            xmin=None, xmax=None, ymin=None, ymax=None,
            xticks=None, yticks=None,
            size=1, color=None, cmap='rainbow', colorbar=True,
            xlabel=None, ylabel=None, title=None,
            figsize=(9.8, 8), pad=1, pos=(0, 0), rowspan=1, colspan=1,
            file_name=None, file_dpi=300):
    """
    Display a 2-dimensional scatter plot.

    :param data:         A Pandas DataFrame
    :param xcolumn:      The column for the horizontal dimension.
    :param ycolumn:      The column for the vertical dimension.
    :param size_column:  A column for the marker size. (optional)
    :param color_column: A column with values for the marker color. (optional)
    :param xmin:         The lower limit for displayed values
                         in the horizontal dimension. (optional)
    :param xmax:         The upper limit for displayed values
                         in the horizontal dimension. (optional)
    :param ymin:         The lower limit for displayed values
                         in the vertical dimension. (optional)
    :param ymax:         The upper limit for displayed values
                         in the vertical dimension. (optional)
    :param xticks:       A sequence of tick positions on the X axis.
                         (optional)
    :param yticks:       A sequence of tick positions on the Y axis.
                         (optional)
    :param size:         A factor to the marker size. (optional)
    :param color:        A color for the markers. (optional)
                         Gets overridden by `color_column`.
    :param cmap:         A Matplotlib Colormap or the name of a color map.
                         Is used in combination with `color_column`. (optional)
                         See `matplotlib.pyplot.scatter()` for more info.
    :param colorbar:     A switch to control if a colorbar is shown. (optional)
    :param xlabel:       A label for the X axis. (optional)
    :param ylabel:       A label for Y axis. (optional)
    :param title:        A title for the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pad:          Padding around the figure. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    columns = list(set(c for c in [xcolumn, ycolumn, size_column, color_column]
                       if c and c in data.columns))
    data = data.loc[:, columns].dropna()

    x = data[xcolumn]
    y = data[ycolumn]

    s = (data[size_column] if size_column else 20) * size
    c = color
    if color_column:
        c = data[color_column]
        if not pd_types.is_numeric_dtype(c.dtype):
            cmap = None
            colorbar = False

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    marker = ax.scatter(x, y, s=s, c=c, marker='o', cmap=cmap)
    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)
    if xticks is not None:
        ax.set_xticks(xticks)
    if yticks is not None:
        ax.set_yticks(yticks)
    ax.set_xlabel(_col_label(xlabel, xcolumn))
    ax.set_ylabel(_col_label(ylabel, ycolumn))
    if color_column and colorbar:
        divider = axg1.make_axes_locatable(ax)
        cb_ax = divider.append_axes('right', '5%', pad='5%')
        plt.colorbar(marker, cax=cb_ax)

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def scatter_map(data: pd.DataFrame,
                longitude_column='longitude', latitude_column='latitude',
                region=None, autofit=False,
                projection='merc',
                map_resolution='i', grid=(1, 2),
                map_style=None, map_style_attributes=None,
                size_column=None, size=1, size_mode=None,
                color_column=None, color='blue', cmap='YlGnBu', colorbar=True,
                title=None,
                figsize=(10, 10), pad=1, pos=(0, 0), rowspan=1, colspan=1,
                file_name=None, file_dpi=300):
    """
    Displays a scatter plot on a geographical map.

    :param data:         A Pandas DataFrame.
    :param longitude_column:
                         The column with the longitudes. (optional)
    :param latitude_column:
                         The column with the latitudes. (optional)
    :param region:       The geographic region to plot. (optional)
                         A iterable with four elements:
                         lower left corner latitude,
                         lower left corner longitude,
                         upper right corner latitude,
                         and upper right corner longitude.
    :param autofit:      A switch to automatically zoom to a region,
                         showing all markers. (optional)
    :param grid:         A pair of distances for grid lines (lat, lon).
                         (optional)
    :param projection:   The named projection of the map.
                         See https://matplotlib.org/basemap/users/mapsetup.html
    :param map_style:    The name of a style. (optional)
    :param map_style_attributes:
                         A dict with style attributes. (optional)
    :param map_resolution:
                         The resolution of geographical and political features
                         on the map: crude `c`, low `l`, intermediate `i`,
                         high `h`, or full `f`. (optional)
    :param size_column:  A column with marker sizes. (optional)
    :param size:         A factor to the marker size. (optional)
    :param size_mode:    The mode for applying the size: `area` or `radius`.
                         (optional)
    :param color_column: A column with values for the marker color. (optional)
    :param color:        A color for the markers. (optional)
                         Gets overridden by `color_column`.
    :param cmap:         A Matplotlib Colormap or the name of a color map.
                         Is used in combination with `color_column`. (optional)
                         See `matplotlib.pyplot.scatter()` for more info.
    :param colorbar:     A switch to control if a colorbar is shown. (optional)
    :param title:        A title for the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pad:          Padding around the figure. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """

    from .basemap import base_map, lat_lon_region

    columns = list(set(c for c in [longitude_column, latitude_column,
                                   size_column, color_column]
                       if c and c in data.columns))
    data = data.loc[:, columns].dropna()

    lon = data.loc[:, longitude_column]
    lat = data.loc[:, latitude_column]

    s = (data.loc[:, size_column].values if size_column else 1) * size
    if size_mode == 'radius':
        s = np.power(s, 2.0) * pi
    if size_mode == 'area':
        pass

    c = color
    if color_column:
        c = data[color_column]
        if not pd_types.is_numeric_dtype(c.dtype):
            cmap = None
            colorbar = False

    if autofit or region is None:
        region = [lat.min(), lon.min(), lat.max(), lon.max()]
        lat_margin = abs(region[2] - region[0]) * 0.15
        lon_margin = abs(region[3] - region[1]) * 0.15
        region[0] -= lat_margin
        region[1] -= lon_margin
        region[2] += lat_margin
        region[3] += lon_margin
        if region[2] - region[0] > 180:
            region[0], region[2] = region[2], region[0]

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    m = base_map(lat_lon_region(*region), projection=projection,
                 resolution=map_resolution, grid=grid,
                 style_name=map_style, style_attributes=map_style_attributes,
                 ax=ax)
    marker = m.scatter(list(lon.values), list(lat.values), latlon=True,
              s=s, c=c, marker='o', cmap=cmap, zorder=10)
    if color_column and colorbar:
        divider = axg1.make_axes_locatable(ax)
        cb_ax = divider.append_axes('right', '5%', pad='5%')
        plt.colorbar(marker, cax=cb_ax)

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def _moving_average(indices: np.ndarray, values: np.ndarray, window):
    if len(indices) != len(values):
        raise Exception('indices and values do not have the same size')

    weights = np.repeat(1.0, window) / window  # kernel
    means = np.convolve(values, weights, 'valid')

    start = floor(window / 2)
    end = len(indices) - ceil(window / 2) + 1
    sub_indices = indices[start:end]

    return sub_indices, means


def _interpolate(indices: np.ndarray, values: np.ndarray, step, kind):
    f = interpolate.interp1d(indices, values, kind=kind)
    x = np.arange(indices[0], indices[-1], step)
    return x, f(x)


def line(data: Union[pd.DataFrame, pd.Series],
         column=None, xcolumn=None,
         color=None, linewidth=2,
         avg_window=None, interpolation_step=None, interpolation_kind='quadratic',
         xmin=None, xmax=None, ymin=None, ymax=None,
         xticks=None, yticks=None,
         xlabel=None, ylabel=None, title=None,
         figsize=(10, 5), pad=1, pos=(0, 0), rowspan=1, colspan=1,
         file_name=None, file_dpi=300):
    """
    Display a line from values in one column of a DataFrame or a Series.

    If `data` is a Series, the index will be used for the horizontal dimension.

    :param data:         A Pandas DataFrame or a Series.
    :param column:       The column with the values to display as a line.
                         The values are used as vertical dimension.
    :param xcolumn:      A column with values for the horizontal dimension.
                         (optional)
    :param color:        A color for the line. (optional)
    :param linewidth:    The width of the line.
    :param avg_window:   The size of a window for smoothing the values
                         with a sliding average. (optional)
    :param interpolate_step:
                         A step size in the horizontal dimension,
                         for smoothing the line with interpolation.
    :param interpolate_kind:
                         The kind of interpolation to use:
                         `quadratic` or `cubic`. (optional)
                         Has an effect only if `interpolation_step` is used.
    :param xmin:         The lower limit for displayed values
                         in the horizontal dimension. (optional)
    :param xmax:         The upper limit for displayed values
                         in the horizontal dimension. (optional)
    :param ymin:         The lower limit for displayed values
                         in the vertical dimension. (optional)
    :param ymax:         The upper limit for displayed values
                         in the vertical dimension. (optional)
    :param xticks:       A sequence of tick positions on the X axis. (optional)
    :param yticks:       A sequence of tick positions on the Y axis. (optional)
    :param xlabel:       A label for the X axis. (optional)
    :param ylabel:       A label for Y axis. (optional)
    :param title:        A title for the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pad:          Padding around the figure. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)

    def plot_line(d, c=None):
        if isinstance(d, pd.DataFrame):
            x = d[xcolumn].values if xcolumn else d.index.values
            y = d[column].values
        else:
            x = d.index.values
            y = d.values
        if avg_window:
            x, y = _moving_average(x, y, avg_window)
        if interpolation_step:
            x, y = _interpolate(x, y, interpolation_step, interpolation_kind)
        ax.plot(x, y, color=c, linewidth=linewidth)

    if isinstance(data, pd.DataFrame):
        # data is DataFrame
        columns = set()
        columns.add(column)
        if xcolumn:
            columns.add(xcolumn)
        data = data.loc[:, columns].dropna()
    else:
        # assume data is Series
        pass

    plot_line(data, c=color)

    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)
    if xticks is not None:
        ax.set_xticks(xticks)
    if xticks is not None:
        ax.set_yticks(yticks)
    ax.set_xlabel(_col_label(xlabel, xcolumn))
    ax.set_ylabel(_col_label(ylabel, column))

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def lines(data: pd.DataFrame, column, xcolumn=None,
          key_column=None, min_n=None, label_column=None,
          color=None, linewidth=2,
          avg_window=None, interpolation_step=None, interpolation_kind='quadratic',
          xmin=None, xmax=None, ymin=None, ymax=None,
          xticks=None, yticks=None,
          xlabel=None, ylabel=None, title=None,
          figsize=(10, 5), pad=1, pos=(0, 0), rowspan=1, colspan=1,
          file_name=None, file_dpi=300):
    """
    Display line(s) from values in one column of a DataFrame.

    :param data:         A Pandas DataFrame.
    :param column:       The column with the values to display as a line.
                         The values are used as vertical dimension.
    :param xcolumn:      A column with values for the horizontal dimension.
                         (optional)
    :param key_column:   A column for grouping without labels.
    :param label_column: A column for grouping with labels.
    :param min_n:        The minimum number of values, required in a group
                         for it to get drawn by a line. (optional)
    :param color:        A color for the line(s). (optional)
    :param linewidth:    The width of the line(s).
    :param avg_window:   The size of a window for smoothing the values
                         with a sliding average. (optional)
    :param interpolate_step:
                         A step size in the horizontal dimension,
                         for smoothing the line with interpolation.
    :param interpolate_kind:
                         The kind of interpolation to use:
                         `quadratic` or `cubic`. (optional)
                         Has an effect only if `interpolation_step` is used.
    :param xmin:         The lower limit for displayed values
                         in the horizontal dimension. (optional)
    :param xmax:         The upper limit for displayed values
                         in the horizontal dimension. (optional)
    :param ymin:         The lower limit for displayed values
                         in the vertical dimension. (optional)
    :param ymax:         The upper limit for displayed values
                         in the vertical dimension. (optional)
    :param xticks:       A sequence of tick positions on the X axis. (optional)
    :param yticks:       A sequence of tick positions on the Y axis. (optional)
    :param xlabel:       A label for the X axis. (optional)
    :param ylabel:       A label for Y axis. (optional)
    :param title:        A title for the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pad:          Padding around the figure. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    legend_handles = []

    columns = set()
    columns.add(column)
    if xcolumn:
        columns.add(xcolumn)

    if label_column and not key_column:
        key_column = label_column

    def plot_line(d, c=None, l=None):
        if min_n and len(d) < min_n:
            return
        x = d.loc[:, xcolumn].values if xcolumn else d.index.values
        y = d.loc[:, column].values
        if avg_window:
            x, y = _moving_average(x, y, avg_window)
        if interpolation_step:
            x, y = _interpolate(x, y, interpolation_step, interpolation_kind)
        ax.plot(x, y, label=l, color=c, linewidth=linewidth)

    if key_column:
        columns.add(key_column)
        if label_column:
            columns.add(label_column)
            data = data.loc[:, columns].dropna()
            lgrouped = data.groupby(label_column)
            keys = sorted(lgrouped.groups.keys())

            for label, c in zip(keys, _build_key_colors(keys, color)):
                ldata = lgrouped.get_group(label)
                legend_handles.append(mlines.Line2D(
                    [], [], color=c, linewidth=linewidth, label=label))
                grouped = ldata.groupby(key_column)
                for k in grouped.groups.keys():
                    plot_line(grouped.get_group(k), c=c, l=label)
        else:
            data = data.loc[:, columns].dropna()
            grouped = data.groupby(key_column)
            keys = grouped.groups.keys()

            for k, c in zip(keys, _build_key_colors(keys, color)):
                    plot_line(grouped.get_group(k), c=c)
    else:
        data = data.loc[:, columns].dropna()
        plot_line(data, c=color)

    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)
    if xticks is not None:
        ax.set_xticks(xticks)
    if xticks is not None:
        ax.set_yticks(yticks)
    ax.set_xlabel(_col_label(xlabel, xcolumn))
    ax.set_ylabel(_col_label(ylabel, column))
    if legend_handles:
        ax.legend(handles=legend_handles)

    _finish_figure(
        fig=fig, ax=ax, title=title, pad=pad,
        file_name=file_name, file_dpi=file_dpi)


def scatter_matrix(data: pd.DataFrame, columns=None,
                   mins=None, maxs=None, ticks=None,
                   key_column=None, color=None,
                   subplot_size=2, pad=1, w_pad=1.0, h_pad=1.75,
                   file_name=None, file_dpi=300):
    """
    Plots a matrix of scatter plots and histograms for a number of columns
    from a Pandas DataFrame.

    Warning: This function cannot be used between `begin()` and `end()` as part
    of another multiplot.

    :param data:         A Pandas DataFrame.
    :param columns:      The columns to include into the matrix. (optional)
    :param key_column:   A column used to build groups. (optional)
    :param color:        A list or dict with colors for the groups. (optional)
    :param mins:         A dict, mapping column names to minimal values.
                         (optional)
    :param maxs:         A dict, mapping column names to maximal values.
                         (optional)
    :param ticks:        A dict, mapping column names to ticks. (optional)
    :param subplot_size: The edge length for the subplots. (optional)
    :param pad:          Padding around the figure. (optional)
    :param w_pad:        Horizontal space between subplots. (optional)
    :param h_pad:        Vertical space between subplots. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    if _in_multiplot():
        raise Exception("There is already an open figure. "
                        "You must use this function outside of a begin()-end()-block?")
    if columns is None:
        columns = data.columns.values
    cn = len(columns)

    if key_column:
        grouped = data.groupby(key_column)
        labels = grouped.groups.keys()
        if isinstance(color, Mapping):
            color = [color.get(l) or next(plt.gca()._get_lines.prop_cycler)['color']
                     for l in labels]
        elif isinstance(color, Iterable):
            color = list(islice(cycle(color), len(labels)))
        else:
            color = [next(plt.gca()._get_lines.prop_cycler)['color']
                     for l in labels]
        _ = plt.close()
        label_colors = dict(zip(labels, color))
        data_color = data[key_column].map(label_colors)
        data = data.assign(scatter_matrix_color=data_color)
    else:
        label_colors = color

    begin(grid=(cn, cn), figsize=(cn * subplot_size, cn * subplot_size))
    try:
        for iy, cy in enumerate(columns):
            ymin = mins.get(cy) if mins is not None else None
            ymax = maxs.get(cy) if maxs is not None else None
            yticks = ticks.get(cy) if ticks is not None else None
            for ix, cx in enumerate(columns):
                xmin = mins.get(cx) if mins is not None else None
                xmax = maxs.get(cx) if maxs is not None else None
                xticks = ticks.get(cx) if ticks is not None else None
                ylabel = cy if ix == 0 else ""
                xlabel = cx if iy == cn - 1 else ""
                if cy != cx:
                    scatter(data, xcolumn=cx, ycolumn=cy,
                            color_column=('scatter_matrix_color' if key_column else None),
                            color=(None if key_column else color),
                            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                            xticks=xticks, yticks=yticks,
                            xlabel=xlabel, ylabel=ylabel,
                            pos=(iy, ix))
                else:
                    hist(data, cx, key_column=key_column, color=label_colors,
                         stacked=True, legend=False,
                         xmin=xmin, xmax=xmax, ticks=xticks,
                         xlabel=xlabel, ylabel=ylabel,
                         pos=(iy, ix))
    finally:
        end(pad=pad, h_pad=h_pad, w_pad=w_pad,
            file_name=file_name, file_dpi=file_dpi)


def hist2d_matrix(data: pd.DataFrame, columns=None,
                  mins=None, maxs=None, bins=None, ticks=None,
                  subplot_size=2, pad=1, w_pad=1.0, h_pad=1.75, cmap='Blues',
                  file_name=None, file_dpi=300):
    """
    Plots a matrix of 2D histogram plots and histograms for a number of columns
    from a Pandas DataFrame.

    Warning: This function cannot be used between `begin()` and `end()` as part
    of another multiplot.

    :param data:         A Pandas DataFrame.
    :param columns:      The columns to include into the matrix. (optional)
    :param mins:         A dict, mapping column names to minimal values.
                         (optional)
    :param maxs:         A dict, mapping column names to maximal values.
                         (optional)
    :param bins:         A dict, mapping column names to bins. (optional)
    :param ticks:        A dict, mapping column names to ticks. (optional)
    :param subplot_size: The edge length for the subplots. (optional)
    :param pad:          Padding around the figure. (optional)
    :param w_pad:        Horizontal space between subplots. (optional)
    :param h_pad:        Vertical space between subplots. (optional)
    :param cmap:         The color map to use. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    if _in_multiplot():
        raise Exception("There is already an open figure. "
                        "You must use this function outside of a begin()-end()-block?")
    if columns is None:
        columns = data.columns.values
    cn = len(columns)

    begin(grid=(cn, cn), figsize=(cn * subplot_size, cn * subplot_size))
    try:
        for iy, cy in enumerate(columns):
            ymin = mins.get(cy) if mins is not None else None
            ymax = maxs.get(cy) if maxs is not None else None
            ybins = bins.get(cy) if bins is not None else None
            yticks = ticks.get(cy) if ticks is not None else None
            for ix, cx in enumerate(columns):
                xmin = mins.get(cx) if mins is not None else None
                xmax = maxs.get(cx) if maxs is not None else None
                xbins = bins.get(cx) if bins is not None else None
                xticks = ticks.get(cx) if ticks is not None else None
                ylabel = cy if ix == 0 else ""
                xlabel = cx if iy == cn - 1 else ""
                if cy != cx:
                    hist2d(data, xcolumn=cx, ycolumn=cy, cmap=cmap,
                           bins=(xbins or 20, ybins or 20),
                           xticks=xticks, yticks=yticks,
                           xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                           xlabel=xlabel, ylabel=ylabel, colorbar=False,
                           pos=(iy, ix))
                else:
                    hist(data, cx,
                         xmin=xmin, xmax=xmax,
                         bins=(xbins or 35), ticks=xticks,
                         xlabel=xlabel, ylabel=ylabel,
                         pos=(iy, ix))
    finally:
        end(pad=pad, h_pad=h_pad, w_pad=w_pad,
            file_name=file_name, file_dpi=file_dpi)
