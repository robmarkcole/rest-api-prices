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

conversion_rates = {
    "fake_currency": {"rate": 1.3, "updated": datetime.now()}
}  # init and show contents

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


def get_conversion_rate(currency: str, conversion_rates: dict = conversion_rates):
    """
    Get the conversion_rate for a currency relative to GBP.
    
    currency : 3 char str
    """
    if currency == "GBP":
        return 1.0

    if currency in conversion_rates.keys():
        if conversion_rates[currency]["updated"] > datetime.now() - timedelta(hours=1):
            # is up to date, return the rate
            return conversion_rates[currency]["rate"]

    query = f"GBP_{currency}"
    url = "https://free.currencyconverterapi.com/api/v6/convert?"
    rate = get(f"{url}apiKey={CURRENCY_API_KEY}&q={query}&compact=ultra").json()[query]
    conversion_rates[currency] = {"rate": rate, "updated": datetime.now()}
    return rate


class PricingAPI(Resource):
    def get(self, order):
        order = json.loads(order)
        if not "currency" in order["order"].keys():
            currency = "GBP"
        else:
            currency = order["order"]["currency"]
        conversion_rate = get_conversion_rate(currency)

        order_quantities = format_order(order)
        pricing = format_pricing(raw_pricing)
        order_details = calc_order_details(
            order_quantities, pricing, currency, conversion_rate
        )
        return order_details


api.add_resource(PricingAPI, "/<string:order>")

if __name__ == "__main__":
    app.run(debug=True)
