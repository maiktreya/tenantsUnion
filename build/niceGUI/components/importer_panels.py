# build/niceGUI/components/importer_panels.py (Corrected)

from nicegui import ui
from typing import List, Dict, Any, Callable, Awaitable

from config import IMPORTER_HEADER_MAP

def render_preview_tabs(
    state: Any,
    panels: Dict[str, ui.column],
    on_sort: Callable,
    on_drop: Callable,
    on_revalidate: Callable,
    on_bloque_change: Callable,
    on_apply_suggestion: Callable,
    on_clear_assignment: Callable,
    on_score_limit_change: Callable[[float], Awaitable[None]],
    get_bloque_score_limit: Callable[[], float],
    on_reset_bloques: Callable[[], None],
):
    """Renders all data preview panels with necessary callbacks."""
    _render_standard_panel("afiliada", panels["afiliadas"], state, on_sort, on_drop, on_revalidate, ["nombre", "apellidos", "cif", "email", "telefono", "fecha_nac"])
    _render_standard_panel("piso", panels["pisos"], state, on_sort, on_drop, on_revalidate, ["direccion", "municipio", "cp", "bloque_id", "n_personas", "inmobiliaria", "prop_vertical", "fecha_firma"])
    _render_standard_panel("facturacion", panels["facturacion"], state, on_sort, on_drop, on_revalidate, ["cuota", "periodicidad", "forma_pago", "iban"])
    _render_bloques_panel(
        panel=panels["bloques"],
        state=state,
        on_drop=on_drop,
        on_revalidate=on_revalidate,
        on_bloque_change=on_bloque_change,
        on_apply_suggestion=on_apply_suggestion,
        on_clear_assignment=on_clear_assignment,
        on_score_limit_change=on_score_limit_change,
        get_bloque_score_limit=get_bloque_score_limit,
        on_reset_bloques=on_reset_bloques,
    )

def _render_standard_panel(data_key: str, panel: ui.column, state: Any, on_sort: Callable, on_drop: Callable, on_revalidate: Callable, fields: List[str]):
    """Renders a generic preview panel for afiliadas, pisos, and facturacion."""
    if not panel: return
    panel.clear()
    with panel, ui.scroll_area().classes("w-full h-[32rem]"):
        with ui.row().classes("w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 items-center no-wrap sticky top-0 z-10"):
            ui.label("Acciones").classes("w-16 min-w-[4rem]")
            with ui.row().classes("w-24 min-w-[6rem] items-center cursor-pointer").on("click", lambda: on_sort("is_valid")):
                ui.label("Estado")
                sort_info = next((c for c in state.sort_criteria if c[0] == "is_valid"), None)
                if sort_info:
                    ui.icon("arrow_upward" if sort_info[1] else "arrow_downward", size="sm")
            ui.label("Afiliada").classes("w-48 min-w-[12rem]")
            for field in fields:
                width = "flex-grow min-w-[15rem]" if field in ["email", "direccion", "iban"] else "w-32 min-w-[8rem]"
                ui.label(IMPORTER_HEADER_MAP.get(field, field.title())).classes(f"{width} cursor-pointer").on("click", lambda f=field: on_sort(f))

        for record in state.records:
            with ui.row().classes("w-full items-center gap-2 p-2 border-t no-wrap") as row:
                record.setdefault("ui_updaters", {})[data_key] = lambda r=row, rec=record: r.classes(remove="bg-red-100 bg-green-50", add=("bg-green-50" if rec["validation"]["is_valid"] else "bg-red-100")).tooltip("\n".join(rec["validation"]["errors"]) or "Válido")

                with ui.column().classes("w-16 min-w-[4rem] items-center"):
                    ui.button(icon="delete", on_click=lambda r=record: on_drop(r)).props("size=sm flat dense color=negative")

                with ui.column().classes("w-24 min-w-[6rem] items-center"):
                    icon = ui.icon("check_circle" if record["validation"]["is_valid"] else "cancel")
                    icon.classes("text-green-500" if record["validation"]["is_valid"] else "text-red-500")
                    def _update_status_icon(ic=icon, rec=record):
                        ic.set_name("check_circle" if rec["validation"]["is_valid"] else "cancel")
                        ic.classes(remove="text-green-500 text-red-500", add=("text-green-500" if rec["validation"]["is_valid"] else "text-red-500"))
                    record["ui_updaters"][f"status_icon_{data_key}"] = _update_status_icon

                ui.label(f"{record['afiliada']['nombre']} {record['afiliada']['apellidos']}").classes("w-48 min-w-[12rem] text-sm")

                for field in fields:
                    width = "flex-grow min-w-[15rem]" if field in ["email", "direccion", "iban"] else "w-32 min-w-[8rem]"
                    ui.input(value=record[data_key].get(field)).classes(width).bind_value(record[data_key], field).on("change", lambda r=record: on_revalidate(r))

            record["ui_updaters"][data_key]()

def _render_bloques_panel(panel: ui.column, state: Any, on_drop: Callable, on_revalidate: Callable, on_bloque_change: Callable, on_apply_suggestion: Callable, on_clear_assignment: Callable, on_score_limit_change: Callable, get_bloque_score_limit: Callable, on_reset_bloques: Callable):
    """Renders the specialized panel for managing 'bloque' assignments."""
    if not panel: return
    panel.clear()
    with panel, ui.scroll_area().classes("w-full h-[32rem]"):
        if not state.records:
            ui.label("Sin registros cargados.").classes("text-sm text-gray-500 p-4")
            return

        with ui.row().classes("w-full items-center gap-2 p-2 bg-white/90 sticky top-0 z-20 border-b"):
            ui.label("Umbral de Coincidencia").classes("text-xs uppercase text-gray-500")
            async def _slider_changed(e):
                try:
                    # NiceGUI provides numeric values for slider; coerce defensively
                    val = float(e.value) if e.value is not None else 0.0
                    await on_score_limit_change(val)
                except Exception:
                    # Silently ignore to avoid breaking UI; errors are notified upstream
                    pass
            slider = ui.slider(
                min=0.0,
                max=1.0,
                step=0.01,
                value=get_bloque_score_limit(),
                on_change=_slider_changed,
            ).classes("flex-1")
            ui.label().classes("text-xs font-mono").bind_text_from(slider, "value", lambda v: f"{v:.2f}")
            ui.button("Reiniciar campos", on_click=on_reset_bloques).props("size=sm flat").classes("ml-2")

        with ui.row().classes("w-full font-bold text-gray-600 gap-2 p-2 bg-gray-50 items-center no-wrap sticky top-[3.2rem] z-10"):
            ui.label("Acciones").classes("w-16")
            with ui.row().classes("w-24 items-center cursor-pointer").on("click", lambda: on_sort("is_valid")):
                ui.label("Estado")
                sort_info_b = next((c for c in state.sort_criteria if c[0] == "is_valid"), None)
                if sort_info_b:
                    ui.icon("arrow_upward" if sort_info_b[1] else "arrow_downward", size="sm")
            ui.label("Dirección Piso").classes("w-48")
            ui.label("Dirección Bloque").classes("flex-grow")
            ui.label("Vinculación").classes("w-36")
            ui.label("Sugerencia").classes("w-48")

        for record in state.records:
            with ui.row().classes("w-full items-start gap-2 p-2 border-t no-wrap") as row:
                record.setdefault("ui_updaters", {})['bloques_row'] = lambda r=row, rec=record: r.classes(remove="bg-red-100 bg-green-50", add=("bg-green-50" if rec["validation"]["is_valid"] else "bg-red-100")).tooltip("\n".join(rec["validation"]["errors"]) or "Válido")

                ui.button(icon="delete", on_click=lambda r=record: on_drop(r)).props("size=sm flat dense color=negative").classes("w-16")

                with ui.column().classes("w-24 items-center"):
                    icon = ui.icon("check_circle" if record["validation"]["is_valid"] else "cancel").classes("text-green-500" if record["validation"]["is_valid"] else "text-red-500")
                    def _update_bloques_status_icon(ic=icon, rec=record):
                        ic.set_name("check_circle" if rec["validation"]["is_valid"] else "cancel")
                        ic.classes(remove="text-green-500 text-red-500", add=(
                            "text-green-500" if rec["validation"]["is_valid"] else "text-red-500"
                        ))
                    record["ui_updaters"]["bloques_status_icon"] = _update_bloques_status_icon

                ui.label(record.get("piso", {}).get("direccion", "")).classes("w-48 text-sm")
                bloque_dir_input = ui.input(value=record.setdefault("bloque", {}).get("direccion")).classes("flex-grow transition-opacity").bind_value(record["bloque"], "direccion").on("change", lambda r=record: on_revalidate(r))

                with ui.column().classes("w-36 items-center gap-1"):
                    # Linked status icon
                    linked = record.get("piso", {}).get("bloque_id") is not None
                    link_icon = ui.icon("check_circle" if linked else "radio_button_unchecked").classes("text-green-500" if linked else "text-gray-300")
                    def _update_link_icon(ic=link_icon, rec=record):
                        is_linked = rec.get("piso", {}).get("bloque_id") is not None
                        ic.set_name("check_circle" if is_linked else "radio_button_unchecked")
                        ic.classes(remove="text-green-500 text-gray-300", add=("text-green-500" if is_linked else "text-gray-300"))
                    record["ui_updaters"]["bloque_link_icon"] = _update_link_icon

                    with ui.row().classes("w-full justify-around"):
                        vinc_btn = ui.button("Vincular", on_click=lambda r=record: on_apply_suggestion(r)).props("size=xs flat")
                        ui.button("Limpiar", on_click=lambda r=record: on_clear_assignment(r)).props("size=xs flat")

                    def _update_vinc_btn(btn=vinc_btn, rec=record):
                        suggestion = rec.get("meta", {}).get("bloque")
                        has_suggestion = bool(suggestion and (suggestion.get("id") or suggestion.get("direccion")))
                        try:
                            btn.set_enabled(has_suggestion)
                        except Exception:
                            # set_enabled might not exist in older NiceGUI versions; fallback via classes
                            if has_suggestion:
                                btn.classes(remove="opacity-50 pointer-events-none")
                            else:
                                btn.classes(add="opacity-50 pointer-events-none")
                    record["ui_updaters"]["bloque_vincular_btn"] = _update_vinc_btn

                suggestion_label = ui.label().classes("w-48 text-xs text-gray-500")
                record["ui_updaters"]["suggestion_label"] = lambda lbl=suggestion_label, rec=record: lbl.set_text(
                    f"ID: {rec['meta'].get('bloque', {}).get('id')} ({rec['meta'].get('bloque_score', 0)*100:.1f}%)" if rec.get('meta', {}).get('bloque') else "Sin sugerencia"
                )

                # Updaters for dynamic UI: row bg, suggestion label, link icon, vincular button, and blocking of address input
                def _update_bloque_dir_input(inp=bloque_dir_input, rec=record):
                    is_linked = rec.get("piso", {}).get("bloque_id") is not None
                    inp.classes(remove="pointer-events-none opacity-60", add=("pointer-events-none opacity-60" if is_linked else ""))
                record["ui_updaters"]["bloque_dir_input"] = _update_bloque_dir_input

                record["ui_updaters"]['bloques_row']()
                record["ui_updaters"]["suggestion_label"]()
                record["ui_updaters"]["bloque_link_icon"]()
                record["ui_updaters"]["bloque_vincular_btn"]()
                record["ui_updaters"]["bloque_dir_input"]()
