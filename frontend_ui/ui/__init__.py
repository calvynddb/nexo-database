"""
UI module - reusable UI components, styling, and utilities.
"""

from .cards import DepthCard, StatCard
from .pagination import PaginationControl
from .inputs import SmartSearchEntry, SearchableComboBox, StyledComboBox
from .utils import (
    setup_treeview_style,
    placeholder_image,
    get_icon,
    get_main_logo,
    create_gradient_strip,
    create_gradient_background,
    apply_window_icon,
    SoftLoadingOverlay,
    animate_toplevel_in,
    log_ui_timing,
)

__all__ = [
    "DepthCard", "StatCard", "PaginationControl",
    "SmartSearchEntry", "SearchableComboBox", "StyledComboBox",
    "setup_treeview_style", "placeholder_image", "get_icon", "get_main_logo", "create_gradient_strip", "create_gradient_background", "apply_window_icon",
    "SoftLoadingOverlay", "animate_toplevel_in", "log_ui_timing"
]
