from imgui_bundle import hello_imgui, immapp
from gui.config import (
    APP_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    DEFAULT_THEME,
    apply_custom_style,
)
from gui.state import AppState
from gui.layout import render_main_layout


def main() -> None:
    # Initialize application state
    state = AppState()

    runner_params = hello_imgui.RunnerParams()
    runner_params.app_window_params.window_title = APP_TITLE
    runner_params.app_window_params.window_geometry.size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    runner_params.app_window_params.restore_previous_geometry = True

    runner_params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window
    )
    runner_params.imgui_window_params.show_menu_bar = False
    runner_params.imgui_window_params.show_status_bar = False
    runner_params.imgui_window_params.tweaked_theme.theme = DEFAULT_THEME
    runner_params.callbacks.setup_imgui_style = apply_custom_style

    # Main loop
    runner_params.callbacks.show_gui = lambda: render_main_layout(state)

    # Addons
    addons = immapp.AddOnsParams(with_implot=True, with_markdown=True)

    # Run application
    immapp.run(runner_params, addons)


if __name__ == "__main__":
    main()
