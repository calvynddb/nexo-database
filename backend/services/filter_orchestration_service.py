"""
Filter orchestration helpers for dashboard-level apply/rebuild decisions.
"""


class FilterOrchestrationService:
    """Pure helper methods for filter orchestration state transitions."""

    @staticmethod
    def should_rebuild_controls(
        current_controls_view,
        controls_signature_map: dict,
        view_class,
        data_signature,
        has_filter_vars: bool,
    ) -> bool:
        return not (
            current_controls_view == view_class
            and controls_signature_map.get(view_class) == data_signature
            and bool(has_filter_vars)
        )

    @staticmethod
    def normalized_apply_signature(query: str, filters: dict) -> tuple:
        normalized_query = str(query or "").strip().lower()
        normalized_filters = tuple(
            sorted((str(key), str(value).strip().lower()) for key, value in (filters or {}).items())
        )
        return normalized_query, normalized_filters

    @staticmethod
    def should_skip_apply(last_signature_by_view: dict, view_class, signature: tuple, force: bool = False) -> bool:
        return (not force) and last_signature_by_view.get(view_class) == signature

    @staticmethod
    def record_apply_signature(last_signature_by_view: dict, view_class, signature: tuple) -> None:
        last_signature_by_view[view_class] = signature

    @staticmethod
    def clear_caches(
        filter_schema_cache: dict,
        filter_controls_data_signature: dict,
        last_signature_by_view: dict,
        view_class=None,
    ) -> None:
        filter_schema_cache.clear()
        filter_controls_data_signature.clear()
        if view_class is None:
            last_signature_by_view.clear()
            return
        last_signature_by_view.pop(view_class, None)
