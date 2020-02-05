# -*- coding: utf-8 -*-
import hashlib
import os
import random
from base64 import b64decode, b64encode

from django.urls import reverse
from django.utils.encoding import force_bytes, force_str

import pytest

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from thorbanks import settings as th_settings
from thorbanks.checks import check_banklink_settings
from thorbanks.forms import PaymentRequest
from thorbanks.utils import get_pkey, pingback_url, request_digest


def only_issue_ids(issues):
    """
    :param issues: list[CheckMessage]
    :return: list[string]
    """
    return [x.id for x in issues]


def get_banklink_config(bank_name=None, printable_name=None):
    import os

    base_dir = os.path.join(os.path.dirname(__file__), "..")

    return {
        bank_name
        or "swedbank": {
            "PRINTABLE_NAME": printable_name or "Swedbank",
            "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/swedbank-common",
            "CLIENT_ID": "uid100052",
            "BANK_ID": "HP",
            "PRIVATE_KEY": os.path.join(base_dir, "certs", "swed_key.pem"),
            "PUBLIC_KEY": os.path.join(base_dir, "certs", "swed_pub.pem"),
            "TYPE": "banklink",
            "IMAGE_PATH": "swedbank.png",
            "ORDER": 1,
            "SEND_REF": True,
        },
        "seb": {
            "PRINTABLE_NAME": "SEB",
            "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/seb-common",
            "CLIENT_ID": "uid100036",
            "BANK_ID": "EYP",
            "PRIVATE_KEY": os.path.join(base_dir, "certs", "seb_key.pem"),
            "PUBLIC_KEY": os.path.join(base_dir, "certs", "seb_pub.pem"),
            "DIGEST_COUNTS_BYTES": True,
            "TYPE": "banklink",
            "IMAGE_PATH": "seb.png",
            "ORDER": 2,
            "SEND_REF": False,
        },
        "lhv": {
            "PRINTABLE_NAME": "LHV",
            "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/lhv-common",
            "CLIENT_ID": "uid100049",
            "BANK_ID": "LHV",
            "PRIVATE_KEY": os.path.join(base_dir, "certs", "lhv_key.pem"),
            "PUBLIC_KEY": os.path.join(base_dir, "certs", "lhv_pub.pem"),
            "TYPE": "banklink",
            "IMAGE_PATH": "lhv.png",
            "ORDER": 3,
        },
        "danske": {
            "PRINTABLE_NAME": "Danske",
            "REQUEST_URL": "http://banks.maximum.thorgate.eu/banklink/sampo-common",
            "CLIENT_ID": "uid100010",
            "BANK_ID": "SAMPOPANK",
            "PRIVATE_KEY": os.path.join(base_dir, "certs", "danske_key.pem"),
            "PUBLIC_KEY": os.path.join(base_dir, "certs", "danske_pub.pem"),
            "TYPE": "banklink",
            "IMAGE_PATH": "danske.png",
            "ORDER": 4,
        },
    }


def test_no_settings_raises_exception(settings):
    settings.BANKLINKS = None

    assert only_issue_ids(check_banklink_settings(None)) == [
        "thorbanks.E004",
    ]


def test_banklinks_is_not_dict(settings):
    settings.BANKLINKS = True

    assert only_issue_ids(check_banklink_settings(None)) == [
        "thorbanks.E004",
    ]


def test_banklink_name_too_long(settings):
    settings.BANKLINKS = get_banklink_config(bank_name="ABCDEFGHIJKLMNOPS")

    assert only_issue_ids(check_banklink_settings(None)) == [
        "thorbanks.E005",
    ]


def test_banklink_data_not_dict(settings):
    settings.BANKLINKS = {"swedbank": None}

    assert only_issue_ids(check_banklink_settings(None)) == [
        "thorbanks.E006",
    ]


@pytest.mark.parametrize(
    "missing_key", ["PRIVATE_KEY", "PUBLIC_KEY", "CLIENT_ID", "REQUEST_URL", "BANK_ID"]
)
def test_missing_keys(settings, missing_key):
    settings.BANKLINKS = get_banklink_config()
    del settings.BANKLINKS["swedbank"][missing_key]

    assert only_issue_ids(check_banklink_settings(None)) == [
        "thorbanks.E007",
    ]


@pytest.mark.parametrize("key_type", ["private", "public"])
def test_no_key_file(settings, key_type):
    file_name = "rand_name_%d.key" % random.randint(1, 999999)

    settings.BANKLINKS = get_banklink_config()
    settings.BANKLINKS["swedbank"]["%s_KEY" % key_type.upper()] = file_name

    assert only_issue_ids(check_banklink_settings(None)) == [
        "thorbanks.{}".format("E009" if key_type == "private" else "E008"),
    ]


def test_getters(settings):
    conf = get_banklink_config()
    settings.BANKLINKS = conf
    th_settings.configure()

    assert th_settings.get_private_key("swedbank") == os.path.abspath(
        conf["swedbank"]["PRIVATE_KEY"]
    )
    assert th_settings.get_public_key("swedbank") == os.path.abspath(
        conf["swedbank"]["PUBLIC_KEY"]
    )
    assert th_settings.get_client_id("swedbank") == conf["swedbank"]["CLIENT_ID"]
    assert th_settings.get_request_url("swedbank") == conf["swedbank"]["REQUEST_URL"]
    assert th_settings.get_link_type("swedbank") == conf["swedbank"]["TYPE"]

    assert th_settings.get_send_ref("swedbank") == conf["swedbank"]["SEND_REF"]
    assert th_settings.get_send_ref("seb") == conf["seb"]["SEND_REF"]
    assert th_settings.get_send_ref("danske") is True

    the_list = th_settings.get_bank_choices()
    assert isinstance(the_list, list)

    for item in the_list:
        assert isinstance(item, tuple)
        assert len(item) == 4
        assert item[0] in conf.keys()

        assert item[1] == conf[item[0]]["PRINTABLE_NAME"]
        assert item[2] == conf[item[0]]["IMAGE_PATH"]
        assert item[3] == conf[item[0]].get("ORDER", 99)


def test_transaction_model():
    trans = th_settings.get_model("Transaction")(
        pk=1, currency="EUR", amount=15.67, bank_name="myBank"
    )

    assert trans.__str__() == "Transaction 1 - EUR 15.67 from myBank [pending]"


def test_pingback_with_request(rf):
    request = rf.get("/test", HTTP_HOST="127.0.0.1")

    ping_back = pingback_url(request=request)

    assert ping_back == "http://%s%s" % (
        request.META["HTTP_HOST"],
        reverse("thorbanks_response"),
    )


@pytest.mark.django_db
def test_payment_result(settings):
    settings.BANKLINKS = get_banklink_config()
    th_settings.configure()

    redirect_to = "http://example.com"
    ping_back = pingback_url(base_url=redirect_to)

    assert ping_back == redirect_to + reverse("thorbanks_response")

    request = PaymentRequest(
        bank_name="swedbank",
        amount=13.99,
        currency="EUR",
        redirect_to=redirect_to,
        redirect_on_failure=redirect_to,
        message="My cool payment",
        url=ping_back,
    )

    assert request.transaction.bank_name == "swedbank"
    assert request.transaction.amount == 13.99
    assert request.transaction.currency == "EUR"
    assert request.transaction.redirect_after_success == redirect_to
    assert request.transaction.redirect_on_failure == redirect_to
    assert request["VK_RETURN"].value() == ping_back

    expected_digest = force_bytes(
        "0041012003008009uid100052001100513.99003EUR00213015My cool payment044http://example"
        ".com/banks/thorbanks_response/044http://example.com/banks/thorbanks_response/024%s"
        % request.transaction.created.strftime("%Y-%m-%dT%H:%M:%S%z")
    )

    assert (
        request_digest(request.cleaned_data, request.transaction.bank_name)
        == expected_digest
    )

    expected_mac = get_pkey("swedbank").sign(
        expected_digest, padding.PKCS1v15(), hashes.SHA1()
    )

    assert request["VK_MAC"].value() == force_str(b64encode(expected_mac))

    assert (
        len(b64decode(request["VK_MAC"].value())) == 256
    )  # The key must be 256 bytes (2048 bit)


@pytest.mark.django_db
def test_payment_form_html_decode_error():
    form = PaymentRequest(
        bank_name="swedbank",
        amount=20.40,
        currency="EUR",
        redirect_to="http://example.com",
        redirect_on_failure="http://example.com",
        message="Pangalink: 12345 (müsli)",
        url="http://example.com",
    )

    assert isinstance(form.submit_button(), str)
    assert isinstance(form.redirect_html(), str)
