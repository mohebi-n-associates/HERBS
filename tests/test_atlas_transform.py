import importlib.util
from pathlib import Path
import unittest

import numpy as np


MODULE_PATH = Path(__file__).parents[1] / "herbs" / "atlas_transform.py"
SPEC = importlib.util.spec_from_file_location("atlas_transform", MODULE_PATH)
atlas_transform = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(atlas_transform)


class AtlasTransformTests(unittest.TestCase):
    def test_volume_labels_and_bregma_receive_identical_transform(self):
        labels = np.arange(2 * 3 * 4).reshape(2, 3, 4)
        atlas = labels.astype(float) + 0.5
        axis_info = {
            "direction_change": (True, False, True),
            "to_HERBS": (2, 0, 1),
        }

        transformed_atlas, transformed_labels, bregma = (
            atlas_transform.transform_atlas_volumes(
                atlas, labels, (1, 2, 3), axis_info
            )
        )

        expected_labels = np.transpose(labels[::-1, :, ::-1], (2, 0, 1))
        np.testing.assert_array_equal(transformed_labels, expected_labels)
        np.testing.assert_array_equal(transformed_atlas, expected_labels + 0.5)
        np.testing.assert_array_equal(bregma, (0, 0, 2))
        self.assertEqual(transformed_atlas.shape, transformed_labels.shape)

    def test_unspecified_bregma_uses_source_midpoints_before_transform(self):
        data = np.zeros((4, 6, 8))
        _, _, bregma = atlas_transform.transform_atlas_volumes(
            data,
            data,
            (0, 0, 0),
            {"direction_change": (False, False, False), "to_HERBS": (1, 2, 0)},
        )

        np.testing.assert_array_equal(bregma, (3, 4, 2))


if __name__ == "__main__":
    unittest.main()
