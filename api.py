from flask import Flask, request
from flask_restful import Resource, Api
from datetime import datetime, timedelta
from requests import get
import json

CURRENCY_API_KEY = "834dbbebf0270311fc5d"

raw_pricing = {
    "prices": [
        {"product_id": 1, "price": 599, "vat_band": "standard"},
        {"product_id": 2, "price": 250, "vat_band": "zero"},
        {"product_id": 3, "price": 250, "vat_band": "zero"},
        {"product_id": 4, "price": 1000, "vat_band": "zero"},
        {"product_id": 5, "price": 1250, "vat_band": "standard"},
    ],
    "vat_bands": {"standard": 0.2, "zero": 0},
}

app = Flask(__name__)
api = Api(app)


def format_pricing(raw_pricing: dict):
    return {
        product["product_id"]: {
            "price": product["price"],
            "VAT": round(
                raw_pricing["vat_bands"][product["vat_band"]] * product["price"], 2
            ),
        }
        for product in raw_pricing["prices"]
    }


def format_order(order: dict):
    return {item["product_id"]: item["quantity"] for item in order["order"]["items"]}


def calc_order_details(
    order_quantities: dict, pricing: dict, currency: str, conversion_rate: float = 1.0
):
    summary = {}
    running_total_price = 0
    running_total_vat = 0

    for product_id in order_quantities:
        summary[product_id] = {}
        quantity = order_quantities[product_id]
        summary[product_id]["quantity"] = quantity

        total_price = quantity * pricing[product_id]["price"] * conversion_rate
        summary[product_id]["total_price"] = round(total_price, 2)
        running_total_price += total_price

        total_vat = quantity * pricing[product_id]["VAT"] * conversion_rate
        summary[product_id]["total_VAT"] = round(total_vat, 2)
        running_total_vat += total_vat

    summary["total_price"] = round(running_total_price, 2)
    summary["total_VAT"] = round(running_total_vat, 2)
    summary["currency"] = currency
    return summary


class currency_conversion:
    """
    Class to keep track of currency conversion.
    """

    def __init__(self, api_key: str, default_currency: str = "GBP"):
        self._api_key = api_key
        self._default_currency = default_currency
        self._conversion_rates = {}

    def get_conversion_rate(self, currency: str):
        """
        Get the conversion_rate for a currency relative to GBP.
    
        currency : 3 char str
        """
        if currency == self._default_currency:
            return 1.0

        if currency in self._conversion_rates.keys():
            if self._conversion_rates[currency]["updated"] > datetime.now() - timedelta(
                hours=1
            ):
                # is up to date, return the rate
                return self._conversion_rates[currency]["rate"]

        # It is necessary to do a query
        query = f"GBP_{currency}"
        url = "https://free.currencyconverterapi.com/api/v6/convert?"
        rate = get(f"{url}apiKey={CURRENCY_API_KEY}&q={query}&compact=ultra").json()[
            query
        ]
        self._conversion_rates[currency] = {"rate": rate, "updated": datetime.now()}
        return rate

    @property
    def conversion_rates(self):
        """Return the history of conversion rates."""
        return self._conversion_rates


class PricingAPI(Resource):
    def post(self):
        order = request.get_json(force=True)
        if not "currency" in order["order"].keys():
            currency = "GBP"
        else:
            currency = order["order"]["currency"]
        conversion_rate = currency_converter.get_conversion_rate(currency)

        order_quantities = format_order(order)
        pricing = format_pricing(raw_pricing)
        order_details = calc_order_details(
            order_quantities, pricing, currency, conversion_rate
        )
        return order_details


api.add_resource(PricingAPI, "/")

if __name__ == "__main__":
    currency_converter = currency_conversion(api_key=CURRENCY_API_KEY)
    app.run(debug=True)
