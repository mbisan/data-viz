Prepare loading and saving in yaml format.

A sample state is here:

```yaml
DATASOURCES:
  - name: 'segsocial_consolidado'
    type: 'LOCAL'
    source: 'test_data/segsocial_consolidado.parquet'
  - name: 'iris'
    type: 'LOCAL'
    source: 'test_data/iris.csv'
  - name: 'test_cases'
    type: 'LOCAL'
    source: 'test_data/test.csv'
  - name: 'agrupado'
    type: 'QUERY'
    source: |
      SELECT
        Fecha,
        Comunidad,
        Provincia,
        Origen,
        Origen2,
        SUM(IF(Tipo='Ingreso', Valor, NULL))/1e6 AS Ingreso,
        SUM(IF(Tipo='Gasto', Valor, NULL))/1e6 AS Gasto,
      FROM
        segsocial_consolidado
      GROUP BY 1, 2, 3, 4, 5
QUERIES:
  - name: 'Test Query'
    query: |
      SELECT
        *
      FROM
        segsocial_consolidado
  - name: 'Another Query'
    query: |
      SELECT DISTINCT
        Fecha
      FROM
        segsocial_consolidado
CHARTS:
```

The yaml file is loaded using AppState's methods:

def load_state(self, filename: str):
    pass

def save_state(self, filename: str):
    pass

The first loads the file into the state, and the second saves the current state to the filename.

Loading a file causes the state to reset (clean SQL context, clean queries, clean charts).

The actual loading (scan_parquet/scan_csv/read_excel) is moved into the Datasources add_datasource method, that drops the need of "data" parameter, since it loads it in place from "source".

- [] The yaml file is properly loaded into the state.
- [] The state is properly saved into the yaml file.
- [] The "+ Load File" button is now functional and the user is able to select and load files from disk (parquet/csv/excel)
