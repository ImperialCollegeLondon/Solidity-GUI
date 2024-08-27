"""Tests for the material Module."""

import pytest

from solidity_gui.main.material import calculate_lame_constants


def test_calculate_lame_constants():
    """Test calculation of Lame's constants from Young's Modulus and Poisson's Ratio."""
    youngs_modulus = 2.233251e10
    poissons_ratio = 0.3

    expected_lambda = 1.28841404e10
    expected_mu = 8.58942692e9

    calculated_lambda, calculated_mu = calculate_lame_constants(
        youngs_modulus, poissons_ratio
    )
    assert calculated_lambda == pytest.approx(expected_lambda)
    assert calculated_mu == pytest.approx(expected_mu)
