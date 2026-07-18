# What’s New in HERBS 0.2.8.1

Release date: 18 July 2026

HERBS 0.2.8.1 is a reliability, security, and maintainability release. It does not intentionally change the core registration workflow. Instead, it corrects coordinate-processing errors, prevents several GUI crashes, makes file and network operations safer, improves installation behavior, and adds automated regression coverage.

## Highlights

- Correct and consistent atlas, segmentation, boundary, Bregma, and probe coordinates.
- A safe, versioned HERBS archive format for user-created project and data files.
- Deterministic image and atlas loading with clearer failure handling.
- Atomic, HTTPS-only atlas downloads that do not replace valid files with partial data.
- Fixed label, layer, cell-detection, probe-eraser, and slice-registration behavior.
- Supported packaging for Python 3.8.10 through 3.11, including a console launcher.
- Package resources and preferences no longer depend on or modify the process working directory.
- 51 regression tests plus continuous integration across all supported Python versions.

## Atlas and Coordinate Correctness

### Custom-atlas transforms

Custom atlas intensity data, segmentation labels, and Bregma coordinates now receive the same axis flips and transposition. Previously, an atlas could appear correctly oriented while its labels or Bregma remained in a different coordinate system, producing incorrect region and probe results.

An unspecified Bregma coordinate is now converted to the midpoint of the original source volume before the volume transform is applied. This preserves the intended anatomical location after axes are reordered or reversed.

### Probe-coordinate bounds

Probe insertion points, shank columns, and recording sites are now validated against every atlas dimension. Negative coordinates and coordinates equal to an axis size are rejected instead of being accepted by NumPy as wrapped or out-of-range indexes.

This prevents probes near an atlas edge from silently sampling the wrong anatomy or raising an indexing exception later in the calculation.

### Allen atlas boundaries

Processed sagittal, coronal, and horizontal Allen boundary volumes are now returned under the keys expected by the atlas viewer. A shape check ensures the three boundary volumes remain aligned.

### Atlas loading and processing

Atlas loaders now have deterministic success and failure contracts:

- Data fields are initialized before reading begins.
- Core file failures cannot be overwritten by a later successful optional-boundary read.
- Raw-processing functions always return the documented six-item result.
- Atlas, segmentation, mask, and boundary shapes are validated.
- Both three-dimensional masks and four-dimensional masks with one trailing channel are supported.
- Constant-valued atlas volumes normalize to zero without producing `NaN` values.
- A failed worker remains in a failure state and reports the actual error.

Custom-atlas mesh downsampling factors must now be integers of at least 2 and must fit all three volume dimensions. Processing stops after reporting an invalid factor rather than continuing with bad state. The factor input also no longer connects a no-argument Qt signal to a slot that requires text.

### Atlas slices at Bregma

A registered slice at `0 mm` from Bregma is now considered valid. The previous readiness check treated zero as missing data, which prevented processing of the anatomically central slice. Width, height, distance, and the two-dimensional Bregma point are now validated independently, with positive dimensions and finite coordinates required.

## Safer HERBS Files

### New archive format

New user-created files are saved as versioned HERBS archives instead of general-purpose Python pickles. The following formats use the new archive implementation:

- Projects: `.herbs`
- Layers: `.herbslayer`
- Objects: `.herbsobj`
- Atlas slices: `.herbsslice`
- Triangulation data: `.herbstri`

Each archive contains a JSON manifest and NumPy arrays written with pickling disabled. The loader verifies the format name, schema version, payload kind, required fields, referenced array entries, duplicate archive members, manifest size, and total expanded size.

Writes are atomic: HERBS writes a temporary file beside the destination and replaces the destination only after the complete archive has been created. A failed save therefore does not destroy the last valid file.

### Legacy-file compatibility

Legacy `.pkl` files can still be opened when they contain the inert built-in and NumPy data types used by older HERBS saves. They are read with a restricted unpickler that rejects executable or unsupported Python globals.

After opening a legacy file, save it again in the corresponding new HERBS format. Some legacy files containing arbitrary custom Python or Qt objects will now be rejected intentionally rather than executed.

The safe archive format applies to user-created project, layer, object, slice, and triangulation files. Internal atlas preprocessing caches remain implementation-specific and should only be obtained from trusted atlas processing or download sources.

### Consistent loading results

Invalid, missing, corrupt, or unsupported HERBS files now return the same `(data, error)` result shape. Callers can report a useful error without failing while unpacking a different return type.

## Image Loading

Image readers now expose a consistent data and metadata contract:

- An 8-bit grayscale TIFF is treated as one grayscale channel, not RGB.
- RGB TIFF data and multi-page grayscale stacks are distinguished using TIFF axes.
- Channel-axis TIFF data is moved into the channel position expected by the viewer.
- Images with more than four channels are rejected before fixed-size GUI channel controls are indexed.
- Multi-series or unsupported TIFF data returns a defined error state.
- Folder-based image scenes are filtered and sorted deterministically.
- Folder readers populate scene count, scale, channel, pixel-type, and filename metadata.
- CZI `gray8` and non-mosaic images use the same normalized contracts.
- Image-stack opacity is applied consistently.

These changes prevent silent channel swaps, incorrect color controls, uninitialized attributes, and failures that depended on filesystem ordering.

## GUI and Tool Fixes

### Labels

- Label-tree construction uses the supported PyQt5 header-resize API.
- Label colors retain the `#` required for current pyqtgraph color parsing.
- Default colors are stored as `QColor` values, so Reset Colors no longer passes an incompatible string to the color setter.
- Lookup-table size is based on the largest label ID, including label tables whose ordering or parent structure is unusual.
- Empty label tables fail with a clear error.

### Layers

- Saved non-contiguous selections are restored using their actual indexes rather than selecting the first *n* layers.
- Empty saved layer lists no longer index a missing final widget.
- Saved property-list lengths and unique layer links are validated.
- Add Layer supplies the required color argument.
- The toolbar Delete button removes the selected layers instead of treating its Qt `checked` boolean as a layer ID.
- Add and Delete controls are included in the layer-control layout.
- Opacity and blend controls are restored for a single selected layer.

### Cell detector and probe eraser

Cell detection no longer references an undefined mode variable. Grayscale and RGB inputs select a defined detection channel, contour data is normalized safely, and 16-bit inputs are handled without overflowing the expected processing range.

The probe eraser now returns its result consistently instead of reaching a path with no return value.

### Restored layer validation

Loaded pixel layers must match the current image dimensions and include all required metadata. Negative or out-of-range processing levels and mismatched declared sizes are rejected before display. Invalid layers abort the operation instead of partially modifying the image view.

## Atlas Downloads

Atlas downloads now share one hardened implementation:

- Only HTTPS URLs and HTTPS redirects are accepted.
- Requests have connection and read timeouts.
- HTTP error statuses are reported.
- Content length is checked when the server provides it.
- SHA-256 verification is performed when an expected digest is supplied.
- Empty, cancelled, incomplete, or failed downloads are removed.
- Existing destination files are replaced atomically only after verification.
- Progress reaches 100% only after the final file is in place.

Downloader worker threads are retained for their full lifetime, errors propagate back to the dialog, and the GUI no longer performs a blocking preliminary `HEAD` request. This prevents partial atlas files, silent background-thread failures, and avoidable interface freezes.

## Installation and Runtime Behavior

### Supported versions and dependencies

Package metadata now consistently supports Python `>=3.8.10,<3.12`, and PyQt5 5.15.5 or newer is installed for every supported Python version, including Python 3.11.

The unused `h5py` and `tables` dependencies were removed. HERBS did not import either library, while `tables` could force an unnecessary native HDF5 build and prevent installation on otherwise supported systems.

The package, installer metadata, and About dialog now obtain `0.2.8.1` from one canonical version value. Project and issue links point to the current `mohebi-n-associates/HERBS` repository.

### Launch options

HERBS can be launched using any of the following:

```bash
herbs
python -m herbs
```

```python
import herbs
herbs.run_herbs()
```

Importing `herbs` no longer imports the complete GUI and CZI stack immediately. The heavier GUI imports occur when the application is launched or the CZI reader is requested.

### Resources and preferences

Icons, stylesheets, UI files, and bundled data now resolve relative to the installed HERBS package. The launcher no longer changes the caller’s process-wide working directory, so relative paths in notebooks, scripts, and embedding applications continue to work normally.

The last selected atlas path is stored atomically in the user configuration directory instead of `herbs/data/atlas_path.txt` inside the installation:

- Windows: `%APPDATA%\HERBS\settings.json`
- macOS: `~/Library/Application Support/HERBS/settings.json`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/HERBS/settings.json`

`HERBS_CONFIG_DIR` can override the configuration directory. Because the old package-local preference was removed, HERBS may ask you to select the atlas folder once after upgrading.

## Maintainability and Verification

Focused modules were extracted for atlas transforms, coordinate checks, slice and layer validation, persistence, download handling, cell-channel selection, package resources, and user settings. This reduces the amount of safety-critical logic embedded directly in the main GUI controller and makes it independently testable.

Version 0.2.8.1 includes:

- 51 automated regression tests.
- Headless GUI construction and resource-path smoke testing.
- Python source compilation checks.
- Targeted Ruff checks for syntax errors and undefined names.
- Wheel-build and package-content verification.
- GitHub Actions coverage for Python 3.8, 3.9, 3.10, and 3.11.

## Upgrade Notes

1. Pull the latest source and reinstall HERBS:

   ```bash
   git pull
   python -m pip install . --upgrade
   ```

2. If prompted, select your atlas folder once so it can be saved in the new user configuration file.

3. Open important legacy `.pkl` project or data files and save them in the new HERBS format.

4. If you automate HERBS file handling, update filters and scripts to recognize the new extensions listed above.

5. Use Python 3.8.10 through 3.11. Python 3.12 and later are not declared supported by this release.

## Implementation References

The changes were kept as separate issue-level commits:

| Commit | Change |
| --- | --- |
| `3241b11` | Fix custom atlas coordinate transforms |
| `879b17f` | Reject probe coordinates outside atlas bounds |
| `4583fab` | Expose processed Allen atlas boundaries |
| `4f54836` | Validate restored image layers before display |
| `4071edd` | Return consistent errors for invalid HERBS files |
| `01fb3ba` | Replace executable user files with safe archives |
| `01e56a2` | Make atlas loading failures deterministic |
| `4bc5a66` | Normalize image reader contracts and channel handling |
| `8fe7c3a` | Prevent cell detector and probe eraser crashes |
| `b2ecbaf` | Make atlas downloads atomic and failure-aware |
| `56994ec` | Fix label color reset state |
| `3912cc5` | Restore saved layer selections exactly |
| `cb1765e` | Allow atlas slices at Bregma |
| `db374d4` | Validate custom atlas downsampling factors |
| `9d2f8e7` | Align Python and PyQt package metadata |
| `4828645` | Keep runtime state outside the package tree |
| `99886a2` | Use one canonical HERBS version |
| `c0bc2d9` | Add regression test CI |
| `f6d20ff` | Remove unused HDF5 runtime dependencies |
| `00b5368` | Bump HERBS version to 0.2.8.1 |
