"""
@author: Jingyi GF{jingyi.g.fuglstad@gmail.com}
"""
import os
from setuptools import setup, find_packages


# Utility function to read the README file.
def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname), encoding="utf-8") as handle:
        return handle.read()


def read_version():
    namespace = {}
    exec(read(os.path.join("herbs", "version.py")), namespace)
    return namespace["__version__"]


CLASSIFIERS = """
Development Status :: 3 - Alpha
Intended Audience :: Science/Research
Intended Audience :: Developers
Intended Audience :: Education
License :: OSI Approved :: MIT License
Programming Language :: Python :: 3
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
Programming Language :: Python :: 3.10
Programming Language :: Python :: 3.11
Programming Language :: Python :: 3 :: Only
Topic :: Software Development
Topic :: Scientific/Engineering
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

REQUIRES = """
PyQt5 >= 5.15.5
aicspylibczi >= 3.0.3
pyqtgraph == 0.12.3
PyOpenGL >= 3.1.5
QtRangeSlider == 0.1.5
opencv-python >= 4.5.4.60
numba >= 0.54.1
numpy >= 1.20.3
scipy >= 1.7.3
requests >= 2.26.0
nibabel >= 3.2.1
pynrrd >= 0.4.3
tifffile >= 2021.11.2
pandas >= 1.3.5
natsort >= 8.0.2
imagecodecs >= 2022.2.22
"""

PACKAGE_DATA = """
main_window.ui
data/query.csv
data/atlas_labels.pkl
icons/*.svg
icons/*.png
icons/layers/*.svg
icons/layers/*.png
icons/sidebar/*.svg
icons/sidebar/*.png
icons/toolbar/*.svg
icons/toolbar/*.png
qss/*.qss
"""


setup(
    name="herbs",
    version=read_version(),
    author="Jingyi GF",
    author_email="jingyi.g.fuglstad@gmail.com",
    description="A Python-based GUI for Histological E-data Registration in Brain Space",
    keywords="brain atlas, histological image registration, probe coordinates",
    url="https://github.com/mohebi-n-associates/HERBS",
    packages=find_packages(),
    package_data={"": [_f for _f in PACKAGE_DATA.split("\n") if _f]},
    include_package_data=True,
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    project_urls={
        "Bug Tracker": "https://github.com/mohebi-n-associates/HERBS/issues",
    },
    classifiers=[_f for _f in CLASSIFIERS.split("\n") if _f],
    python_requires=">=3.8.10,<3.12",
    install_requires=[_f for _f in REQUIRES.split("\n") if _f],
    entry_points={"console_scripts": ["herbs=herbs.run_herbs:run_herbs"]},
)
