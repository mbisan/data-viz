The objective of this repository "data-viz" is to create a "Tableau clone" app that allows reading and exploring tables in parquet, csv, json and excel formats. It also allows executing SQL queries over them and generating simple graphs quickly.

The desired workflow for the app is the following:

- Load the file, once the table or tables are loaded, we will have one or several tables available.
- Data exploration: the column names, null counts and unique values, are cached for quick exploration.
- New columns: Using SQL.
- Aggregation: Using SQL, which turns into "new data sources".
- Plots: Only simple aggregation functions for graphics, SUM, MIN, MAX, AVG, COUNT(DISTINCT), etc, ...

The goal of the app is to be:

- Low on resources, non-web based
- Low on visualization configuration options
- Simple styles
- Storing results in plain text
- Prioritize speed, and that computations of shown values are explicit
