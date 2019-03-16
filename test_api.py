import api as api

GBP = "GBP"

TEST_ORDER = {
    "order": {
        "id": 12345,
        "items": [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 5},
            {"product_id": 3, "quantity": 1},
        ],
    }
}

TEST_ORDER_FORMATTED = {1: 1, 2: 5, 3: 1}

TEST_PRICING_FORMATTED = {
    1: {"price": 599, "VAT": 119.8},
    2: {"price": 250, "VAT": 0},
    3: {"price": 250, "VAT": 0},
    4: {"price": 1000, "VAT": 0},
    5: {"price": 1250, "VAT": 250.0},
}

TEST_VALID_GBP_ORDER = {
    1: {"quantity": 1, "total_price": 599.0, "total_VAT": 119.8},
    2: {"quantity": 5, "total_price": 1250.0, "total_VAT": 0.0},
    3: {"quantity": 1, "total_price": 250.0, "total_VAT": 0.0},
    "total_price": 2099.0,
    "total_VAT": 119.8,
    "currency": "GBP",
}


def test_format_pricing():
    assert api.format_pricing(api.raw_pricing) == TEST_PRICING_FORMATTED


def test_format_order():
    assert api.format_order(TEST_ORDER) == TEST_ORDER_FORMATTED


def test_calc_order_details():
    assert (
        api.calc_order_details(TEST_ORDER_FORMATTED, TEST_PRICING_FORMATTED, GBP)
        == TEST_VALID_GBP_ORDER
    )
