"""Tests for CustomInteractorStyle."""
from contextlib import nullcontext as does_not_raise
from itertools import product
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from pytest import MonkeyPatch

from solidity_gui.main.custom_interactor_style import CustomInteractorStyle

INTERACT_FUNC_NAMES = {"pan": "Pan", "rotate": "Rotate", "zoom": "Dolly"}
VALID_MODES = INTERACT_FUNC_NAMES.keys()


@pytest.fixture
def style(monkeypatch: MonkeyPatch) -> CustomInteractorStyle:
    """A fixture for CustomInteractorStyle.

    The relevant pan/rotate/zoom methods from the base class are patched so we can check
    whether they were called.
    """
    for prefix, name in product(("Start", "End"), INTERACT_FUNC_NAMES.values()):
        monkeypatch.setattr(CustomInteractorStyle, f"{prefix}{name}", MagicMock())

    return CustomInteractorStyle()


@patch.object(CustomInteractorStyle, "AddObserver")
def test_init(add_observer_mock: Mock, subscribe_mock: MagicMock) -> None:
    """Test CustomInteractorStyle's constructor."""
    style = CustomInteractorStyle()

    # Check default arg
    assert style.interact_mode == "pan"

    # Check that left mouse button events are overridden
    style.AddObserver.assert_any_call("LeftButtonPressEvent", style._mouse_down)
    style.AddObserver.assert_any_call("LeftButtonReleaseEvent", style._mouse_up)

    # Check object has subscribed to changes in interact mode
    subscribe_mock.assert_called_once_with(
        style._change_interact_mode, "window.change_mode"
    )


@pytest.mark.parametrize(
    "mode,raises",
    (
        (mode, does_not_raise() if mode in VALID_MODES else pytest.raises(ValueError))
        for mode in (*VALID_MODES, "PAN", "Pan", "badger")
    ),
)
def test_change_interact_mode(
    style: CustomInteractorStyle, mode: str, raises: Any
) -> None:
    """Test the _change_interact_mode() method."""
    with raises:
        style._change_interact_mode(mode)


def _check_mouse_func(style: CustomInteractorStyle, prefix: str, mode: str) -> None:
    """Checks that the right method for the prefix + mode was called."""
    for key, value in INTERACT_FUNC_NAMES.items():
        func = getattr(style, f"{prefix}{value}")

        if key == mode:
            func.assert_called_once_with()
        else:
            func.assert_not_called()


@pytest.mark.parametrize("mode", VALID_MODES)
def test_mouse_down(style: CustomInteractorStyle, mode: str) -> None:
    """Test the _mouse_down() method."""
    style._change_interact_mode(mode)
    style._mouse_down(MagicMock(), MagicMock())
    _check_mouse_func(style, "Start", mode)


@pytest.mark.parametrize("mode", VALID_MODES)
def test_mouse_up(style: CustomInteractorStyle, mode: str) -> None:
    """Test the _mouse_up() method."""
    style._change_interact_mode(mode)
    style._mouse_up(MagicMock(), MagicMock())
    _check_mouse_func(style, "End", mode)
