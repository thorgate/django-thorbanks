# -*- coding: utf-8 -*-


import random
import time

from django.urls import reverse

import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from tests.utils import (
    assert_no_errors,
    click,
    IPIZZA_BANKS,
    IS_TRAVIS,
    ready,
    select_radio,
    set_input_text,
    TIMEOUT,
)


@pytest.mark.parametrize("bank_name", IPIZZA_BANKS)
@pytest.mark.django_db
@pytest.mark.timeout(TIMEOUT)
def test_auth_flow(bank_name, live_server, selenium):
    if IS_TRAVIS:
        time.sleep(1 + random.uniform(0.5, 2.3))  # Give server time to start up

    auth_url = "%s%s" % (live_server.url, reverse("auth"))

    # Get the auth page
    selenium.get(auth_url)
    selenium.implicitly_wait(3)  # 3 seconds of grace time when there might be lag

    # wait for the page to load
    WebDriverWait(selenium, 10).until(expected_conditions.title_contains("Thorbanks"))

    # Also wait for styles
    WebDriverWait(selenium, 10).until(ready)

    # Select correct radio
    select_radio("bank_name", bank_name, selenium)

    # Click Authenticate
    click('input[type="submit"]', selenium)

    # Wait for the banks test page to load
    WebDriverWait(selenium, 10).until(
        expected_conditions.title_contains("Pangalink-net")
    )

    # Also wait for styles
    WebDriverWait(selenium, 10).until(ready)

    # Check that there are no errors
    assert_no_errors(selenium)

    # Set custom values for name and personal id
    set_input_text("authUserName", "Tõõgera Leõpäöldi", selenium)
    set_input_text("authUserId", "51001091072", selenium)

    # Click submit
    click('button[type="submit"]', selenium)

    # Wait until return button is clickable
    WebDriverWait(selenium, 10).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-button="return"]')
        )
    )

    # Click the return button
    click('[data-button="return"]', selenium)

    # Wait until we are redirected back to example app
    WebDriverWait(selenium, 10).until(expected_conditions.title_contains("Thorbanks"))

    # Assert correct result
    result = selenium.find_element(By.CSS_SELECTOR, "[data-result]")
    assert result and result.text == "success"

    # Assert name
    result = selenium.find_element(By.CSS_SELECTOR, "[data-name]")
    assert result and result.text == "Tõõgera Leõpäöldi"

    # Assert person code
    result = selenium.find_element(By.CSS_SELECTOR, "[data-code]")
    assert result and result.text == "51001091072"
