Object Joiner 1.1

Overview

Object Joiner is a Blender addon designed to streamline the process of joining multiple objects into a single, optimized mesh. With customizable voxel size and target detail settings, you can control the level of detail and polygon count in the resulting mesh, making it ideal for both high-detail models and optimized, low-polygon versions.

Created by Given Borthwick
Features

    Customizable Voxel Size: Control the detail of the voxel remeshing process. Smaller values yield more detailed meshes but may increase computation time.
    Target Detail Control: Adjust the polygon count of the final mesh with a target detail parameter between 0 and 1.
    Hide Original Objects: Option to hide original objects after joining to keep your workspace clean.
    Easy Unhide Functionality: Quickly unhide original objects if needed.
    Automated Workflow: Duplicates selected objects, joins them, applies modifiers, and cleans up automatically.

Installation

    Download the Addon:
        Save the object_joiner.py script to a convenient location on your computer.

    Install via Blender:
        Open Blender.
        Navigate to Edit > Preferences.
        Click on the Add-ons tab.
        Click Install... at the top.
        Locate and select the downloaded object_joiner.py file.
        After installation, enable the addon by checking the box next to Object Joiner.

    Verify Installation:
        In the 3D Viewport, press N to open the sidebar.
        Navigate to the Object Joiner tab to access the addon’s interface.

Usage

    Select Objects:
        In the 3D Viewport, select the objects you wish to join.

    Open Object Joiner Panel:
        Press N to open the sidebar.
        Click on the Object Joiner tab.

    Configure Settings:
        Voxel Size (m): Set the desired voxel size. Smaller values create more detailed meshes but may increase computation time.
        Target Detail: Set a value between 0.01 and 1. Lower values reduce the polygon count of the final mesh.
        Hide Original Objects: Check this box if you want the original objects to be hidden after joining.

    Join Objects:
        Click the Join Objects button to execute the join operation.

    Unhide Original Objects (If Hidden):
        If you chose to hide the original objects, a Unhide Original Objects button will appear below the Join Objects button.
        Click Unhide Original Objects to restore the visibility of the original objects.

Additional Information

    Voxel Remeshing: Utilizes Blender’s Remesh modifier in voxel mode to create a unified mesh with controlled detail.
    Shrinkwrap Modifiers: Applied to ensure the joined mesh conforms to the original shapes before decimation.
    Decimation: Reduces the polygon count based on the target detail setting, optimizing the mesh for performance.

Troubleshooting

    Original Objects Still Hidden:
        Ensure that the Hide Original Objects option was enabled during the join operation.
        Use the Unhide Original Objects button in the Object Joiner panel.
        Alternatively, press Alt + H in the 3D Viewport to unhide all hidden objects.

    Addon Not Responding:
        Make sure that objects are selected before clicking the Join Objects button.
        Check Blender’s System Console for any error messages:
            Go to Window > Toggle System Console to view Blender's console output.

    Performance Issues:
        Be cautious with very small voxel sizes or very low target detail values, as they can significantly impact performance, especially with complex or numerous objects.

Contributing

Contributions are welcome! If you encounter bugs or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.
License

This project is licensed under the CC0 License.
Contact

Created by Given Borthwick

    Email: bgivenb@gmail.com
