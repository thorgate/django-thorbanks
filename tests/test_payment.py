# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import pytest
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from django.core.urlresolvers import reverse

from tests.utils import select_radio, click, IPIZZA_BANKS, ready, set_input_text, assert_no_errors, IS_TRAVIS, TIMEOUT


@pytest.mark.parametrize("bank_name", IPIZZA_BANKS)
@pytest.mark.parametrize("send_ref", [True, False])
@pytest.mark.django_db
@pytest.mark.timeout(TIMEOUT)
def test_payment_flow(bank_name, send_ref, live_server, selenium):
    from shop.models import Order
    from thorbanks.models import Transaction

    assert bank_name in IPIZZA_BANKS

    if IS_TRAVIS:
        time.sleep(1 + random.uniform(0.5, 2.3))  # Give server time to start up

    pay_url = '%s%s?send_ref=%d' % (live_server.url, reverse('payment'), 1 if send_ref else 0)

    # Get the order page
    selenium.get(pay_url)
    selenium.implicitly_wait(3)  # 3 seconds of grace time when there might be lag

    # wait for the page to load
    WebDriverWait(selenium, 10).until(
        expected_conditions.title_contains('Thorbanks')
    )

    # Also wait for styles
    WebDriverWait(selenium, 10).until(ready)

    # Set amount to a random value
    amount = round(random.uniform(0.1, 5000), 5)
    set_input_text('amount', str(amount), selenium)

    # Select correct radio
    select_radio('bank_name', bank_name, selenium)

    # Click Pay
    click('input[type="submit"]', selenium)

    # Wait for the banks test page to load
    WebDriverWait(selenium, 10).until(
        expected_conditions.title_contains('Pangalink-net')
    )

    # Also wait for styles
    WebDriverWait(selenium, 10).until(ready)

    # Check that there are no errors
    assert_no_errors(selenium)

    # Set custom value for name
    set_input_text('senderName', 'Tõõgera Leõpäöldi', selenium)

    # Check that the amount is correct
    elem = selenium.find_element_by_css_selector('form table tr:last-child td:last-child')
    assert elem
    assert elem.text.replace(' ', '') == ('%.2f€' % amount).replace('.', ',')

    # Click submit
    click('button[type="submit"]', selenium)

    # Wait until return button is clickable
    WebDriverWait(selenium, 10).until(
        expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, '[data-button="return"]'))
    )

    # Click the return button
    click('[data-button="return"]', selenium)

    # Wait until we are redirected back to example app
    WebDriverWait(selenium, 10).until(
        expected_conditions.title_contains('Thorbanks')
    )

    assert 'success' in selenium.current_url
    url_parts = [x for x in selenium.current_url.split('/') if x]

    assert len(url_parts) == 5
    order_id = url_parts[-2]
    assert order_id and all([x.isdigit() for x in order_id])

    # Get the transaction from db
    order = Order.objects.get(pk=order_id)

    assert order and order.pk
    assert round(order.amount, 2) == round(amount, 2)
    assert order.is_paid

    assert order.transaction_id

    assert order.transaction.bank_name == bank_name
    assert order.transaction.amount == round(amount, 2)
    assert order.transaction.currency == 'EUR'
    assert order.transaction.status == Transaction.STATUS_COMPLETED
