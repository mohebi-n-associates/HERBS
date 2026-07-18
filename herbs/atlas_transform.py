"""Coordinate transforms shared by custom-atlas processing code."""

import numpy as np


def make_boundary_dict(sagittal, coronal, horizontal):
    """Collect the three atlas boundary volumes after validating alignment."""
    shapes = {np.shape(sagittal), np.shape(coronal), np.shape(horizontal)}
    if len(shapes) != 1:
        raise ValueError("Atlas boundary volumes must have matching shapes.")
    return {
        "s_contour": sagittal,
        "c_contour": coronal,
        "h_contour": horizontal,
    }


def prepare_atlas_mask(mask_data, volume_shape):
    """Normalize supported 3-D/4-D masks and validate their volume shape."""
    mask_data = np.asarray(mask_data)
    if mask_data.ndim == 4 and mask_data.shape[-1] == 1:
        mask_data = mask_data[..., 0]
    if mask_data.ndim != 3 or tuple(mask_data.shape) != tuple(volume_shape):
        raise ValueError("Atlas mask must be 3-D and match the atlas volume shape.")
    return mask_data


def normalize_atlas_volume(atlas_data):
    """Normalize an atlas to [0, 1] without dividing by zero."""
    atlas_data = np.asarray(atlas_data, dtype=float)
    atlas_data = atlas_data - np.min(atlas_data)
    maximum = np.max(atlas_data)
    if maximum == 0:
        return np.zeros_like(atlas_data)
    return atlas_data / maximum


def transform_atlas_volumes(atlas_data, segmentation_data, bregma, axis_info):
    """Transform atlas data, labels, and Bregma into the same axis system.

    ``direction_change`` describes flips in the source coordinate system and
    ``to_HERBS`` describes the subsequent transpose into HERBS' stored axis
    order. A zero Bregma coordinate retains the UI's historical meaning of
    "unspecified" and is replaced with the midpoint of that source axis.
    """
    atlas_data = np.asarray(atlas_data)
    segmentation_data = np.asarray(segmentation_data)
    if atlas_data.shape != segmentation_data.shape:
        raise ValueError("Atlas and segmentation volumes must have matching shapes.")

    source_shape = np.asarray(atlas_data.shape, dtype=int)
    order = tuple(axis_info["to_HERBS"])
    direction_change = tuple(axis_info["direction_change"])
    if sorted(order) != [0, 1, 2] or len(direction_change) != 3:
        raise ValueError("Atlas axis information must describe three unique axes.")

    transformed_atlas = atlas_data
    transformed_segmentation = segmentation_data
    transformed_bregma = np.asarray(bregma, dtype=int).copy()
    if transformed_bregma.shape != (3,):
        raise ValueError("Bregma must contain exactly three voxel coordinates.")

    unspecified = transformed_bregma == 0
    transformed_bregma[unspecified] = source_shape[unspecified] // 2

    for axis, should_flip in enumerate(direction_change):
        if should_flip:
            transformed_atlas = np.flip(transformed_atlas, axis=axis)
            transformed_segmentation = np.flip(transformed_segmentation, axis=axis)
            transformed_bregma[axis] = (
                source_shape[axis] - 1 - transformed_bregma[axis]
            )

    transformed_atlas = np.transpose(transformed_atlas, order)
    transformed_segmentation = np.transpose(transformed_segmentation, order)
    transformed_bregma = transformed_bregma[np.asarray(order)]

    return transformed_atlas, transformed_segmentation, transformed_bregma
