"""Pure validation and reporting helpers for Object Joiner."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeshSummary:
    source_objects: int
    source_polygons: int
    result_polygons: int

    @property
    def change_percent(self) -> float:
        if self.source_polygons == 0:
            return 0.0
        return (
            100.0 * (self.result_polygons - self.source_polygons) / self.source_polygons
        )


def validate_settings(
    mesh_count: int, voxel_size: float, target_detail: float, mode: str = "REMESH"
) -> None:
    if mesh_count < 2:
        raise ValueError("Select at least two mesh objects.")
    if mode not in {"REMESH", "JOIN"}:
        raise ValueError("Mode must be REMESH or JOIN.")
    if mode == "JOIN":
        return
    if not 0.0001 <= voxel_size <= 1.0:
        raise ValueError("Voxel size must be between 0.0001 and 1.0 scene units.")
    if not 0.01 <= target_detail <= 1.0:
        raise ValueError("Target detail must be between 0.01 and 1.0.")


def summarize_meshes(source_polygons: list[int], result_polygons: int) -> MeshSummary:
    if any(count < 0 for count in source_polygons) or result_polygons < 0:
        raise ValueError("Polygon counts cannot be negative.")
    return MeshSummary(len(source_polygons), sum(source_polygons), result_polygons)
