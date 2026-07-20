from pathlib import Path
import runpy
from unittest import mock
import unittest


REPOSITORY_ROOT = Path(__file__).parents[1]


class PackagingMetadataTests(unittest.TestCase):
    def test_supported_python_versions_always_install_pyqt(self):
        with mock.patch("setuptools.setup") as setup:
            runpy.run_path(str(REPOSITORY_ROOT / "setup.py"), run_name="__main__")

        metadata = setup.call_args.kwargs
        self.assertEqual(metadata["version"], "0.2.8.1")
        self.assertEqual(metadata["python_requires"], ">=3.8.10,<3.12")
        self.assertIn("PyQt5 >= 5.15.5", metadata["install_requires"])
        self.assertIn("pyqtgraph == 0.12.3", metadata["install_requires"])
        self.assertIn("numpy >= 1.20.3, < 2", metadata["install_requires"])
        self.assertIn(
            "opencv-python >= 4.5.4.60, < 4.12", metadata["install_requires"]
        )
        self.assertFalse(
            any(requirement.startswith(("h5py", "tables"))
                for requirement in metadata["install_requires"])
        )
        self.assertFalse(
            any(requirement.startswith("PyQt5") and ";" in requirement
                for requirement in metadata["install_requires"])
        )
        self.assertIn(
            "Programming Language :: Python :: 3.11", metadata["classifiers"]
        )
        self.assertNotIn("Typing :: Typed", metadata["classifiers"])
        self.assertEqual(
            metadata["entry_points"]["console_scripts"],
            ["herbs=herbs.run_herbs:run_herbs"],
        )

    def test_project_links_point_to_the_current_repository(self):
        with mock.patch("setuptools.setup") as setup:
            runpy.run_path(str(REPOSITORY_ROOT / "setup.py"), run_name="__main__")

        metadata = setup.call_args.kwargs
        self.assertEqual(
            metadata["url"], "https://github.com/mohebi-n-associates/HERBS"
        )
        self.assertEqual(
            metadata["project_urls"]["Bug Tracker"],
            "https://github.com/mohebi-n-associates/HERBS/issues",
        )


if __name__ == "__main__":
    unittest.main()
