import numpy as np


def parse_image_data(content, shape, n_bytes):
    dtype = np.dtype(f">i{n_bytes}")

    return np.frombuffer(content, dtype).reshape(shape)
