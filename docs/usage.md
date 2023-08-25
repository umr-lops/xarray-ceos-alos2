# Usage

## Opening datasets

Datasets of levels 1.1, 1.5, or 3.1 can be opened using:

```python
import ceos_alos2

url = "..."
tree = ceos_alos2.open_alos2(url, chunks={})
```

## Backend options

Additional parameters can be set using the `backend_options` parameter. The valid options are:

- `storage_options`: additional parameters passed on to the appropriate `fsspec` filesystem
- `records_per_chunk`: request size when fetching image data (see {ref}`request-size`)
- `use_cache`: use cache files instead of parsing the image files (see {ref}`caching`)
- `create_cache`: create cache files (see {ref}`caching`)

## Access optimizations

(request-size)=

### Request size

The image data of CEOS ALOS2 datasets is subdivided into records that represent the lines (rows) of the image. Each record begins with metadata, followed by the actual line data.

However, this is not optimized for the typical data access pattern: when opening the dataset, all the metadata is read, and once computations on the image are performed the image data is accessed separately. Thus, each record is requested at least twice, once when collecting the metadata and at least once when computing the image data. Additionally, requesting the records one-by-one means that tens of thousands of requests (or syscalls in case of a local file system) have to performed, which can take a very long time.

Using the `records_per_chunk` setting, a number of records can be grouped and requested together. This allows reducing the number of requests by a lot, which in turn makes data access much faster.

:::{tip}
Always specify the request size explicitly
:::

For example:

```python
tree = ceos_alos2.open_alos2(url, chunks={}, backend_options={"records_per_chunk": 4096})
```

(caching)=

### Caching

Even though adjusting the request size can decrease access times, reading and parsing the image metadata still takes a lot of time (in the case of level 1.1 ScanSAR this can take more than 10 minutes). To avoid that, it is possible to save the metadata in special cache files, allowing to open datasets (i.e. reading the file metadata) in a matter of seconds.

The `use_cache` parameter controls whether or not these cache files are used, which can be stored either alongside the image file (i.e. a "remote cache file") or in a local directory (`$user_cache_dir/xarray-ceos-alos2/<hash-of-dataset-url>/<image>.index`, where `$user_cache_dir` depends on the OS). If both exist the remote cache file is preferred.

Cache files can be created either by enabling the `create_cache` flag or by running the `ceos-alos2-create-cache` executable.

Using `create_cache`:

```python
tree = ceos_alos2.open_alos2(
    url,
    chunks={},
    backend_options={"records_per_chunk": 4096, "create_cache": True, "use_cache": False},
)
```

This will open the dataset with a request size of 4096 records and write a local cache file for _each image_.

Using `ceos-alos2-create-cache`:

```sh
ceos-alos2-create-cache --rpc 4096 <image-path>
# or, with a explict target path
ceos-alos2-create-cache --rpc 4096 <image-path> <target-path>
```

This will open a _single_ image with a request size of 4096 records and create a cache file, either in the specified target path, or adjacent to the image file.
