# **Reusable UI Components in QGIS Earth Engine Plugin**

The plugin provides utility functions in `ui/utils.py` to simplify UI creation in QGIS. These functions help construct structured, reusable components for dialogs and form layouts.

## **UI Utility Functions**

### **1. `build_form_group_box(title, rows, collapsable=False, collapsed=False)`**
Creates a labeled section containing form inputs.

- `title` *(str)* – The title of the group box.
- `rows` *(list of tuples)* – Each tuple represents a (label, widget) pair.
- `collapsable` *(bool, optional)* – Allows collapsing the section.
- `collapsed` *(bool, optional)* – Sets the default collapsed state.

### **2. `build_vbox_dialog(windowTitle, widgets, accepted, rejected)`**
Creates a vertically stacked dialog.

- `windowTitle` *(str)* – Title of the dialog.
- `widgets` *(list)* – A list of UI components to include.
- `accepted` *(function)* – Callback executed when confirmed.
- `rejected` *(function)* – Callback executed when canceled.

### **3. `get_values(dialog)`**
Extracts user inputs from a dialog.

- `dialog` – The dialog instance.
- **Returns** a dictionary mapping object names to user inputs.

## **Usage in Plugin Development**
To create a new UI component:
1. **Define the form** using `build_form_group_box()`.
2. **Wrap it inside a dialog** using `build_vbox_dialog()`.
3. **Retrieve user inputs** with `get_values(dialog)`.
4. **Integrate with plugin actions** via `initGui()`.

This approach ensures consistency and modularity in UI development.