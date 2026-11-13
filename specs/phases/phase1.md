
The first phase involves creating the bones of the app's GUI:

- Primary window: a full view container.
  - A tab-style layout for each chart.
  - By default two tabs: "Datasources" and "Chart 1", with a button to add new charts. The chart names can be changed.
- The "Datasources" tab has a list of open datasources, and an sql editor.
  - Sidebar of the left.
    - The sidebar contains a button to load a file. For now only a placeholder.
    - The list extends to the bottom of the view.
  - SQL editor on the right. A button to "execute query". A button to "save as datasource". The SQL editor has tabs (same as the viewport) and a + button to add a new empty query.
    - The SQL editor comes from the package: imgui-bundle.
  - Below the SQL editor, a collapsible table view of the results. A dropdown menu with buttons to save data to: clipboard, csv, json, excel.
    - When collapsed, the table view is placed on the bottom of the view. (i.e. it opens from the bottom).
    - The SQL editor occupies the full view when the table view is collapsed.
    - The table columns occupy the column names, adjusted, and do not extend the full width. If there are enough columns, a horizontal sidebar allows viewing the rest of the columns.
    - The save data button goes on the right side, the toggle view button on the left. Next to the save data button an indicator of total row numbers appears.
- The chart tabs contain the following:
  - Sidebar with a selector of datasource and list of columns on the left.
  - Main view for the plot. Leave empty for now.

This phase focuses strictly on layout, visual hierarchy, and component placement—no backend data processing or Polars queries are wired up yet.

Code & Package Organization
- `main.py`: Entry point setting up Dear PyGui viewport, initializing the UI, and running the render loop.
- `gui/`:
  - `gui/layout.py`: Main window, tab bar coordinator, and dynamic `+` tab handling.
  - `gui/datasources.py`: Layout components for the "Datasources" tab.
  - `gui/chart.py`: Layout components for chart tabs.
  - `gui/config.py`: UI constants.

Tasks:

- [ ] Application starts cleanly via `uv run python main.py` and opens a styled Dear PyGui window.
- [ ] "Datasources" tab displays sidebar (Load File button + Datasource list), SQL editor, Action buttons, and collapsible Results preview with export options.
- [ ] Default "Chart 1" tab is present with a datasource picker, column list sidebar, and empty plot area.
- [ ] Clicking the `+` button creates a new chart tab.
- [ ] Window resizes cleanly.
