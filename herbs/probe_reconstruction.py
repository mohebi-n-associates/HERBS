"""Build self-contained coordinate metadata for exported probe objects."""

from pathlib import Path

import numpy as np


PROBE_RECONSTRUCTION_SCHEMA_VERSION = 1
HERBS_AXES = ("LR", "AP", "DV")
HERBS_AXIS_DIRECTIONS = ("right", "anterior", "superior")
_OPPOSITE_DIRECTION = {
    "right": "left",
    "left": "right",
    "anterior": "posterior",
    "posterior": "anterior",
    "superior": "inferior",
    "inferior": "superior",
}
_ALLEN_CCF_2017_SHAPES = {
    10.0: (1320, 800, 1140),
    25.0: (528, 320, 456),
    50.0: (264, 160, 228),
    100.0: (132, 80, 114),
}


def normalize_axis_info(axis_info, herbs_shape):
    """Validate an atlas transform and fill fields required for inversion."""
    herbs_shape = tuple(int(value) for value in herbs_shape)
    if len(herbs_shape) != 3 or any(value <= 0 for value in herbs_shape):
        raise ValueError("HERBS atlas shape must contain three positive dimensions.")

    supplied = axis_info is not None
    if axis_info is None:
        axis_info = {
            "to_HERBS": (0, 1, 2),
            "from_HERBS": (0, 1, 2),
            "direction_change": (False, False, False),
            "size": herbs_shape,
        }

    to_herbs = tuple(int(value) for value in axis_info["to_HERBS"])
    if len(to_herbs) != 3 or sorted(to_herbs) != [0, 1, 2]:
        raise ValueError("to_HERBS must be a permutation of three atlas axes.")

    inverse = tuple(int(value) for value in np.argsort(to_herbs))
    from_herbs = tuple(
        int(value) for value in axis_info.get("from_HERBS", inverse)
    )
    if from_herbs != inverse:
        raise ValueError("from_HERBS is not the inverse of to_HERBS.")

    direction_change = tuple(bool(value) for value in axis_info["direction_change"])
    if len(direction_change) != 3:
        raise ValueError("direction_change must describe exactly three source axes.")

    if "size" in axis_info:
        source_shape = tuple(int(value) for value in axis_info["size"])
    else:
        source_shape_array = np.empty(3, dtype=int)
        source_shape_array[np.asarray(to_herbs)] = np.asarray(herbs_shape)
        source_shape = tuple(source_shape_array.tolist())
    if len(source_shape) != 3 or any(value <= 0 for value in source_shape):
        raise ValueError("Source atlas shape must contain three positive dimensions.")

    expected_herbs_shape = tuple(np.asarray(source_shape)[np.asarray(to_herbs)])
    if expected_herbs_shape != herbs_shape:
        raise ValueError(
            "Atlas axis metadata does not match the atlas used for the probe."
        )

    return {
        "to_HERBS": to_herbs,
        "from_HERBS": from_herbs,
        "direction_change": direction_change,
        "size": source_shape,
        "available_from_atlas": supplied,
    }


def herbs_vox_to_source_vox(points, axis_info):
    """Convert one or more continuous HERBS voxels into source-atlas voxels."""
    points = np.asarray(points, dtype=float)
    if points.shape[-1:] != (3,):
        raise ValueError("Coordinate arrays must end with three values.")

    source_points = points[..., np.asarray(axis_info["from_HERBS"])].copy()
    source_shape = np.asarray(axis_info["size"], dtype=float)
    for axis, should_flip in enumerate(axis_info["direction_change"]):
        if should_flip:
            source_points[..., axis] = (
                source_shape[axis] - 1 - source_points[..., axis]
            )
    return source_points


def _source_axis_metadata(axis_info):
    source_axes = [None, None, None]
    source_directions = [None, None, None]
    for herbs_axis, source_axis in enumerate(axis_info["to_HERBS"]):
        source_axes[source_axis] = HERBS_AXES[herbs_axis]
        direction = HERBS_AXIS_DIRECTIONS[herbs_axis]
        if axis_info["direction_change"][source_axis]:
            direction = _OPPOSITE_DIRECTION[direction]
        source_directions[source_axis] = direction
    return source_axes, source_directions


def _is_allen_ccf_2017(axis_info, voxel_size_um):
    expected_shape = _ALLEN_CCF_2017_SHAPES.get(float(voxel_size_um))
    return (
        expected_shape == tuple(axis_info["size"])
        and tuple(axis_info["to_HERBS"]) == (2, 0, 1)
        and tuple(axis_info["direction_change"]) == (True, True, False)
    )


def _flatten_groups(groups, dtype=None):
    arrays = [np.asarray(group, dtype=dtype) for group in groups]
    if not arrays:
        return np.empty((0,), dtype=dtype)
    return np.concatenate(arrays, axis=0)


def _structure_text(structure_ids, label_info, key, default=""):
    lookup = {
        int(label_id): str(value)
        for label_id, value in zip(
            np.ravel(label_info["index"]), np.ravel(label_info[key])
        )
    }
    return [lookup.get(int(label_id), default) for label_id in structure_ids]


def _coordinate_record(relative_bregma_vox, bregma_herbs_vox, voxel_size_um,
                       axis_info, voxel_index=None, allen_ccf=False):
    relative_bregma_vox = np.asarray(relative_bregma_vox, dtype=float)
    herbs_vox = relative_bregma_vox + bregma_herbs_vox
    source_vox = herbs_vox_to_source_vox(herbs_vox, axis_info)
    record = {
        "herbs_vox": herbs_vox,
        "herbs_vox_index": (
            np.asarray(voxel_index, dtype=int)
            if voxel_index is not None
            else herbs_vox.astype(int)
        ),
        "bregma_um": relative_bregma_vox * voxel_size_um,
        "source_vox": source_vox,
        "source_um": source_vox * voxel_size_um,
    }
    if allen_ccf:
        record["allen_ccf_vox"] = record["source_vox"].copy()
        record["allen_ccf_um"] = record["source_um"].copy()
    return record


def build_probe_reconstruction(
    *,
    insertion_bregma_vox,
    terminus_bregma_vox,
    insertion_vox_index,
    terminus_vox_index,
    contact_bregma_vox,
    contact_vox_index,
    contact_structure_ids,
    contact_local_from_tip_base_um,
    probe_length_um,
    probe_settings,
    site_face,
    voxel_size_um,
    bregma_herbs_vox,
    herbs_atlas_shape,
    label_info,
    axis_info=None,
    atlas_identifier=None,
    atlas_path=None,
    software_version=None,
):
    """Create the reconstruction payload embedded in each merged probe.

    Contacts are flattened column-major. Within a column, index zero is the
    contact nearest the geometric tip for probe geometries generated by HERBS.
    """
    voxel_size_um = float(voxel_size_um)
    if not np.isfinite(voxel_size_um) or voxel_size_um <= 0:
        raise ValueError("Atlas voxel size must be a positive number.")
    bregma_herbs_vox = np.asarray(bregma_herbs_vox, dtype=float)
    if bregma_herbs_vox.shape != (3,):
        raise ValueError("Bregma must contain three HERBS voxel coordinates.")

    normalized_axis_info = normalize_axis_info(axis_info, herbs_atlas_shape)
    source_axes, source_directions = _source_axis_metadata(normalized_axis_info)
    allen_ccf = _is_allen_ccf_2017(normalized_axis_info, voxel_size_um)

    contact_counts = [len(group) for group in contact_bregma_vox]
    if not (
        contact_counts == [len(group) for group in contact_vox_index]
        == [len(group) for group in contact_structure_ids]
        == [len(group) for group in contact_local_from_tip_base_um]
    ):
        raise ValueError("Probe contact coordinate groups do not have matching sizes.")

    contact_bregma_vox_flat = _flatten_groups(contact_bregma_vox, dtype=float)
    contact_vox_index_flat = _flatten_groups(contact_vox_index, dtype=int)
    structure_ids = _flatten_groups(contact_structure_ids, dtype=int)
    local_from_tip_base_um = _flatten_groups(
        contact_local_from_tip_base_um, dtype=float
    )
    column_index = np.concatenate(
        [np.full(count, column, dtype=int) for column, count in enumerate(contact_counts)]
    ) if contact_counts else np.empty((0,), dtype=int)
    index_in_column = np.concatenate(
        [np.arange(count, dtype=int) for count in contact_counts]
    ) if contact_counts else np.empty((0,), dtype=int)

    contact_herbs_vox = contact_bregma_vox_flat + bregma_herbs_vox
    contact_source_vox = herbs_vox_to_source_vox(
        contact_herbs_vox, normalized_axis_info
    )
    tip_length_um = float(probe_settings.get("tip_length") or 0)
    distance_from_tip_um = local_from_tip_base_um[:, 0] + tip_length_um
    contact_local_um = local_from_tip_base_um.copy()
    contact_local_um[:, 0] = distance_from_tip_um

    contacts = {
        "count": int(len(structure_ids)),
        "site_index": np.arange(len(structure_ids), dtype=int),
        "column_index": column_index,
        "index_in_column": index_in_column,
        "column_contact_counts": np.asarray(contact_counts, dtype=int),
        "ordering": "column-major; index_in_column 0 is tip-nearest",
        "probe_local_axes": ["distance_from_tip", "lateral", "surface_normal"],
        "probe_local_um": contact_local_um,
        "distance_from_tip_um": distance_from_tip_um,
        "distance_from_insertion_um": float(probe_length_um) - distance_from_tip_um,
        "herbs_vox": contact_herbs_vox,
        "herbs_vox_index": contact_vox_index_flat,
        "bregma_um": contact_bregma_vox_flat * voxel_size_um,
        "source_vox": contact_source_vox,
        "source_um": contact_source_vox * voxel_size_um,
        "structure_id": structure_ids,
        "structure_acronym": _structure_text(
            structure_ids, label_info, "abbrev"
        ),
        "structure_name": _structure_text(structure_ids, label_info, "label"),
    }
    if allen_ccf:
        contacts["allen_ccf_vox"] = contacts["source_vox"].copy()
        contacts["allen_ccf_um"] = contacts["source_um"].copy()

    source_name = "Allen Mouse Common Coordinate Framework"
    source_version = "CCFv3 2017"
    if not allen_ccf:
        source_name = atlas_identifier or "Source atlas"
        source_version = None

    atlas = {
        "identifier": atlas_identifier,
        "path_at_export": str(Path(atlas_path).resolve()) if atlas_path else None,
        "voxel_size_um": voxel_size_um,
        "herbs_shape_vox": tuple(int(value) for value in herbs_atlas_shape),
        "bregma_herbs_vox": bregma_herbs_vox,
        "herbs_axes": list(HERBS_AXES),
        "herbs_axis_directions": list(HERBS_AXIS_DIRECTIONS),
        "source_name": source_name,
        "source_version": source_version,
        "source_shape_vox": tuple(normalized_axis_info["size"]),
        "source_axes": source_axes,
        "source_axis_directions": source_directions,
        "bregma_source_vox": herbs_vox_to_source_vox(
            bregma_herbs_vox, normalized_axis_info
        ),
        "axis_transform": normalized_axis_info,
        "label_lookup": label_info,
    }
    atlas["bregma_source_um"] = atlas["bregma_source_vox"] * voxel_size_um

    return {
        "schema_version": PROBE_RECONSTRUCTION_SCHEMA_VERSION,
        "software": {"name": "HERBS", "version": software_version},
        "atlas": atlas,
        "probe": {
            "settings": probe_settings,
            "site_face": site_face,
            "contact_ordering": contacts["ordering"],
        },
        "coordinates": {
            "tip": _coordinate_record(
                terminus_bregma_vox,
                bregma_herbs_vox,
                voxel_size_um,
                normalized_axis_info,
                voxel_index=terminus_vox_index,
                allen_ccf=allen_ccf,
            ),
            "insertion": _coordinate_record(
                insertion_bregma_vox,
                bregma_herbs_vox,
                voxel_size_um,
                normalized_axis_info,
                voxel_index=insertion_vox_index,
                allen_ccf=allen_ccf,
            ),
            "contacts": contacts,
        },
    }
