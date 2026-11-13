"""Main layout coordinator and tab bar handling for data-viz."""

from typing import Optional
from imgui_bundle import imgui
from gui.state import AppState
from gui.datasources import render_datasources_tab


def render_main_layout(state: AppState) -> None:
    tab_flags = imgui.TabBarFlags_.reorderable

    if imgui.begin_tab_bar("MainTabBar", tab_flags):
        if imgui.begin_tab_item_simple("Datasources"):
            render_datasources_tab(state)
            imgui.end_tab_item()

        chart_to_remove: Optional[int] = None

        for chart in state.charts.values():
            tab_label = f"{chart.name}###chart_tab_{chart.id}"
            selected, p_open = imgui.begin_tab_item(tab_label, p_open=True)

            if imgui.is_item_hovered() and imgui.is_mouse_double_clicked(imgui.MouseButton_.left):
                imgui.open_popup(f"RenameChartPopup_{chart.id}")

            if imgui.begin_popup(f"RenameChartPopup_{chart.id}"):
                imgui.text("Rename Chart:")
                changed, new_title = imgui.input_text("##tab_doubleclick_rename", chart.name)
                if changed and new_title.strip():
                    chart.name = new_title.strip()
                imgui.spacing()
                if imgui.button("OK", imgui.ImVec2(70.0, 0.0)) or imgui.is_key_pressed(imgui.Key.enter):
                    imgui.close_current_popup()
                imgui.same_line()
                if imgui.button("Cancel", imgui.ImVec2(70.0, 0.0)):
                    imgui.close_current_popup()
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
