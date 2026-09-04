# Object Joiner for Blender

[![Tests](https://github.com/bgivenb/Blender-Object-Joiner/actions/workflows/test.yml/badge.svg)](https://github.com/bgivenb/Blender-Object-Joiner/actions/workflows/test.yml)

A Blender add-on for turning multiple selected meshes into one continuous, controllably decimated sculpting mesh while preserving the originals. It duplicates the inputs, voxel-remeshes the copies, shrinkwraps the result toward the source surface, decimates it, and runs a final shrinkwrap pass to restore surface detail.

<a href="https://www.reddit.com/r/blender/comments/1gq8xs4/i_made_a_free_plugin_to_join_multiple_meshes/"><img src="docs/images/original-reddit-demo.gif" alt="Original Object Joiner sculpting workflow in Blender" width="720"></a>

*Excerpt from the original Blender walkthrough. [Watch the complete demo on r/blender](https://www.reddit.com/r/blender/comments/1gq8xs4/i_made_a_free_plugin_to_join_multiple_meshes/) or read the [design discussion](https://www.reddit.com/r/blender/comments/1gq8f3s/i_made_a_free_blender_addon_for_merging_meshes/).*

### Current reproducible example

![Two source meshes beside their joined result](docs/images/object-joiner-example.png)

## Design

- **Non-destructive:** processing happens on copies in a dedicated result collection.
- **Bounded controls:** voxel size and decimation ratio are validated before Blender begins expensive work.
- **Measurable:** each result records the source object count and before/after polygon counts as custom properties; Blender also reports the percentage change.
- **Recoverable:** hidden source objects are tagged and can be restored with **Unhide Originals**.
- **Failure-aware:** partial results are removed and source visibility is restored if the operation fails.

## Install

1. Download the add-on ZIP and matching `.sha256` file from the [latest release](https://github.com/bgivenb/Blender-Object-Joiner/releases/latest).
2. Verify the archive against the published SHA-256 checksum.
3. In Blender 3.6 or newer, open **Edit → Preferences → Add-ons → Install** and select the downloaded ZIP.
4. Enable **Object Joiner**.
5. Open the 3D Viewport sidebar (`N`) and choose **Object Joiner**.

To build the same installable archive from a source checkout, run `python scripts/package_addon.py`; the ZIP and checksum are written to `dist/`.

## Use

Select at least two mesh objects, choose a voxel size and target decimation ratio, and click **Build Joined Mesh**. Smaller voxels preserve more detail but cost substantially more time and memory. Start with `0.05 m` and refine from there based on scene scale.

The originals remain intact. When **Hide original objects** is enabled, use **Unhide Originals** to restore their viewport and render visibility.

## Development

Run the dependency-free tests:

```bash
python -m unittest discover -s tests -v
```

Verify add-on registration in Blender:

```bash
blender --background --python-expr "import sys; sys.path.insert(0, '.'); import objectjoiner as addon; addon.register(); addon.unregister()"
```

Rebuild the checked-in example image:

```bash
blender --background --python scripts/render_example.py
```

Build and checksum the installable add-on archive with:

```bash
python scripts/package_addon.py
```

## Scope

This is an independent hobby project. Always keep a saved copy of important Blender work before running geometry operations.

## License

[CC0 1.0 Universal](LICENSE)
