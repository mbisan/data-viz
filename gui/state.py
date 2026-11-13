"""State management for the app."""

from dataclasses import dataclass, field
import time
from typing import List, Tuple, Dict, Optional
from imgui_bundle import imgui_color_text_edit as ed
from gui.config import DEFAULT_RESULTS_HEIGHT
from gui.helpers import create_sql_editor

import polars as pl


class DatasourceError(Exception):
    pass

class Datasources:
    sql_context: pl.SQLContext
    num_rows: int
    schemas: Dict[str, pl.Schema]

    def __init__(self, num_rows: int = 10000):
        self.sql_context = pl.SQLContext()
        self.num_rows = num_rows
        self.schemas = {}

    def add_datasource(self, name: str, data: pl.LazyFrame):
        self.sql_context.register(name, data)
        self.schemas[name] = data.collect_schema()

    def remove_datasource(self, name: str):
        self.sql_context.unregister(name)
        del self.schemas[name]

    def get_schema(self, name: str) -> pl.Schema:
        if name not in self.schemas:
            raise DatasourceError(f"There is no table named: {name}")
        return self.schemas[name]

    def get_schemas(self) -> Dict[str, pl.Schema]:
        return self.schemas

    def get_table_list(self) -> List[str]:
        return list(self.schemas.keys())

    def execute_query(self, query: str) -> Tuple[int, pl.DataFrame]:
        try:
            query_df = self.sql_context.execute(query)
            row_count = query_df.select(pl.len())
            row_count_result, query_df_result = pl.collect_all([row_count, query_df.limit(self.num_rows)])
        except pl.exceptions.SQLInterfaceError as e:
            raise DatasourceError(f"SQL syntax or schema error: {e}") from e
        except pl.exceptions.PolarsError as e:
            raise DatasourceError(f"Query execution failed: {e}") from e
        return row_count_result.item(), query_df_result

@dataclass
class QueryTab:
    id: int
    name: str
    result_dataframe: pl.DataFrame | None = None
    result_rows: int | None = None
    page: int = 0
    editor: ed.TextEditor = field(default_factory=create_sql_editor)

@dataclass
class ChartTab:
    id: int
    name: str
    selected_datasource: str | None = None
    sidebar_width: float = 250.0


class AppState:
    """Global application state containing datasources, queries, and charts."""

    def __init__(self) -> None:
        self.datasources: Datasources = Datasources()

        self.datasources.add_datasource(
            'segsocial_consolidado',
            pl.scan_parquet('test_data/segsocial_consolidado.parquet')
        )
        self.datasources.add_datasource(
            'iris',
            pl.scan_csv('test_data/iris.csv')
        )

        self.queries: Dict[int, QueryTab] = {}
        self.active_query_id: int = 0

        self.charts: Dict[int, ChartTab] = {}

        self.status_message: Optional[str] = None
        self.status_timestamp: float = 0.0

        # Persistent sizes
        self.results_collapsed: bool = False
        self.datasources_sidebar_width: float = 250.0
        self.results_height = DEFAULT_RESULTS_HEIGHT

    def set_status(self, message: str) -> None:
        self.status_message = message
        self.status_timestamp = time.time()

    def get_active_status(self) -> Optional[str]:
        if self.status_message and (time.time() - self.status_timestamp < 4.0):
            return self.status_message
        return None

    def add_query(self) -> QueryTab:
        new_id = max([0] + list(self.queries.keys())) + 1
        self.queries[new_id] = QueryTab(id=new_id, name=f"Query {new_id}")
        self.active_query_id = new_id
        return self.queries[new_id]

    def remove_query(self, query_id: int) -> None:
        if query_id in self.queries:
            del self.queries[query_id]
        if query_id == self.active_query_id:
            self.active_query_id = max([0] + [i for i in self.queries.keys()])

    def get_active_query(self) -> Optional[QueryTab]:
        if self.active_query_id in self.queries:
            return self.queries[self.active_query_id]

    def add_chart(self) -> ChartTab:
        new_id = max([0] + list(self.charts.keys())) + 1
        self.charts[new_id] = ChartTab(id=new_id, name=f"Chart {new_id}")
        return self.charts[new_id]

    def remove_chart(self, chart_id: int) -> None:
        if chart_id in self.charts:
            del self.charts[chart_id]
        self.set_status(f"Removed chart #{chart_id}")
