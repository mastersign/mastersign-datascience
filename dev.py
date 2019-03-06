import pandas as pd
import numpy as np
from mastersign.datascience import plot as pl

data_4 = pd.DataFrame(
    {
        "latitude": np.random.normal(size=100) * 0.5 + 53.5,
        "longitude": np.random.normal(size=100) * 1 + 10.0,
        "value_a": np.random.normal(size=100),
        "value_b": np.random.gamma(2, size=100),
    })


pl.scatter_map(data_4, size=50, map_resolution='50m')
