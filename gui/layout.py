"""Main layout coordinator and tab bar handling for data-viz."""

from typing import Optional
from imgui_bundle import imgui
from gui.state import AppState
from gui.datasources import render_datasources_tab


def render_main_layout(state: AppState) -> None:
    io = imgui.get_io()
    ctrl_s = (
        io.key_ctrl and not io.key_shift and not io.key_alt
        and imgui.is_key_pressed(imgui.Key.s, False)
    )
    if ctrl_s:
        print('guardar main')

    tab_flags = imgui.TabBarFlags_.reorderable

    if imgui.begin_tab_bar("MainTabBar", tab_flags):
        if imgui.tab_item_button("File", imgui.TabItemFlags_.leading):
            imgui.open_popup("FileMenuPopup")

        btn_min = imgui.get_item_rect_min()
        btn_max = imgui.get_item_rect_max()
        imgui.set_next_window_pos(imgui.ImVec2(btn_min.x, btn_max.y))

        if imgui.begin_popup("FileMenuPopup"):
            clicked_open, _ = imgui.menu_item("Open...", "", False)
            if clicked_open:
                print('abrir')

            clicked_save, _ = imgui.menu_item("Save", "Ctrl+S", False)
            if clicked_save:
                print('guardar')

            imgui.end_popup()

        if imgui.begin_tab_item_simple("Datasources", flags=imgui.TabItemFlags_.no_reorder):
            render_datasources_tab(state)
            imgui.end_tab_item()

        chart_to_remove: Optional[int] = None

        for chart in state.charts.values():
            tab_label = f"{chart.name}###chart_tab_{chart.id}"
            selected, p_open = imgui.begin_tab_item(tab_label, p_open=True)

            if imgui.begin_popup_context_item(f"RenameChartPopup_{chart.id}"):
                imgui.text("Rename Chart:")
                changed, new_title = imgui.input_text("##tab_doubleclick_rename", chart.name)
                if changed and new_title.strip():
                    chart.name = new_title.strip()
                imgui.end_popup()

            if not p_open:
                chart_to_remove = chart.id

            if selected:
                imgui.end_tab_item()

        if chart_to_remove is not None:
            state.remove_chart(chart_to_remove)

        if imgui.tab_item_button("+", imgui.TabItemFlags_.trailing):
            state.add_chart()

        imgui.end_tab_bar()

    imgui.same_line()
    imgui.separator()

    status_msg = state.get_active_status()
    if status_msg:
        imgui.same_line()
        imgui.text_colored(imgui.ImVec4(0.35, 0.85, 0.45, 1.0), f"[OK] {status_msg}")
