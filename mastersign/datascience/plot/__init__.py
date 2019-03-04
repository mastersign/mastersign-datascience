# -*- coding: utf-8 -*-

"""
This module contains functionality to comfortably create plots.
"""

from math import floor, ceil, pi
from itertools import islice, chain
from warnings import warn
import pandas as pd
import numpy as np
from scipy import interpolate
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from configparser import ConfigParser
from IPython.display import HTML, display
from tabulate import tabulate
from .basemap import base_map, lat_lon_region

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


current_figure = None
current_grid = (1, 1)
allow_tight_layout = True


def begin(figsize=(10, 5), grid=(1, 1)):
    """
    Begins a figure with multiple subplots.

    :param figsize: A tuple with the figure size in inches (width, height).
                    (optional)
    :param grid:    The grid size to place the subplots in (rows, columns).
                    (optional)
    """
    global current_figure, current_grid, allow_tight_layout
    if current_figure is not None:
        warn("There is already an open figure. Did you use end()?")
    current_figure = plt.figure(figsize=figsize)
    current_grid = grid
    allow_tight_layout = True


def end(pad=None, w_pad=None, h_pad=None,
        file_name=None, file_dpi=300):
    """
    Finalizes a figure with multiple subplots.

    :param pad:       Padding around the figure. (optional)
    :param w_pad:     Horizontal space between subplots. (optional)
                      See `matplotlib.pyplot.tight_layout()`.
    :param h_pad:     Vertical space between subplots. (optional)
                      See `matplotlib.pyplot.tight_layout()`.
    :param tight_layout:
                      A switch to call `matplotlib.pyplot.tight_layout()`.
    :param file_name: A path to a file to save the plot in. (optional)
    :param file_dpi:  A resolution to render the saved plot. (optional)
    """
    global current_figure, allow_tight_layout
    if current_figure is None:
        raise Exception("No current figure. Did you use begin()?")
    if allow_tight_layout:
        if pad is not None:
            plt.tight_layout(pad=pad, h_pad=h_pad, w_pad=w_pad)
        elif h_pad is not None or w_pad is not None:
            plt.tight_layout(h_pad=h_pad, w_pad=w_pad)
    elif pad is not None or h_pad is not None or w_pad is not None:
        # one reason can be a plot with colorbar, e.g. hist2d
        warn("Padding can not be set because tight layout is suppressed.")

    if file_name:
        current_figure.savefig(file_name, dpi=file_dpi)
    plt.show()
    current_figure = None


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


def _suppress_tight_layout():
    global allow_tight_layout
    allow_tight_layout = False


def pie(data: pd.DataFrame, column, label_column=None, sort_by=None,
        title=None, pct=True,
        figsize=(4, 4), pos=(0, 0), rowspan=1, colspan=1,
        file_name=None, file_dpi=300):
    """
    Display a pie chart with values from a column.

    :param data:         A Pandas DataFrame.
    :param column:       The column to use.
    :param label_column: A column to use for the labels.
                         By default the index is used.
    :param sort_by:      The sort mode `None`, `"label"`, or `"value"`
    :param title:        The title of the plot.
    :param pct:          A switch to display percentages.
    :param figsize:      The figure size in inches. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """

    if sort_by:
        data = data.sort_values(by=label_column) \
            if label_column else data.sort_index()
    if sort_by == 'value':
        data.sort_values(by=column, ascending=False, inplace=True)

    x = data.loc[:, column]
    labels = data.loc[:, label_column] if label_column else data.index

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    if pct:
        ax.pie(x, labels=labels,
                startangle=180, counterclock=False, autopct='%1.1f%%')
    else:
        ax.pie(x, labels=labels,
                startangle=180, counterclock=False)
    ax.axis('equal')
    if not _in_multiplot() and file_name:
        fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax.set_title(title)
    if not _in_multiplot():
        plt.show()


def pie_groups(data: pd.DataFrame, column, sort_by=None,
               title=None, pct=True,
               figsize=(4, 4), pos=(0, 0), rowspan=1, colspan=1,
               file_name=None, file_dpi=300):
    """
    Display a pie chart by counting rows according to a column value.

    :param data:      A Pandas DataFrame.
    :param column:    The column to use for grouping.
    :param sort_by:   The sort mode `None`, `"label"`, or `"value"`
    :param title:     The title of the plot.
    :param pct:       A switch to display percentages.
    :param figsize:   The figure size in inches. (optional)
    :param pos:       The position in the grid of a multiplot. (optional)
    :param rowspan:   The number of rows to span in the grid
                      of a multiplot. (optional)
    :param colspan:   The number of columns to span in the grid
                      of a multiplot. (optional)
    :param file_name: A path to a file to save the plot in. (optional)
    :param file_dpi:  A resolution to render the saved plot. (optional)
    """

    groups = data.groupby(column, sort=False).size()
    group_data = pd.DataFrame({'value': groups}, index=groups.index)
    pie(group_data, 'value', sort_by=sort_by,
        title=title, pct=pct,
        figsize=figsize, pos=pos, rowspan=rowspan, colspan=colspan,
        file_name=file_name, file_dpi=file_dpi)


def bar(data: pd.DataFrame, value_column, label_column=None,
        xlabel=None, ylabel=None, title=None,
        figsize=(10, 4), pos=(0, 0), rowspan=1, colspan=1,
        file_name=None, file_dpi=300):
    """
    Display a bar chart from one two columns.

    :param data:         A Pandas DataFrame.
    :param value_column: The column with the values for the bars height.
    :param label_column: The column with the labels for the bars. (optional)
    :param xlabel:       The label for the X axis. (optional)
    :param ylabel:       The label for the Y axis. (optional)
    :param title:        The title of the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    if label_column:
        data = data.loc[:, [label_column, value_column]].dropna()
        labels = data.loc[:, label_column]
        values = data.loc[:, value_column]
    else:
        values = data.loc[:, value_column].dropna()
        labels = values.index

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    ax.bar(labels, values)
    ax.set_xlabel(_col_label(xlabel, label_column))
    ax.set_ylabel(_col_label(ylabel, value_column))
    if not _in_multiplot() and file_name:
        fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax.set_title(title)
    if not _in_multiplot():
        plt.show()



def hist(data: pd.DataFrame, column, key_column=None,
         bins=35, ticks=None, xmin=None, xmax=None, ylog=False,
         xlabel=None, ylabel=None, title=None,
         figsize=(10, 4), pos=(0, 0), rowspan=1, colspan=1,
         file_name=None, file_dpi=300):
    """
    Display a histogram for the values of one column.
    Optionally group the values by another key column.

    :param data:       A Pandas DataFrame.
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
    :param xlabel:     The label for the X axis. (optional)
    :param ylabel:     The label for the Y axis. (optional)
    :param title:      The title of the plot. (optional)
    :param figsize:    The figure size in inches. (optional)
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

    if key_column:
        grouped = data.groupby(key_column)
        labels = grouped.groups.keys()
        x = [prep_values(grouped.get_group(g).loc[:, column]) for g in labels]
    else:
        labels = None
        x = prep_values(data.loc[:, column])
    columns = [column]
    if key_column:
        columns.append(key_column)

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    ax.hist(x, label=labels, bins=bins)
    ax.set_xlim(left=xmin, right=xmax)
    if ticks is not None:
        ax.set_xticks(ticks)
    if ylog:
        ax.set_yscale('log', nonposy='clip')
    ax.set_xlabel(_col_label(xlabel, column))
    ax.set_ylabel(_col_label(ylabel, 'count'))
    if key_column:
        ax.legend()
    if not _in_multiplot() and file_name:
        fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax.set_title(title)
    if not _in_multiplot():
        plt.show()


def hist2d(data: pd.DataFrame, xcolumn, ycolumn,
           xmin=None, xmax=None, ymin=None, ymax=None,
           cmap='Blues', bins=20, colorbar=True,
           xlabel=None, ylabel=None, title=None,
           figsize=(7.5, 6), pos=(0, 0), rowspan=1, colspan=1,
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
    :param cmap:      A Matplotlib Colormap or the name of a color map.
                      (optional)
                      See `matplotlib.pyplot.hist2d()` for more info.
    :param bins:      None or int or [int, int] or array_like or [array, array].
                      (optional)
                      See `matplotlib.pyplot.hist2d()` for more info.
    :param colorbar:  A switch to control if a colorbar is shown. (optional)
    :param xlabel:    A label for the X axis. (optional)
    :param ylabel:    A label for Y axis. (optional)
    :param title:     A title for the plot. (optional)
    :param figsize:   The figure size in inches. (optional)
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
    ax.set_xlabel(_col_label(xlabel, xcolumn))
    ax.set_ylabel(_col_label(ylabel, ycolumn))
    if colorbar:
        (cb_ax, cb_kw) = matplotlib.colorbar.make_axes(ax)
        plt.colorbar(image, cax=cb_ax, **cb_kw)
        _suppress_tight_layout()
    if not _in_multiplot() and file_name:
        fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax.set_title(title)
    if not _in_multiplot():
        plt.show()


def scatter(data: pd.DataFrame, xcolumn, ycolumn,
            size_column=None, color_column=None,
            xmin=None, xmax=None, ymin=None, ymax=None,
            size=1, color=None, cmap='rainbow',
            xlabel=None, ylabel=None, title=None,
            figsize=(9.8, 8), pos=(0, 0), rowspan=1, colspan=1,
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
    :param size:         A factor to the marker size. (optional)
    :param color:        A color for the markers. (optional)
                         Gets overridden by `color_column`.
    :param cmap:         A Matplotlib Colormap or the name of a color map.
                         Is used in combination with `color_column`. (optional)
                         See `matplotlib.pyplot.scatter()` for more info.
    :param xlabel:       A label for the X axis. (optional)
    :param ylabel:       A label for Y axis. (optional)
    :param title:        A title for the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    columns = [xcolumn, ycolumn]
    if size_column:
        columns.append(size_column)
    if color_column:
        columns.append(color_column)
    data = data.loc[:, columns].dropna()

    x = data.loc[:, xcolumn]
    y = data.loc[:, ycolumn]

    s = (data.loc[:, size_column] if size_column else 20) * size
    c = data.loc[:, color_column] if color_column else color

    (fig, ax) = _plt(figsize=figsize, pos=pos,
                     rowspan=rowspan, colspan=colspan)
    marker = ax.scatter(x, y, s=s, c=c, marker='o', cmap=cmap)
    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)
    ax.set_xlabel(_col_label(xlabel, xcolumn))
    ax.set_ylabel(_col_label(ylabel, ycolumn))
    if color_column:
        (cb_ax, cb_kw) = matplotlib.colorbar.make_axes(ax)
        plt.colorbar(marker, cax=cb_ax, **cb_kw)
        _suppress_tight_layout()
    if not _in_multiplot() and file_name:
        fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax.set_title(title)
    if not _in_multiplot():
        plt.show()


def scatter_map(data: pd.DataFrame,
                longitude_column='longitude', latitude_column='latitude',
                region=None, autofit=False,
                projection='merc',
                map_resolution='i', grid=(1, 2),
                map_style=None, map_style_attributes=None,
                size_column=None, size=1, size_mode=None,
                color_column=None, color='blue', cmap='YlGnBu',
                title=None,
                figsize=(10, 10), pos=(0, 0), rowspan=1, colspan=1,
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
    :param title:        A title for the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
    :param pos:          The position in the grid of a multiplot. (optional)
    :param rowspan:      The number of rows to span in the grid
                         of a multiplot. (optional)
    :param colspan:      The number of columns to span in the grid
                         of a multiplot. (optional)
    :param file_name:    A path to a file to save the plot in. (optional)
    :param file_dpi:     A resolution to render the saved plot. (optional)
    """
    columns = [longitude_column, latitude_column]
    if size_column:
        columns.append(size_column)
    if color_column:
        columns.append(color_column)

    data = data.loc[:, columns].dropna()
    lon = data.loc[:, longitude_column]
    lat = data.loc[:, latitude_column]
    s = (data.loc[:, size_column].values if size_column else 1) * size
    if size_mode == 'radius':
        s = np.power(s, 2.0) * pi
    if size_mode == 'area':
        pass
    c = data.loc[:, color_column].values if color_column else color

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
    if color_column:
        (cb_ax, cb_kw) = matplotlib.colorbar.make_axes(ax)
        plt.colorbar(marker, cax=cb_ax, **cb_kw)
        _suppress_tight_layout()
    if not _in_multiplot() and file_name:
        fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax.set_title(title)
    if not _in_multiplot():
        plt.show()


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


def lines(data: pd.DataFrame, column, xcolumn = None,
          key_column=None, min_n=None, label_column=None,
          color=None, linewidth=2,
          avg_window=None, interpolation_step=None, interpolation_kind='quadratic',
          xmin=None, xmax=None, ymin=None, ymax=None,
          xlabel=None, ylabel=None, title=None,
          figsize=(10, 5), pos=(0, 0), rowspan=1, colspan=1,
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
    :param xlabel:       A label for the X axis. (optional)
    :param ylabel:       A label for Y axis. (optional)
    :param title:        A title for the plot. (optional)
    :param figsize:      The figure size in inches. (optional)
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
        if label_column and color is None:
            columns.add(label_column)
            data = data.loc[:, columns].dropna()
            lgrouped = data.groupby(label_column)
            for label in sorted(lgrouped.groups.keys()):
                ldata = lgrouped.get_group(label)
                color = next(plt.gca()._get_lines.prop_cycler)['color']
                legend_handles.append(mlines.Line2D(
                    [], [], color=color, linewidth=linewidth, label=label))
                grouped = ldata.groupby(key_column)
                for k in grouped.groups.keys():
                    plot_line(grouped.get_group(k), color, label)
        else:
            data = data.loc[:, columns].dropna()
            grouped = data.groupby(key_column)

            for k in sorted(grouped.groups.keys()):
                plot_line(grouped.get_group(k), color)
    else:
        data = data.loc[:, columns].dropna()
        plot_line(data, color)

    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)
    ax.set_xlabel(_col_label(xlabel, xcolumn))
    ax.set_ylabel(_col_label(ylabel, column))
    if legend_handles:
        ax.legend(handles=legend_handles)
    if not _in_multiplot() and file_name:
        fig.savefig(file_name, dpi=file_dpi)
    if title:
        ax.set_title(title)
    if not _in_multiplot():
        plt.show()


def scatter_matrix(data: pd.DataFrame, columns=None,
                   subplot_size=2,
                   file_name=None, file_dpi=300):
    """
    Plots a matrix of scatter plots and histograms for a number of columns
    from a Pandas DataFrame.

    Warning: This function cannot be used between `begin()` and `end()` as part
    of another multiplot.

    :param data:         A Pandas DataFrame.
    :param columns:      The columns to include into the matrix. (optional)
    :param subplot_size: The edge length for the subplots. (optional)
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

    for iy, cy in enumerate(columns):
        for ix, cx in enumerate(columns):
            ylabel = cy if ix == 0 else ""
            xlabel = cx if iy == cn - 1 else ""
            if cy != cx:
                scatter(data, xcolumn=cx, ycolumn=cy,
                        xlabel=xlabel, ylabel=ylabel,
                        pos=(iy, ix))
            else:
                hist(data, cx,
                     xlabel=xlabel, ylabel=ylabel,
                     pos=(iy, ix))

    end(h_pad=1.75, w_pad=1.0,
        file_name=file_name, file_dpi=file_dpi)


def hist2d_matrix(data: pd.DataFrame, columns=None,
                  subplot_size=2, cmap='Blues',
                  file_name=None, file_dpi=300):
    """
    Plots a matrix of 2D histogram plots and histograms for a number of columns
    from a Pandas DataFrame.

    Warning: This function cannot be used between `begin()` and `end()` as part
    of another multiplot.

    :param data:         A Pandas DataFrame.
    :param columns:      The columns to include into the matrix. (optional)
    :param subplot_size: The edge length for the subplots. (optional)
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

    for iy, cy in enumerate(columns):
        for ix, cx in enumerate(columns):
            ylabel = cy if ix == 0 else ""
            xlabel = cx if iy == cn - 1 else ""
            if cy != cx:
                hist2d(data, xcolumn=cx, ycolumn=cy, cmap=cmap,
                       xlabel=xlabel, ylabel=ylabel, colorbar=False,
                       pos=(iy, ix))
            else:
                hist(data, cx,
                     xlabel=xlabel, ylabel=ylabel,
                     pos=(iy, ix))

    end(h_pad=1.75, w_pad=1.0,
        file_name=file_name, file_dpi=file_dpi)