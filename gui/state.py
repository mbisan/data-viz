"""State management for the app."""

from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import List, Tuple, Dict, Optional, Any
import yaml
from imgui_bundle import imgui_color_text_edit as ed
from gui.config import DEFAULT_RESULTS_HEIGHT, DEBUG
from gui.helpers import create_sql_editor

import polars as pl


class DatasourceError(Exception):
    pass

class FileLoadError(Exception):
    pass

@dataclass
class DataSource:
    name: str
    height: int
    frame: pl.LazyFrame
    schema: pl.Schema
    type: str
    source: str
    show_columns: bool = False

class Datasources:
    sql_context: pl.SQLContext
    num_rows: int
    datasources: List[DataSource]

    def __init__(self, num_rows: int = 10000):
        self.sql_context = pl.SQLContext()
        self.num_rows = num_rows
        self.datasources = []

    def get_table_list(self) -> List[str]:
        return [ds.name for ds in self.datasources]

    def add_datasource(self, name: str, type: str, source: str):
        if name in self.get_table_list():
            self.remove_datasource(name)
        try:
            data: pl.LazyFrame | None = None
            if type == 'QUERY':
                data = self.sql_context.execute(source)
            else: # load local file
                if source.endswith('.parquet'):
                    data = pl.scan_parquet(source)
                elif source.endswith('.csv'):
                    data = pl.scan_csv(source)

            if data is None:
                raise DatasourceError(f"Could not load {source}")

            new_datasource = DataSource(
                name,
                data.select(pl.len()).collect().item(),
                data,
                data.collect_schema(),
                type,
                source
            )
        except pl.exceptions.SQLInterfaceError as e:
            raise DatasourceError(f"SQL syntax or schema error: {e}") from e
        except pl.exceptions.PolarsError as e:
            raise DatasourceError(f"Query execution failed: {e}") from e
        self.datasources.append(new_datasource)
        self.sql_context.register(name, data)

    def remove_datasource(self, name: str):
        idx = next((i for i, ds in enumerate(self.datasources) if ds.name == name), None)
        if idx is None:
            raise DatasourceError(f"There is no table named: {name}")

        dependent = []
        for ds in self.datasources:
            if name in ds.source and name!=ds.name:
                dependent.append(ds.name)
        if len(dependent)>0:
            raise DatasourceError(f"These tables depend on {name}: {dependent}")

        self.sql_context.unregister(name)
        del self.datasources[idx]

    def get_schema(self, name: str) -> pl.Schema:
        match_df = next((ds for ds in self.datasources if ds.name == name), None)
        if match_df is None:
            raise DatasourceError(f"There is no table named: {name}")
        return match_df.schema

    def get_schemas(self) -> Dict[str, pl.Schema]:
        return {ds.name: ds.schema for ds in self.datasources}

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
    result_error: str | None = None
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

        self.queries: Dict[int, QueryTab] = {}

        self.active_query_id: int = 0
        self.pending_select_query_id: int | None = None
        self.pending_delete_query_id: int | None = None
        self.open_delete_popup: bool = False
        self.save_ds_name: str = ""

        self.charts: Dict[int, ChartTab] = {}

        self.status_message: Optional[str] = None
        self.status_timestamp: float = 0.0

        # Persistent sizes
        self.results_collapsed: bool = False
        self.datasources_sidebar_width: float = 250.0
        self.results_height = DEFAULT_RESULTS_HEIGHT

        self.file_dialog: Any = None
        self.files_to_process: list[str] = []
        self.files_to_process_popup_open: bool = False

        if DEBUG:
            self.load_state("test_data/state.data-viz")

    def load_state(self, filename: str):
        try:
            with open(filename, "r") as f:
                dict_state = yaml.safe_load(f.read())
        except Exception as e:
            raise FileLoadError(f"Something went wrong while loading {filename}: {str(e)}")

        schemas = {
            'DATASOURCES': ["name", "type", "source"],
            'QUERIES': ["name", "query"]
        }

        for key, key_list in schemas.items():
            values = dict_state.get(key, [])
            if isinstance(values, list):
                for ds in values:
                    for k in key_list:
                        if k not in ds:
                            raise FileLoadError(f"Some {key} are missing the {k}.")

        if isinstance(dict_state.get("DATASOURCES", []), list):
            for ds in dict_state.get("DATASOURCES", []):
                self.datasources.add_datasource(ds["name"], ds["type"], ds["source"])
        if isinstance(dict_state.get("QUERIES", []), list):
            for ds in dict_state.get("QUERIES", []):
                self.add_query(ds["query"], ds["name"])
        if isinstance(dict_state.get("CHARTS", []), list):
            for ds in dict_state.get("CHARTS", []): # TODO
                self.add_chart()

    def save_state(self, filename: str):
        pass

    def set_status(self, message: str) -> None:
        self.status_message = message
        self.status_timestamp = time.time()

    def get_active_status(self) -> Optional[str]:
        if self.status_message and (time.time() - self.status_timestamp < 4.0):
            return self.status_message
        return None

    def add_query(self, default_query: str="", query_name: str | None = None) -> QueryTab:
        new_id = max([0] + list(self.queries.keys())) + 1
        if query_name is None:
            query_name = f"Query {new_id}"
        self.queries[new_id] = QueryTab(id=new_id, name=query_name)
        self.queries[new_id].editor.set_text(default_query)
        self.active_query_id = new_id
        self.pending_select_query_id = new_id
        return self.queries[new_id]

    def remove_query(self, query_id: int) -> None:
        if query_id in self.queries:
            del self.queries[query_id]
        if query_id == self.active_query_id:
            self.active_query_id = max([0] + [i for i in self.queries.keys()])
            self.pending_select_query_id = self.active_query_id

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
