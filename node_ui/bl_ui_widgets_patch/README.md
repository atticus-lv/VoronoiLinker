# Blender UI Widgets
Addon with UI Widgets for a persistent (modal) draggable floating panel, textboxes, checkboxes, buttons and sliders for Blender 2.8 and newer versions.

The panel can __stay open__ all the time in the 3D viewport during mesh editing.  It is not only some kind of popup panel, it persists opened like the side bar or Blender's native N-Panel.

Each widget object has many attributes that can be set by the programmer to customize its appearance and behavior.  One can opt to let the widgets automatically take the appearance of the selected Blender's Theme or can override any of the characteristics individually, and per widget.

The widgets are also fully scalable, bound to Blender's Resolution Scale configuration ("ui_scale") and/or by programmer's customization.  It is also ready to get tied to an Addon Preferences setup page, as can be seen in this demo panel.

Not much documentation is available for now, but the code has a lot of annotations to help you out and each module has its mod log listing all added features.  Also, at each module's init method you can find all available attributes described with detailed information.

The GPU module of Blender 2.8 is used for drawing.  This package has a demo panel to showcase all available widgets so that you can install it and have a quick testing.  It also serves as a template or a baseline for creating __your own addons__.  I attempted to add a little bit of each feature to the demo code in order to help starters.  Below follows some images taken from the demo panel itself.

## Sample of the demo panel in the viewport
![Viewport sample](https://github.com/mmmrqs/media/blob/main/Suzanne.png)

## Example of an Addon that uses these widgets
![ReferenceCameras](https://github.com/mmmrqs/media/blob/main/RCameras.png)
https://github.com/mmmrqs/Blender-Reference-Camera-Panel-addon

## Widgets appearance
![Widgets](https://github.com/mmmrqs/media/blob/main/widgets.png)

## A sneak peek at button's attributes
![Code sample](https://github.com/mmmrqs/media/blob/main/code.png)

## Classes relationships for the BL_UI_Widgets
![BL_UI_Widgets UML](https://github.com/mmmrqs/media/blob/main/Classes_UML2.png)
