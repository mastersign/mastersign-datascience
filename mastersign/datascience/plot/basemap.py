# -*- coding: utf-8 -*-

"""
This module contains functionality used to plot on a map.

See e.g. `mastersign.datascience.plot.scatter_map()`.
"""

from typing import Any, Optional, Tuple, Sequence, Iterable, List, Mapping
import numpy as np
from mpl_toolkits.basemap import Basemap

EPSG_WGS84_GIS = 3857  # Pseudo Mercator (Google Maps, OpenStreetView, Bing, ...)
EPSG_WGS84_GPS = 4326  # GPS
EPSG_ETRS89 = 5243     # LCC Germany


def lat_lon_region(lower_left_corner_latitude,
           lower_left_corner_longitude,
           upper_right_corner_latitude,
           upper_right_corner_longitude):
    """
    Converts a geographical region with lower left corner
    and upper right corner into a Basemap compatible structure.

    :param lower_left_corner_latitude:
        The latitude of the lower left corner.
    :param lower_left_corner_longitude:
        The longitude of the lower left corner.
    :param upper_right_corner_latitude:
        The latitude of the lower left corner.
    :param upper_right_corner_longitude:
        The longitude of the lower left corner.

    :return: A dict with the keys ``llcrnrlat``, ``llcrnrlon``,
             ``urcrnrlat``, and ``urcrnrlon``.
    """
    return {
        'llcrnrlat': lower_left_corner_latitude,
        'llcrnrlon': lower_left_corner_longitude,
        'urcrnrlat': upper_right_corner_latitude,
        'urcrnrlon': upper_right_corner_longitude
    }


map_styles = {
    'default': {
        'ocean': '#D0E8FF',
        'continent': '#E0FFC0',
        'coast': '#60A0FF',
        'lake': '#D0E8FF',
        'river': '#60A0FF',
        'border': '#C08080',
        'region': '#E0A0A0',
        'district': '#F0C0C0',
        'grid': '#00000020',
        'coast_width': 0.5,
        'river_width': 0.3,
        'border_width': 0.8,
        'region_width': 0.4,
        'district_width': 0.2,
        'grid_width': 1.0,
        'grid_dashes': [4, 2],
        'draw_coast': True,
        'draw_river': True,
        'draw_border': True,
        'draw_region': True,
        'draw_district': True,
        'draw_grid': True,
        'local_border': False,
    },
    'gray': {
        'ocean': '#E0E0E0',
        'continent': '#FFFFFF',
        'coast': '#C0C0C0',
        'lake': '#D0D0D0',
        'river': '#D0D0D0',
        'border': '#A0A0A0',
        'region': '#C0C0C0',
        'district': '#E0E0E0',
        'grid': '#00000020',
        'coast_width': 0.8,
        'river_width': 0.6,
        'border_width': 1.1,
        'region_width': 0.8,
        'district_width': 0.2,
        'grid_width': 1.0,
        'grid_dashes': [4, 2],
        'draw_coast': True,
        'draw_river': True,
        'draw_border': True,
        'draw_region': True,
        'draw_district': True,
        'draw_grid': True,
        'local_border': False,
    },
}


def _draw_grid(m, dlat=30.0, dlon=60.0, color='#BBBBBB', linewidth=1, dashes=[4,2]):
    m.drawparallels(np.arange(-180.0 + dlat, +180 - dlat, dlat),
                    color=color, linewidth=linewidth, dashes=dashes)
    m.drawmeridians(np.arange(0.0, 360.0, dlon),
                    color=color, linewidth=linewidth, dashes=dashes)


def base_map(region: Mapping[str, float],
             projection: str = 'cyl',
             epsg: Optional[int] = None,
             grid: Tuple[float, float] = (30, 60),
             resolution: str = 'i',
             style_name: Optional[str] = None,
             style_attributes: Optional[Mapping[str, Any]] = None,
             ax = None) -> Basemap:
    """
    Creates a Basemap instance containing continents, coastlines,
    rivers and country borders.

    :param region:
        A Basemap compatible structure defining a rectangular
        geographical region. (See `lat_lon_region()`.)
    :type region: Mapping[str, float]

    :param projection:
        A named projection from Basemap.
        E.g. `cyl`, `robin`, `mill`, `ortho`, `merc`, and a lot more.

        See https://matplotlib.org/basemap/users/mapsetup.html
        for more details.

    :param epsg:
        An EPSG projection code as an alternative to the named
        projection types.
        E.g. `EPSG_WGS84_GIS`, `EPSG_WGS84_GPS`, or `EPSG_ETRS89`.

        See http://spatialreference.org/ref/epsg/ for EPSG codes.

    :type epsg: Optional[int]

    :param lat_0:
        The latitude facing the viewer for orthographic projections.
    :type lat_0: float

    :param lon_0:
        The longitude facing the viewer for orthographic projections.
    :type lon_0: float

    :param grid:
        A tuple with latitude and longitude intervals for drawing a grid.
    :type grid: Tuple[float, float]

    :param resolution:
        The Basemap resolution level: ``c`` (crude), ``l`` (low),
        ``i`` (intermediate), ``h`` (high), or ``f`` (full).
    :type resolution: str

    :param style_name:
        The name of a style in `map_styles`.
    :type style_name: str

    :param style_attributes:
        A dict like structure with overridings for the style.
    :type style_attributes: Optional[Mapping[str, Any]]

    :param ax:
        A mapplotlib Axes object.

    :return:
        The initialized Basemap instance.
    :rtype: mpl_toolkits.basemap.Basemap
    """

    style = map_styles[style_name or 'default']
    if style_attributes:
        style = {**style, **style_attributes}

    m = Basemap(projection=projection, epsg=epsg, resolution=resolution,
                ax=ax, lat_0=0, lon_0=0, **region)
    m.drawmapboundary(fill_color=style['ocean'])
    m.fillcontinents(color=style['continent'], lake_color=style['lake'])
    if style['draw_river']:
        m.drawrivers(color=style['river'], linewidth=style['river_width'])
    if style['draw_coast']:
        m.drawcoastlines(color=style['coast'], linewidth=style['coast_width'])
    if style['draw_border']:
        m.drawcountries(color=style['border'], linewidth=style['border_width'])
    if style['draw_grid']:
        _draw_grid(m, *grid, color=style['grid'], linewidth=style['grid_width'])
    return m


def g2m(m: Basemap, coord: Tuple[float, float]) \
        -> Tuple[float, float]:
    """
    Convert geographical coordinate into x-y-coordinates in the plotting space.

    :param m:
        The Basemap instance to use for conversion.
    :type m: mpl_toolkits.basemap.Basemap

    :param coord:
        A tuple with the latitude and longitude.
    :type coord: Tuple[float, float]

    :return:
        A tuple with the x and y coordinates in the plotting space.
    :rtype: Tuple[float, float]
    """
    return m(coord[1], coord[0])


def g2ms(m: Basemap, coords: Iterable[Tuple[float, float]]) \
         -> List[Tuple[float, float]]:
    """
    Convert an iterable with geographical coordinates into
    a list of x-y-coordinates in the plotting space.

    :param m:
        The Basemap instance to use for conversion.
    :type m: mpl_toolkits.basemap.Basemap

    :param coords:
        An iterable with geographical coordinates (lat, lon).
    :type coords: Iterable[Tuple[float, float]]

    :return:
        A list with x-y-coordinates in the plotting space.
    :rtype:
        List[Tuple[float, float]]
    """
    return [m(c[1], c[0]) for c in coords]


def g2xys(m: Basemap, coords: Iterable[Tuple[float, float]]) \
          -> Tuple[Sequence[float], Sequence[float]]:
    """
    Convert an iterable with geographical coordinates into
    two sequences with x- and y-coordinates in the plotting space.

    Can be used to convert an iterable with geographic coordinates
    into the input for a line or scatter plot.

    :param m:
        The Basemap instance to use for conversion.
    :type m: mpl_toolkits.basemap.Basemap

    :param coords:
        An iterable with geographical coordinates (lat, lon).
    :type coords: Iterable[Tuple[float, float]]

    :return:
        Two lists with x- and y-coordinates in the plotting space.
    :rtype:
        Tuple[Sequence[float], Sequence[float]]
    """
    x, y = zip(*g2ms(m, coords))
    return x, y


def _shoot(lon: float, lat: float, azimuth: float, maxdist: float):
    """
    Shooter Function
    Original javascript on http://williams.best.vwh.net/gccalc.htm
    Translated to python by Thomas Lecocq
    """
    glat1 = lat * np.pi / 180.
    glon1 = lon * np.pi / 180.
    s = maxdist / 1.852
    faz = azimuth * np.pi / 180.

    EPS= 0.00000000005
    if ((np.abs(np.cos(glat1))<EPS) and not (np.abs(np.sin(faz))<EPS)):
        raise Exception("Only N-S courses are meaningful, starting at a pole!")

    a=6378.13/1.852
    f=1/298.257223563
    r = 1 - f
    tu = r * np.tan(glat1)
    sf = np.sin(faz)
    cf = np.cos(faz)
    if (cf==0):
        b=0.
    else:
        b=2. * np.arctan2 (tu, cf)

    cu = 1. / np.sqrt(1 + tu * tu)
    su = tu * cu
    sa = cu * sf
    c2a = 1 - sa * sa
    x = 1. + np.sqrt(1. + c2a * (1. / (r * r) - 1.))
    x = (x - 2.) / x
    c = 1. - x
    c = (x * x / 4. + 1.) / c
    d = (0.375 * x * x - 1.) * x
    tu = s / (r * a * c)
    y = tu
    c = y + 1
    while (np.abs (y - c) > EPS):

        sy = np.sin(y)
        cy = np.cos(y)
        cz = np.cos(b + y)
        e = 2. * cz * cz - 1.
        c = y
        x = e * cy
        y = e + e - 1.
        y = (((sy * sy * 4. - 3.) * y * cz * d / 6. + x) *
              d / 4. - cz) * sy * d + tu

    b = cu * cy * cf - su * sy
    c = r * np.sqrt(sa * sa + b * b)
    d = su * cy + cu * sy * cf
    glat2 = (np.arctan2(d, c) + np.pi) % (2*np.pi) - np.pi
    c = cu * cy - su * sy * cf
    x = np.arctan2(sy * sf, c)
    c = ((-3. * c2a + 4.) * f + 4.) * c2a * f / 16.
    d = ((e * cy * c + cz) * sy * c + y) * sa
    glon2 = ((glon1 + x - (1. - c) * d * f + np.pi) % (2*np.pi)) - np.pi

    baz = (np.arctan2(sa, b) + np.pi) % (2 * np.pi)

    glon2 *= 180./np.pi
    glat2 *= 180./np.pi
    baz *= 180./np.pi

    return (glon2, glat2, baz)


def _equi(m: Basemap, centerlon: float, centerlat: float, radius: float) \
          -> Tuple[float, float]:
    glon1 = centerlon
    glat1 = centerlat
    X = []
    Y = []
    for azimuth in range(0, 360):
        glon2, glat2, baz = _shoot(glon1, glat1, azimuth, radius)
        X.append(glon2)
        Y.append(glat2)
    X.append(X[0])
    Y.append(Y[0])

    #~ m.plot(X,Y,**kwargs) #Should work, but doesn't...
    return m(X, Y)
