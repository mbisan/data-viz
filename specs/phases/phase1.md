
The first phase involves creating the bones of the app's GUI:

- A tab-style layout for each chart.
- The first tab has a list of open datasources, and an sql editor.
  - Sidebar of the left.
    - The sidebar contains a button to load a file. For now only a placeholder.
  - SQL editor on the right. A button to "execute query". A button to "save as datasource".
  - Below the SQL editor, a collapsible table view of the results. A dropdown menu with buttons to save data to: clipboard, csv, json, excel.
- The chart tabs contain the following:
  - Sidebar with a selector of datasource and list of columns on the left.
  - Main view for the plot. Leave empty for now.

For this phase, implement only the layout.
