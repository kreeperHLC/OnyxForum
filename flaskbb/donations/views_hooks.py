from datetime import datetime
import string
import requests

from flask import Flask, Blueprint, Response, request, url_for
from flask.views import MethodView
from flaskbb.utils.helpers import register_view
from pluggy import HookimplMarker

impl = HookimplMarker("flaskbb")


def parse_datetime(qiwi_format: str) -> datetime:
    return datetime.fromisoformat(qiwi_format)


class QiwiHook(MethodView):
    def post(self):
        content = request.get_json()

        print("----")
        print("Qiwi hook:")
        print("Request: " + str(request.__dict__))
        print("Json: " + str(content))
        print("----")

        if content['payment']['type'] != 'IN' or content['payment']['status'] != 'SUCCESS':
            print("Skip hook: Not suitable hook")
            return Response(status=200)

        if content['payment']['sum']['currency'] != 643:  # ruble
            print("Skip hook: Unknown currency")
            return Response(status=200)

        dt = parse_datetime(content['payment']['date'])
        ckey = content['payment']['comment'].split(' ')[0].lower().strip(string.punctuation)
        amount = content['payment']['sum']['amount']

        print("New donation from " + ckey + ". Amount: " + str(amount) + ". Datetime: " + dt.isoformat())
        return Response(status=200)


def register_webhooks_service(app):
    headers = {
        "Authorization": "Bearer " + app.config["QIWI_TOKEN"],
        "Accept": "application/json"
    }

    res = requests.get("https://edge.qiwi.com/person-profile/v1/profile/current", headers=headers)
    print("QIWI Test:")
    print(res.__dict__)

    if not app.config["QIWI_HOOKS"]:
        print("QIWI Webhooks registration skipped")
        return

    params = {
        "hookType": 1,
        "param": url_for("donations.qiwi_hook", _external=True),
        "txnType": 0
    }
    headers = {
        "Authorization": "Bearer " + app.config["QIWI_TOKEN"],
        "Accept": "application/json"
    }
    res = requests.put("https://edge.qiwi.com/payment-notifier/v1/hooks", params=params, headers=headers)
    print("QIWI Webhooks registration result:")
    print("Request: " + str(res.request.__dict__))
    print("Res: " + str(res.__dict__))


@impl(tryfirst=True)
def flaskbb_load_blueprints(app: Flask):
    donations = Blueprint("donations", __name__)

    register_view(
        donations,
        routes=['/qiwi_hook'],
        view_func=QiwiHook.as_view('qiwi_hook')
    )

    app.register_blueprint(donations)
    app.before_first_request(lambda: register_webhooks_service(app))
