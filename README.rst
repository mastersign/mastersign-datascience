#######################
Mastersign Data Science
#######################

    High level helpers for data science in Python with Pandas.

************
Installation
************

::

	pip install mastersign-datascience

or

::

	python ./setup.py install


-----------------------------
Plotting on Cartographic Maps
-----------------------------

You can use the library without further manual steps;
but if you want to use plotting functions which draw on a cartographic maps,
like ``scatter_map()``, you must install *Basemap* yourself.
PyPI does not host a version of *Basemap* which can easily be used as a dependency.
Therefore *Basemap* is not listed as a dependency in this library.

On Windows, you may install the Wheel
from https://www.lfd.uci.edu/~gohlke/pythonlibs/#basemap .
Download the e.g. ``basemap‑1.2.0‑cp36‑cp36m‑win_amd64.whl`` and then install it
with ``pip``:

::

	pip install .\basemap‑1.2.0‑cp36‑cp36m‑win_amd64.whl

On Linux you may install *Basemap* with your distributions package manager.
E.g. on Ubuntu you can use ``apt``:

::

	sudo apt install python3-mpltoolkits.basemap


*************
Documentation
*************

https://mastersign.github.io/mastersign-datascience

*************
Demonstration
*************

Take a look at the Jupyter Notebooks ``demo-*.ipynb`` for demonstration.
