from .iterators import InfinitePermutationIterator, chunked_readlines_iterator, BufferedShuffleIterator, TransformIterator
from typing import Union, Iterable, Callable, Any, Optional
import os

"""
This module contains common datasets, which are implemented as convenience functions that compose underlying Infinibatch iterators.
"""


def bump_seed(seed: Optional[int], step = 1):
    """
    Helper to bump a random seed if not None
    """
    return None if seed is None else seed + 1


def chunked_dataset_iterator(paths: Union[str, Iterable[str]], shuffle: bool=True, buffer_size: int=2**20, transform: Callable[[Any],Any]=None, seed: Optional[int]=None, num_instances: int=1, instance_rank: int=0):
    """
    Dataset reading data from gzipped chunks.

    This dataset infinitely repeats the data.

    Args:
        paths: path, or list of paths, of directory containing dataset, i.e., a collection of .gz-files containing compressed text
        shuffle: if true, the data is shuffled
        buffer_size: size of the buffer in number of samples / data items used for shuffling
        transform: transform to be applied to each data item (transform(Any) -> Any)
        seed: random seed (or None)
        num_instances: number of instances of this dataset. Meant for use with multi-process data loading, e.g., in distributed training.
        instance_rank: rank of this instance of the dataset. Meant for use with multi-process data loading, e.g., in distributed training.
    """
    if isinstance(paths, str):  # handle single string
        paths = [paths]
    # set up the chunk reader
    chunk_file_paths = [  # enumerate all .gz files in the given paths
        os.path.join(path, subpath.name)
        for path in paths
        for subpath in os.scandir(path)
        if subpath.is_file() and subpath.name.endswith('.gz')
    ]
    chunk_file_paths.sort()  # make sure file order is always the same, independent of OS
    chunks  = InfinitePermutationIterator(chunk_file_paths, seed, shuffle=shuffle, num_instances=num_instances, instance_rank=instance_rank)
    # set up the item reader
    samples = chunked_readlines_iterator(chunks)
    # set up the item randomizer
    if shuffle:
        # use different seed for BufferedShuffleGenerator
        samples = BufferedShuffleIterator(samples, buffer_size, bump_seed(seed, 1))
    
    # apply transform, if given
    if transform is not None:
        samples = TransformIterator(samples, transform)

    # this is what we are serving out
    return samples
