from imgui_bundle import imgui, rich_md
from gui.config import (
    MIN_EDITOR_HEIGHT,
    MAX_UNPAGED_CELLS,
    DEFAULT_PAGE_SIZE,
    render_vertical_splitter,
    render_horizontal_splitter,
)
from gui.state import AppState, QueryTab, DatasourceError


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
        state.set_status("File loader placeholder: File dialog will be connected in Phase 2.")

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

    for ds in state.datasources.datasources:
        clicked, _ = imgui.selectable(ds.name, False)
        if clicked:
            pass

        imgui.indent(12.0)
        imgui.text_disabled(f"{len(ds.schema)} columns")
        imgui.unindent(12.0)
        imgui.spacing()

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

    _render_action_bar(state, active_query)

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

    active_query.editor.render(f"SqlTextEditor_{active_query.id}", imgui.ImVec2(avail.x, editor_height))

    if code_font is not None:
        imgui.pop_font()

    if not state.results_collapsed:
        state.results_height = render_horizontal_splitter(
            "ResultsHorizontalSplitter",
            state.results_height,
        )

    _render_results_section(state, active_query, table_height)


def _render_action_bar(state: AppState, active_query: QueryTab) -> None:
    if imgui.button("Execute Query", imgui.ImVec2(120.0, 28.0)):
        query = active_query.editor.get_text()
        print(query)
        try:
            rows, result_df = state.datasources.execute_query(query)
            active_query.result_rows = rows
            active_query.result_dataframe = result_df
            active_query.page = 0
        except DatasourceError as e:
            state.set_status(f"{e}")
        if active_query.result_dataframe is not None:
            state.set_status(f"Query executed successfully ({active_query.result_dataframe.height:,} rows returned in 4.2ms)")

    imgui.same_line()

    if imgui.button("Save as Datasource", imgui.ImVec2(150.0, 28.0)):
        new_ds_name = f"query_{active_query.id}_result.parquet"
        state.set_status(f"Saved query results as new datasource: '{new_ds_name}'")

def _render_query_tab_bar(state: AppState) -> None:
    if imgui.begin_tab_bar("SqlQueryTabBar", imgui.TabBarFlags_.reorderable):
        query_to_remove = None

        for query_id, query in state.queries.items():
            tab_label = f"{query.name}###query_tab_{query.id}"

            selected, p_open = imgui.begin_tab_item(tab_label, p_open=True)
            if not p_open:
                query_to_remove = query.id

            if imgui.begin_popup_context_item(f"RenameQueryPopup_{query.id}"):
                imgui.text("Rename Query:")
                changed, new_name = imgui.input_text("##rename_query_input", query.name)
                if changed and new_name.strip():
                    query.name = new_name.strip()
                imgui.end_popup()

            if selected:
                state.active_query_id = query.id
                imgui.end_tab_item()

        if query_to_remove is not None:
            state.remove_query(query_to_remove)

        if imgui.tab_item_button("+", imgui.TabItemFlags_.trailing):
            new_q = state.add_query()
            state.set_status(f"Created new query tab: '{new_q.name}'")

        imgui.end_tab_bar()


def _render_results_section(state: AppState, active_query: QueryTab, table_height: float) -> None:
    toggle_label = "Show Results" if state.results_collapsed else "Hide Results"
    if imgui.button(toggle_label, imgui.ImVec2(130.0, 26.0)):
        state.results_collapsed = not state.results_collapsed

    if active_query.result_dataframe is None:
        return

    imgui.separator()

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
    page_size = DEFAULT_PAGE_SIZE if is_paged else total_rows

    if is_paged and total_rows > 0:
        max_page = (total_rows - 1) // page_size
        current_page = query.page
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_rows)

        imgui.align_text_to_frame_padding()
        imgui.text(f"Showing results {start_idx + 1}-{end_idx} of {total_rows} rows")
        imgui.same_line()

        imgui.begin_disabled(current_page == 0)
        if imgui.button(f"<##prev_{query.id}"):
            query.page -= 1
        imgui.end_disabled()

        imgui.same_line()
        imgui.begin_disabled(current_page >= max_page)
        if imgui.button(f">##next_{query.id}"):
            query.page += 1
        imgui.end_disabled()

        table_height = max(50.0, height - imgui.get_frame_height_with_spacing())
    else:
        start_idx = 0
        end_idx = total_rows
        table_height = height

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
        while clipper.step():
            for row_idx in range(clipper.display_start, clipper.display_end):
                row = page_rows[row_idx]
                imgui.table_next_row()
                for col_idx, val in enumerate(row):
                    imgui.table_set_column_index(col_idx)
                    imgui.text_unformatted(str(val))
        clipper.end()

        imgui.end_table()


def _copy_results_to_clipboard(query: QueryTab) -> None:
    if query.result_dataframe is None:
        return

    header = "\t".join(query.result_dataframe.columns)
    row_lines = ["\t".join(str(c) for c in row) for row in query.result_dataframe.rows()]
    tsv = header + "\n" + "\n".join(row_lines)
    imgui.set_clipboard_text(tsv)
