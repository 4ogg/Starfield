# Starfield Generator Blender Add-on

This repository contains a Blender add-on that procedurally builds a dense, high-quality star field that is suitable for still renders or animated fly-throughs. The add-on focuses on realism by scattering emissive star meshes through a spherical volume with natural variation in size, colour and brightness.

## Features

- Generate thousands of stars distributed through a configurable spherical volume.
- Automatically builds a material that uses random per-object values to vary colour and brightness for a natural look.
- Reproducible output via a user-controlled random seed.
- Easy-to-use panel in the 3D Viewport sidebar, allowing quick tweaking and regeneration.

## Installation

1. Download or clone this repository.
2. In Blender, open **Edit → Preferences… → Add-ons**.
3. Press **Install…** and select the `starfield_generator` folder (or create a ZIP of the folder and select that ZIP file).
4. Enable **Procedural Starfield Generator** in the add-on list.

Once enabled, the add-on registers itself automatically. Updates to the add-on can be installed by repeating the steps above.

## Usage

1. Open the 3D Viewport and press **N** to show the sidebar if it is hidden.
2. Switch to the **Starfield** tab that the add-on adds to the sidebar.
3. Adjust the generation parameters:
   - **Collection** and **Clear Existing** control where the stars live and whether previous stars are removed.
   - **Star Count**, **Field Radius**, and **Random Seed** determine the overall layout and reproducibility.
   - **Min/Max Star Size** define the size range for the stars.
   - **Base Brightness** and **Brightness Variation** tune the emission material.
4. Click **Generate Star Field**. A new collection (default name `Starfield`) containing the generated stars will appear.

The stars are standard mesh objects that share a single emissive material. You can render stills or animations using any render engine that supports emission shaders (Cycles and Eevee both work well). The generated collection can also be duplicated or instanced to create layered star fields for parallax effects.

## Rendering Tips

- Combine the generated stars with volumetric fog or nebula geometry for deeper space scenes.
- Increase **Star Count** and **Brightness Variation** for dense Milky Way-style backgrounds, or decrease them for sparse interstellar space.
- Animate the camera through the star field to create convincing fly-throughs; the add-on's spherical distribution avoids obvious planar parallax issues.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) (if provided) for details.
