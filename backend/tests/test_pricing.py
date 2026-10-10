import pytest
from backend.app.services.pricing_service import (
    calculate_line_item,
    calculate_change_order_totals,
)

def test_calculate_line_item_standard():
    assert calculate_line_item(8.0, 2000.0) == 16000.0
    assert calculate_line_item(5.0, 2000.0) == 10000.0
    assert calculate_line_item(1.5, 2000.0) == 3000.0
    assert calculate_line_item(0.5, 2000.0) == 1000.0

def test_calculate_line_item_edge_cases():
    # Zero hours
    assert calculate_line_item(0.0, 2000.0) == 0.0
    # Zero rate
    assert calculate_line_item(8.0, 0.0) == 0.0
    # None handling
    assert calculate_line_item(None, 2000.0) == 0.0
    assert calculate_line_item(8.0, None) == 0.0
    # Fractional hours with rounding
    assert calculate_line_item(1.333333, 1500.0) == 2000.0
    # Negative values clamp to 0
    assert calculate_line_item(-5.0, 2000.0) == 0.0
    assert calculate_line_item(5.0, -100.0) == 0.0

def test_calculate_change_order_totals_without_tax():
    items = [
        {"hours": 8.0, "rate": 2000.0},
        {"hours": 5.0, "rate": 2000.0},
    ]
    res = calculate_change_order_totals(items, tax_rate_percent=0.0)
    assert res["subtotal"] == 26000.0
    assert res["taxes"] == 0.0
    assert res["total"] == 26000.0
    assert items[0]["line_total"] == 16000.0
    assert items[1]["line_total"] == 10000.0

def test_calculate_change_order_totals_with_tax():
    items = [
        {"hours": 10.0, "rate": 1000.0},
    ]
    res = calculate_change_order_totals(items, tax_rate_percent=18.0)
    assert res["subtotal"] == 10000.0
    assert res["taxes"] == 1800.0
    assert res["total"] == 11800.0

def test_calculate_change_order_empty():
    res = calculate_change_order_totals([], tax_rate_percent=10.0)
    assert res["subtotal"] == 0.0
    assert res["taxes"] == 0.0
    assert res["total"] == 0.0
