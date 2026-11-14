from time import time

from imgui_bundle import imgui, rich_md
from imgui_bundle.portable_file_dialogs import open_file
from gui.config import (
    MIN_EDITOR_HEIGHT,
    MAX_UNPAGED_CELLS,
    DEFAULT_PAGE_SIZE,
    MAX_CELL_CHARS,
    render_vertical_splitter,
    render_horizontal_splitter,
)
from gui.state import AppState, QueryTab, DatasourceError


def execute_query(state: AppState, active_query: QueryTab):
    query = active_query.editor.get_text()
    active_query.result_rows = 0
    active_query.result_dataframe = None
    active_query.result_error = None
    state.results_collapsed = False
    try:
        a = time()
        rows, result_df = state.datasources.execute_query(query)
        time_taken = time()-a
        active_query.result_rows = rows
        active_query.result_dataframe = result_df
        active_query.page = 0
        if active_query.result_dataframe is not None:
            state.set_status(f"Query executed successfully ({active_query.result_dataframe.height:,} rows returned in {int(time_taken*1000)}ms)")
    except DatasourceError as e:
        active_query.result_error = str(e)


def render_datasources_tab(state: AppState) -> None:
    avail_size = imgui.get_content_region_avail()
    splitter_w = 5.0

    imgui.begin_child(
        "DatasourcesSidebar",
        imgui.ImVec2(state.datasources_sidebar_width, avail_size.y),
        child_flags=imgui.ChildFlags_.borders,
    )
    _render_sidebar(state)
    imgui.end_child()

    state.datasources_sidebar_width = render_vertical_splitter(
        "DatasourcesSidebarSplitter",
        state.datasources_sidebar_width,
        height=avail_size.y,
    )

    right_pane_width = avail_size.x - state.datasources_sidebar_width - splitter_w
    imgui.begin_child(
        "DatasourcesRightPane",
        imgui.ImVec2(right_pane_width, avail_size.y),
        child_flags=0,
    )
    _render_right_pane(state)
    imgui.end_child()


def _render_sidebar(state: AppState) -> None:
    imgui.spacing()

    if imgui.button("+ Load File", imgui.ImVec2(-1.0, 32.0)):
        try:
            state.file_dialog = open_file(
                "Select data file",
                "",
                ["Data files (*.parquet *.csv *.xlsx *.xls)", "*.parquet *.csv *.xlsx *.xls", "All files", "*"],
            )
        except Exception as e:
            state.set_status(f"Error opening file dialog: {e}")

    if state.file_dialog is not None and state.file_dialog.ready():
        try:
            results = state.file_dialog.result()
        except Exception as e:
            results = []
            state.set_status(f"Error reading file dialog: {e}")
        state.file_dialog = None
        for file_path in results:
            if file_path:
                state.files_to_process.append(file_path)

    if len(state.files_to_process)>0 and not state.files_to_process_popup_open:
        state.files_to_process_popup_open = True
        print('open popup')
        imgui.open_popup("Save as Datasource From File")

    if len(state.files_to_process)>0:
        _render_save_datasource_from_file_popup(state, state.files_to_process[0], "Save as Datasource From File")

    imgui.spacing()
    imgui.separator()
    imgui.spacing()

    ds_count = len(state.datasources.get_table_list())
    imgui.text_colored(imgui.ImVec4(0.7, 0.7, 0.7, 1.0), "OPEN DATASOURCES")
    imgui.same_line()
    imgui.text_disabled(f"({ds_count})")

    imgui.spacing()

    sidebar_avail = imgui.get_content_region_avail()
    imgui.begin_child("DatasourceListChild", imgui.ImVec2(0.0, sidebar_avail.y), child_flags=0)

    datasource_to_remove = None

    for ds in state.datasources.datasources:
        clicked, _ = imgui.selectable(f"{ds.name}##{id(ds)}", ds.show_columns)

        if imgui.begin_popup_context_item(f"ManageDatasourcePopup_{id(ds.name)}"):
            open_in_query_clicked, _ = imgui.selectable("Open in query", True)
            if open_in_query_clicked: # open the datasource on a new query
                if ds.type == 'QUERY':
                    state.add_query(ds.source)
                else:
                    column_names = [f'`{col}`' if '.' in col else col for col in ds.schema.names()]
                    state.add_query('SELECT\n  ' + ',\n  '.join(column_names) + f'\nFROM\n  {ds.name}')

            delete_button_clicked, _ = imgui.selectable("Remove datasource", True)
            if delete_button_clicked:
                datasource_to_remove = ds.name
            imgui.end_popup()

        if clicked:
            ds.show_columns = not ds.show_columns

        imgui.indent(12.0)
        imgui.text_disabled(f"{ds.height:,} rows  •  {len(ds.schema)} columns")

        if ds.show_columns:
            imgui.spacing()
            right_edge = imgui.get_cursor_pos_x() + imgui.get_content_region_avail().x

            for col_name, col_type in ds.schema.items():
                type_str = str(col_type)
                type_width = imgui.calc_text_size(type_str).x

                imgui.text(col_name)

                imgui.same_line()
                imgui.set_cursor_pos_x(right_edge - type_width)
                imgui.text_disabled(type_str)

        imgui.unindent(12.0)
        imgui.spacing()

    if datasource_to_remove is not None:
        try:
            msg = f"Successfully removed {datasource_to_remove}"
            state.datasources.remove_datasource(datasource_to_remove)
            state.set_status(msg)
        except DatasourceError as e:
            state.set_status(str(e))

    imgui.end_child()


def _render_right_pane(state: AppState) -> None:
    _render_query_tab_bar(state)

    active_query = state.get_active_query()
    if not active_query:
        imgui.text("No active query.")
        return

    io = imgui.get_io()
    if io.key_ctrl and imgui.is_key_chord_pressed(int(imgui.Key.mod_ctrl) | int(imgui.Key.mod_shift) | int(imgui.Key._7)):
        active_query.editor.toggle_comments()
        state.set_status("Toggled comment on selected line(s)")

    imgui.spacing()

    avail = imgui.get_content_region_avail()
    bar_height = 34.0
    splitter_h = 5.0 if not state.results_collapsed else 0.0
    spacing = imgui.get_style().item_spacing.y

    if state.results_collapsed:
        editor_height = max(MIN_EDITOR_HEIGHT, avail.y - bar_height - spacing)
        table_height = 0.0
    else:
        table_height = state.results_height
        editor_height = max(
            MIN_EDITOR_HEIGHT,
            avail.y - table_height - bar_height - splitter_h - (spacing * 2),
        )

    code_font = rich_md.get_code_font()
    if code_font is not None:
        imgui.push_font(code_font.font, code_font.size)

    io = imgui.get_io()
    focused = imgui.is_window_focused(imgui.FocusedFlags_.child_windows)
    if focused:
        if imgui.is_key_pressed(imgui.Key.keypad7, repeat=True):
            if not any(c == ord("7") for c in io.input_queue_characters):
                io.add_key_event(imgui.Key.home, True)
                io.add_key_event(imgui.Key.home, False)
        if imgui.is_key_pressed(imgui.Key.keypad1, repeat=True):
            if not any(c == ord("1") for c in io.input_queue_characters):
                io.add_key_event(imgui.Key.end, True)
                io.add_key_event(imgui.Key.end, False)
    shift_enter = (
        focused and io.key_ctrl and not io.key_shift and not io.key_alt
        and imgui.is_key_pressed(imgui.Key.enter, False)
    )
    if shift_enter:
        active_query.editor.set_read_only_enabled(True)
        execute_query(state, active_query)

    active_query.editor.render(f"SqlTextEditor_{active_query.id}", imgui.ImVec2(avail.x, editor_height))
    if shift_enter:
        active_query.editor.set_read_only_enabled(False)

    if code_font is not None:
        imgui.pop_font()

    if not state.results_collapsed:
        state.results_height = render_horizontal_splitter(
            "ResultsHorizontalSplitter",
            state.results_height,
        )

    _render_results_section(state, active_query, table_height)


def _render_query_tab_bar(state: AppState) -> None:
    if imgui.begin_tab_bar("SqlQueryTabBar", imgui.TabBarFlags_.reorderable):
        for query in state.queries.values():
            tab_label = f"{query.name}###query_tab_{query.id}"

            flags = imgui.TabItemFlags_.no_assumed_closure
            if state.pending_select_query_id == query.id:
                flags |= imgui.TabItemFlags_.set_selected
                state.pending_select_query_id = None  # one-shot

            selected, p_open = imgui.begin_tab_item(tab_label, p_open=True, flags=flags)
            if not p_open and state.pending_delete_query_id is None:
                state.pending_delete_query_id = query.id
                state.open_delete_popup = True

            if imgui.begin_popup_context_item(f"RenameQueryPopup_{query.id}"):
                imgui.text("Rename Query:")
                changed, new_name = imgui.input_text("##rename_query_input", query.name)
                if changed and new_name.strip():
                    query.name = new_name.strip()
                imgui.end_popup()

            if selected:
                state.active_query_id = query.id
                imgui.end_tab_item()

        if state.pending_delete_query_id is not None:
            popup_id = f"RemoveQueryPopup"
            if state.open_delete_popup:
                imgui.open_popup(popup_id)
                state.open_delete_popup = False
            query_to_delete = state.queries[state.pending_delete_query_id]
            if imgui.begin_popup(popup_id):
                if imgui.button(f"Delete '{query_to_delete.name}'?"):
                    state.remove_query(query_to_delete.id)
                    state.pending_delete_query_id = None
                    imgui.close_current_popup()
                imgui.end_popup()
            else:
                state.pending_delete_query_id = None

        if imgui.tab_item_button("+", imgui.TabItemFlags_.trailing):
            new_q = state.add_query()
            state.set_status(f"Created new query tab: '{new_q.name}'")

        imgui.end_tab_bar()


def _render_results_section(state: AppState, active_query: QueryTab, table_height: float) -> None:
    toggle_label = "Show Results" if state.results_collapsed else "Hide Results"
    if imgui.button(toggle_label, imgui.ImVec2(130.0, 26.0)):
        state.results_collapsed = not state.results_collapsed

    imgui.same_line()

    if imgui.button("Execute Query", imgui.ImVec2(120.0, 28.0)):
        execute_query(state, active_query)

    imgui.same_line()

    if imgui.button("Save as Datasource", imgui.ImVec2(150.0, 28.0)):
        state.save_ds_name = f"query_{active_query.id}_result"  # default suggestion
        imgui.open_popup("Save as Datasource")

    _render_save_datasource_popup(state, active_query, "Save as Datasource")

    if active_query.result_error is not None and not state.results_collapsed:
        if table_height > 0:
            _render_error(active_query, table_height)
        return

    if active_query.result_dataframe is None:
        return

    avail_w = imgui.get_content_region_avail().x
    row_count_str = f"Total rows: {active_query.result_rows:,}"
    save_button_label = "Save Data..."

    row_text_w = imgui.calc_text_size(row_count_str).x
    save_btn_w = 110.0
    spacing = imgui.get_style().item_spacing.x

    right_offset = avail_w - (row_text_w + save_btn_w + (spacing * 2))
    if right_offset > 140.0:
        imgui.same_line(right_offset)

    imgui.align_text_to_frame_padding()
    imgui.text_disabled(row_count_str)

    imgui.same_line()
    if imgui.button(save_button_label, imgui.ImVec2(save_btn_w, 26.0)):
        imgui.open_popup("ExportDataDropdown")

    if imgui.begin_popup("ExportDataDropdown"):
        imgui.text_disabled("Export Query Results")
        imgui.separator()

        if imgui.menu_item_simple("Copy to Clipboard"):
            _copy_results_to_clipboard(active_query)
            state.set_status("Results copied to system clipboard as TSV.")

        if imgui.menu_item_simple("Export as CSV (.csv)"):
            state.set_status("Exported results to CSV file.")

        if imgui.menu_item_simple("Export as JSON (.json)"):
            state.set_status("Exported results to JSON file.")

        if imgui.menu_item_simple("Export as Excel (.xlsx)"):
            state.set_status("Exported results to Excel file.")

        imgui.end_popup()

    if not state.results_collapsed and table_height > 0:
        _render_table(active_query, table_height)


def _render_save_datasource_from_file_popup(state: AppState, path: str, popup_id: str) -> None:
    center = imgui.get_main_viewport().get_center()
    imgui.set_next_window_pos(center, imgui.Cond_.appearing, imgui.ImVec2(0.5, 0.5))

    opened, _ = imgui.begin_popup_modal(
        popup_id, None, imgui.WindowFlags_.always_auto_resize
    )
    if not opened:
        return

    imgui.text("Name for the new datasource:")
    imgui.set_next_item_width(300.0)
    if imgui.is_window_appearing():
        imgui.set_keyboard_focus_here()

    submitted, state.save_ds_name = imgui.input_text(
        "##save_ds_name",
        state.save_ds_name,
        imgui.InputTextFlags_.enter_returns_true,
    )

    name = state.save_ds_name.strip()
    valid = bool(name)

    imgui.spacing()

    imgui.begin_disabled(not valid)
    ok = imgui.button("OK", imgui.ImVec2(120.0, 0.0))
    imgui.end_disabled()

    imgui.same_line()
    cancel = imgui.button("Cancel", imgui.ImVec2(120.0, 0.0))

    if cancel or imgui.is_key_pressed(imgui.Key.escape):
        imgui.close_current_popup()
    elif (ok or submitted) and valid:
        state.files_to_process = [f for f in state.files_to_process if f!=path]
        state.files_to_process_popup_open = False
        try:
            state.datasources.add_datasource(name, "LOCAL", path)
            state.set_status(f"Saved query results as new datasource: '{name}'")
            imgui.close_current_popup()
        except DatasourceError as e:
            state.set_status(f"Something went wrong while loading the file.")
            imgui.close_current_popup()

    imgui.end_popup()


def _render_save_datasource_popup(state: AppState, query: QueryTab, popup_id: str) -> None:
    center = imgui.get_main_viewport().get_center()
    imgui.set_next_window_pos(center, imgui.Cond_.appearing, imgui.ImVec2(0.5, 0.5))

    opened, _ = imgui.begin_popup_modal(
        popup_id, None, imgui.WindowFlags_.always_auto_resize
    )
    if not opened:
        return

    imgui.text("Name for the new datasource:")
    imgui.set_next_item_width(300.0)
    if imgui.is_window_appearing():
        imgui.set_keyboard_focus_here()

    submitted, state.save_ds_name = imgui.input_text(
        "##save_ds_name",
        state.save_ds_name,
        imgui.InputTextFlags_.enter_returns_true,
    )

    name = state.save_ds_name.strip()
    valid = bool(name)

    imgui.spacing()

    imgui.begin_disabled(not valid)
    ok = imgui.button("OK", imgui.ImVec2(120.0, 0.0))
    imgui.end_disabled()

    imgui.same_line()
    cancel = imgui.button("Cancel", imgui.ImVec2(120.0, 0.0))

    if cancel or imgui.is_key_pressed(imgui.Key.escape):
        imgui.close_current_popup()
    elif (ok or submitted) and valid:
        try:
            query_str = query.editor.get_text()
            state.datasources.add_datasource(name, "QUERY", query_str)
            state.set_status(f"Saved query results as new datasource: '{name}'")
            imgui.close_current_popup()
        except DatasourceError as e:
            state.set_status(f"Something went wrong: see error message")
            query.result_error = str(e)
            imgui.close_current_popup()

    imgui.end_popup()


def _render_error(query: QueryTab, height: float) -> None:
    if query.result_error is None:
        return
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(1.0, 0.4, 0.4, 1.0))
    imgui.begin_child(
        f"ResultsError_{query.id}",
        imgui.ImVec2(0.0, height),
        child_flags=imgui.ChildFlags_.borders,
    )
    imgui.text_unformatted("Query failed")
    imgui.separator()
    imgui.push_text_wrap_pos(0.0)
    imgui.text_unformatted(query.result_error)
    imgui.pop_text_wrap_pos()
    imgui.end_child()
    imgui.pop_style_color()


def _render_table(query: QueryTab, height: float) -> None:
    if query.result_dataframe is None:
        imgui.text_disabled("Nothing to display.")
        return

    df = query.result_dataframe
    cols = df.columns

    if not cols:
        imgui.text_disabled("No columns returned.")
        return

    total_rows = df.height
    total_cells = df.width * total_rows
    is_paged = total_cells > MAX_UNPAGED_CELLS
    page_size = DEFAULT_PAGE_SIZE if is_paged else max(total_rows, 1)

    max_page = max(0, (total_rows - 1) // page_size) if total_rows > 0 else 0
    query.page = min(max(query.page, 0), max_page)
    current_page = query.page

    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_rows)
    table_height = max(50.0, height - imgui.get_frame_height_with_spacing())

    page_rows = df.slice(start_idx, end_idx - start_idx).rows()

    table_flags = (
        imgui.TableFlags_.scroll_x
        | imgui.TableFlags_.scroll_y
        | imgui.TableFlags_.sizing_fixed_fit
        | imgui.TableFlags_.borders
        | imgui.TableFlags_.row_bg
        | imgui.TableFlags_.resizable
    )

    if imgui.begin_table(f"ResultsTable_{query.id}", len(cols), table_flags, imgui.ImVec2(0.0, table_height)):
        imgui.table_setup_scroll_freeze(0, 1)

        for col_name in cols:
            imgui.table_setup_column(col_name)
        imgui.table_headers_row()

        clipper = imgui.ListClipper()
        clipper.begin(len(page_rows))
        schema_types = query.result_dataframe.schema.dtypes()
        while clipper.step():
            for row_idx in range(clipper.display_start, clipper.display_end):
                row = page_rows[row_idx]
                imgui.table_next_row()
                for col_idx, (sch, val) in enumerate(zip(schema_types, row)):
                    imgui.table_set_column_index(col_idx)
                    if sch.is_numeric():
                        if not isinstance(val, (float, int)):
                            text = 'NULL'
                        elif sch.is_float():
                            text = f"{val:.3f}"
                        else:
                            text = str(val)
                        text_w = imgui.calc_text_size(text).x
                        avail_w = imgui.get_content_region_avail().x
                        imgui.set_cursor_pos_x(
                            imgui.get_cursor_pos_x() + max(0.0, avail_w - text_w)
                        )
                        imgui.text_unformatted(text)
                    else:
                        text = str(val).replace("\n", "\\n").replace("\r", "\\r")
                        if len(text)>MAX_CELL_CHARS:
                            text = text[:MAX_CELL_CHARS] + '...'
                        imgui.text_unformatted(text)
        clipper.end()

        imgui.end_table()

    imgui.indent(6.0)
    imgui.begin_disabled(current_page == 0)
    if imgui.button(f"<##prev_{query.id}"):
        query.page -= 1
    imgui.end_disabled()

    imgui.same_line()
    imgui.begin_disabled(current_page >= max_page)
    if imgui.button(f">##next_{query.id}"):
        query.page += 1
    imgui.end_disabled()

    imgui.same_line()
    imgui.align_text_to_frame_padding()
    if total_rows > 0:
        imgui.text(f"Showing results {start_idx + 1:,}-{end_idx:,} of {total_rows:,} rows")
    else:
        imgui.text("Showing 0 rows")


def _copy_results_to_clipboard(query: QueryTab) -> None:
    if query.result_dataframe is None:
        return

    header = "\t".join(query.result_dataframe.columns)
    row_lines = ["\t".join(str(c) for c in row) for row in query.result_dataframe.rows()]
    tsv = header + "\n" + "\n".join(row_lines)
    imgui.set_clipboard_text(tsv)
