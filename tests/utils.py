from __future__ import unicode_literals

import os

from selenium.common.exceptions import NoSuchElementException

IPIZZA_BANKS = [
    'swedbank',
    'seb',
    'lhv',
    'danske',
]

IS_TRAVIS = os.environ.get('TRAVIS', None)
TIMEOUT = 200 if IS_TRAVIS else 20


def click(selector, selenium):
    element = selenium.find_element_by_css_selector(selector)

    assert element and (not isinstance(element, list) or len(element) == 1)

    if isinstance(element, list):
        element = element[0]

    element.click()

    return element


def select_radio(name, value, selenium):
    click('input[name="%s"][value="%s"]' % (name, value), selenium)
    checked = selenium.find_element_by_css_selector('input[name="%s"]:checked' % name)

    assert checked
    assert checked.get_attribute('name') == name
    assert checked.get_attribute('value') == value


def set_input_text(name, value, selenium):
    element = click('input[name="%s"]' % name, selenium)

    element.clear()
    element.send_keys(value)
    element = selenium.find_element_by_css_selector('input[name="%s"]' % name)

    assert element
    assert element.get_attribute('name') == name
    assert element.get_attribute('value') == value


def ready(d):
    return d.execute_script("return document.readyState") == "complete"


def assert_no_errors(selenium, err_type='payment'):
    try:
        err = selenium.find_element_by_css_selector("[data-%s-error]" % err_type)

    except NoSuchElementException:
        pass

    else:
        raise AssertionError("Creating payment error: %s" % (err.text or err.get_attribute('data-payment-error')))


def assert_ex_msg(e, expected):
    if hasattr(e, 'value'):
        if isinstance(e.value, Exception):
            e = e.value

    message = getattr(e, 'message', getattr(e, 'args', ''))

    if isinstance(message, (list, tuple)):
        if message:
            message = message[0]

        else:
            message = ''

    assert message == expected
