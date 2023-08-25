# xarray-ceos-alos2

Read ALOS2 CEOS files into `datatree` objects.

## Installation

From PyPI

```sh
pip install xarray-ceos-alos2
```

From conda-forge

```sh
conda install -c conda-forge xarray-ceos-alos2
```

## Usage

```python
import ceos_alos2

tree = ceos_alos2.open_alos2(url, chunks={}, backend_options={"requests_per_chunk": 4096})
```
