# Changelog

## 2.1.0

- Add Join only mode for combining evaluated geometry without remeshing.
- Bake visible modifiers from every source, not just the active input; retain source objects and modifiers.
- Normalize world transforms before remeshing, handling negative scale and reporting evaluated polygon counts.
- Restore original visibility faithfully and limit restoration to the current view layer.
- Clean unused generated meshes and restore selection/active object on failure.
- Add Blender integration tests and packaged-install verification to CI.

## 2.0.0

- Introduce non-destructive copies, remesh/shrinkwrap/decimate processing, validation, and packaging.
