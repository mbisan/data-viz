"""UI Configuration, font management, and constants for data-viz."""

from typing import Optional, Any
from imgui_bundle import hello_imgui, imgui

DEBUG = True

# Window Settings
APP_TITLE = "data-viz"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

# Layout Dimensions
SIDEBAR_WIDTH = 250.0
MIN_SIDEBAR_WIDTH = 150.0
MAX_SIDEBAR_WIDTH = 600.0
DEFAULT_RESULTS_HEIGHT = 400.0
MIN_RESULTS_HEIGHT = 100.0
MAX_RESULTS_HEIGHT = 650.0
MIN_EDITOR_HEIGHT = 100.0

# Table results
MAX_UNPAGED_CELLS = 20_000
DEFAULT_PAGE_SIZE = 200
MAX_CELL_CHARS = 50

# Theme Settings
DEFAULT_THEME = hello_imgui.ImGuiTheme_.darcula


def apply_custom_style() -> None:
    """Apply styling tweaks for a modern and clean desktop UI."""
    style = imgui.get_style()

    # Rounded corners
    style.window_rounding = 6.0
    style.child_rounding = 4.0
    style.frame_rounding = 4.0
    style.popup_rounding = 4.0
    style.tab_rounding = 4.0
    style.scrollbar_rounding = 6.0
    style.grab_rounding = 4.0

    # Spacing and padding
    style.item_spacing = imgui.ImVec2(8.0, 6.0)
    style.item_inner_spacing = imgui.ImVec2(6.0, 4.0)
    style.frame_padding = imgui.ImVec2(8.0, 5.0)
    style.window_padding = imgui.ImVec2(10.0, 10.0)
    style.scrollbar_size = 12.0


def render_vertical_splitter(
    id_str: str,
    current_width: float,
    height: float = -1.0,
    min_w: float = MIN_SIDEBAR_WIDTH,
    max_w: float = MAX_SIDEBAR_WIDTH,
) -> float:
    """Render a draggable vertical splitter bar between two horizontal panels."""
    imgui.same_line(0.0, 0.0)
    imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(0.18, 0.20, 0.25, 0.35))
    imgui.push_style_color(imgui.Col_.button_active, imgui.ImVec4(0.35, 0.55, 0.85, 1.0))
    imgui.push_style_color(imgui.Col_.button_hovered, imgui.ImVec4(0.30, 0.50, 0.80, 0.7))

    imgui.button(f"##{id_str}", imgui.ImVec2(5.0, height))

    if imgui.is_item_active():
        current_width += imgui.get_io().mouse_delta.x
        if current_width < min_w:
            current_width = min_w
        if current_width > max_w:
            current_width = max_w

    if imgui.is_item_hovered() or imgui.is_item_active():
        imgui.set_mouse_cursor(imgui.MouseCursor_.resize_ew)

    imgui.pop_style_color(3)
    imgui.same_line(0.0, 0.0)
    return current_width


def render_horizontal_splitter(
    id_str: str,
    current_height: float,
    min_h: float = MIN_RESULTS_HEIGHT,
    max_h: float = MAX_RESULTS_HEIGHT,
) -> float:
    """Render a draggable horizontal splitter bar between SQL editor and results table."""
    imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(0.18, 0.20, 0.25, 0.35))
    imgui.push_style_color(imgui.Col_.button_active, imgui.ImVec4(0.35, 0.55, 0.85, 1.0))
    imgui.push_style_color(imgui.Col_.button_hovered, imgui.ImVec4(0.30, 0.50, 0.80, 0.7))

    imgui.button(f"##{id_str}", imgui.ImVec2(-1.0, 5.0))

    if imgui.is_item_active():
        # Dragging upwards increases table height, dragging downwards decreases it
        current_height -= imgui.get_io().mouse_delta.y
        if current_height < min_h:
            current_height = min_h
        if current_height > max_h:
            current_height = max_h

    if imgui.is_item_hovered() or imgui.is_item_active():
        imgui.set_mouse_cursor(imgui.MouseCursor_.resize_ns)

    imgui.pop_style_color(3)
    return current_height
