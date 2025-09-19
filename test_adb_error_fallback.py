"""Smoke test ensuring integration survives missing adb_shell.AdbError."""
from __future__ import annotations

import importlib
import sys
from typing import List


def main() -> None:
    """Run the compatibility smoke test."""
    try:
        import adb_shell.exceptions as adb_exceptions
    except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
        print("AdbError fallback compatibility test: SKIPPED (adb_shell not installed)")
        return

    expected_base = getattr(adb_exceptions, "AdbException", Exception)
    had_adb_error = hasattr(adb_exceptions, "AdbError")
    original_adb_error = getattr(adb_exceptions, "AdbError", None)

    if had_adb_error:
        delattr(adb_exceptions, "AdbError")

    modules_to_check: List[str] = [
        "custom_components.android_tv_box.adb_service",
        "custom_components.android_tv_box.config_flow",
        "custom_components.android_tv_box.__init__",
    ]

    # Remove modules so they reload with the modified adb_exceptions.
    cleared_modules = {}
    for module_name in modules_to_check:
        cleared_modules[module_name] = sys.modules.pop(module_name, None)

    try:
        adb_service = importlib.import_module(modules_to_check[0])
        config_flow = importlib.import_module(modules_to_check[1])
        integration = importlib.import_module(modules_to_check[2])

        assert adb_service.BASE_ADB_ERROR is expected_base, "ADB service base error mismatch"
        assert config_flow.BASE_ADB_ERROR is expected_base, "Config flow base error mismatch"
        assert integration.BASE_ADB_ERROR is expected_base, "Integration base error mismatch"

        print("AdbError fallback compatibility test: PASS")
    finally:
        # Restore adb_exceptions.AdbError if it was present originally.
        if had_adb_error:
            setattr(adb_exceptions, "AdbError", original_adb_error)

        # Ensure modules are reloaded with the original adb_exceptions state.
        for module_name in modules_to_check:
            sys.modules.pop(module_name, None)
        for module_name, module in cleared_modules.items():
            if module is not None:
                sys.modules[module_name] = module

        # Reload the modules to restore normal operation for subsequent tests.
        for module_name in modules_to_check:
            importlib.import_module(module_name)


if __name__ == "__main__":
    main()
