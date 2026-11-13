from imgui_bundle import imgui_color_text_edit as ed


def create_sql_editor(initial_text: str = "") -> ed.TextEditor:
    editor = ed.TextEditor()
    editor.set_language(ed.TextEditor.Language.sql())
    editor.set_palette(ed.TextEditor.get_dark_palette())
    editor.set_show_line_numbers_enabled(True)
    editor.set_show_current_line_highlight_enabled(False)
    editor.set_auto_indent_enabled(True)
    editor.set_tab_size(2)
    editor.set_insert_spaces_on_tabs(True)
    editor.set_read_only_enabled(False)
    if initial_text:
        editor.set_text(initial_text)
    return editor
