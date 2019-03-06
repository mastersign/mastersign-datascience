# -*- coding: utf-8 -*-

"""
This module contains functionality used to plot on a map.

See e.g. `mastersign.datascience.plot.scatter_map()`.
"""

import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature, COLORS


def create_projection(name='Mercator', **kwargs):
    proj_class = getattr(ccrs, name)
    return proj_class(**kwargs)


def draw_cartographic_features(ax, resolution='110m'):
    features = []
    features.append(NaturalEarthFeature(
        'physical', 'ocean', resolution,
        edgecolor='face',
        facecolor=COLORS['water'],
        zorder=-1))
    features.append(NaturalEarthFeature(
        'physical', 'land', resolution,
        edgecolor='face',
        facecolor=COLORS['land'],
        zorder=-1))
    features.append(NaturalEarthFeature(
        'physical', 'coastline', resolution,
        edgecolor='black',
        facecolor='none'))
    features.append(NaturalEarthFeature(
        'physical', 'rivers_lake_centerlines', resolution,
        edgecolor=COLORS['water'],
        facecolor='none'))
    features.append(NaturalEarthFeature(
        'physical', 'lakes', resolution,
        edgecolor='face',
        facecolor=COLORS['water']))
    features.append(NaturalEarthFeature(
        'cultural', 'admin_0_boundary_lines_land', resolution,
        edgecolor='black',
        facecolor='none'))
    features.append(NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lakes', resolution,
        edgecolor='black',
        facecolor='none'))

    for f in features:
        ax.add_feature(f)
    # ax.add_feature(cfeature.LAND)
    # ax.add_feature(cfeature.COASTLINE)
    # ax.add_feature(cfeature.LAKES)
    # ax.add_feature(cfeature.RIVERS)
    # ax.add_feature(cfeature.BORDERS)
    # ax.add_feature(cfeature.STATES)
    # states_provinces = cfeature.NaturalEarthFeature(
    #     category='cultural',
    #     name='admin_1_states_provinces_lines',
    #     scale='50m',
    #     facecolor='none')
    # ax.add_feature(states_provinces)
    # ax.gridlines()

    return ax
