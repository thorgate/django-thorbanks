import random

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory

from thorbanks import settings
from thorbanks.forms import PaymentRequest
from thorbanks.utils import pingback_url, request_digest


class TestThorBanksSettings(TestCase):
    @staticmethod
    def get_banklink_config(bank_name=None, printable_name=None):
        import os

        return {
            bank_name or 'swedbank': {
                'PRINTABLE_NAME': printable_name or 'Swedbank',
                'REQUEST_URL': 'https://pangalink.net/banklink/swedbank',
                'SND_ID': 'uid513131',
                'PRIVATE_KEY': os.path.join(os.path.dirname(__file__), '..', 'example', 'certs', 'swed_key.pem'),
                'PUBLIC_KEY': os.path.join(os.path.dirname(__file__), '..', 'example', 'certs', 'swed_cert.pem'),
                'TYPE': 'banklink',
                'IMAGE_PATH': 'swedbank.png',
                'ORDER': 1,
            },
            'seb': {
                'PRINTABLE_NAME': 'SEB',
                'REQUEST_URL': 'https://pangalink.net/banklink/seb',
                'SND_ID': 'uid513157',
                'PRIVATE_KEY': os.path.join(os.path.dirname(__file__), '..', 'example', 'certs', 'seb_key.pem'),
                'PUBLIC_KEY': os.path.join(os.path.dirname(__file__), '..', 'example', 'certs', 'seb_cert.pem'),
                'DIGEST_COUNTS_BYTES': True,
                'TYPE': 'banklink',
                'IMAGE_PATH': 'seb.png',
                'ORDER': 2,
            },
            'danske': {
                'PRINTABLE_NAME': 'Danske Bank',
                'REQUEST_URL': 'https://pangalink.net/banklink/sampo',
                'SND_ID': 'uid513160',
                'PRIVATE_KEY': os.path.join(os.path.dirname(__file__), '..', 'example', 'certs', 'danske_key.pem'),
                'PUBLIC_KEY': os.path.join(os.path.dirname(__file__), '..', 'example', 'certs', 'danske_cert.pem'),
                'ENCODING': 'ISO-8859-1',
                'TYPE': 'banklink',
                'IMAGE_PATH': 'danske.png',
                'ORDER': 3,
            },
        }

    def test_no_settings_raises_exception(self):
        with self.settings(BANKLINKS=None):
            with self.assertRaisesMessage(ImproperlyConfigured, "BANKLINKS not found in settings"):
                settings.configure()

    def test_banklinks_is_not_dict(self):
        with self.settings(BANKLINKS=True):
            with self.assertRaisesMessage(ImproperlyConfigured, "settings.BANKLINKS must be dict"):
                settings.configure()

    def test_banklink_name_too_long(self):
        conf = self.get_banklink_config(bank_name="ABCDEFGHIJKLMNOPS")

        with self.settings(BANKLINKS=conf):
            with self.assertRaisesMessage(ImproperlyConfigured, "Bank's name must be at most 16 characters (ABCDEFGHIJKLMNOPS)"):
                settings.configure()

    def test_banklink_data_not_dict(self):
        with self.settings(BANKLINKS={'swedbank': None}):
            error_msg = "Each bank in settings.BANKLINKS must correspond to dict with settings of that bank"
            with self.assertRaisesMessage(ImproperlyConfigured, error_msg):
                settings.configure()

    def test_banklink_private_key_missing(self):
        conf = self.get_banklink_config()
        del conf['swedbank']['PRIVATE_KEY']

        with self.settings(BANKLINKS=conf):
            with self.assertRaisesMessage(ImproperlyConfigured, "PRIVATE_KEY not found in settings for bank %s" % "swedbank"):
                settings.configure()

    def test_banklink_public_key_missing(self):
        conf = self.get_banklink_config()
        del conf['swedbank']['PUBLIC_KEY']

        with self.settings(BANKLINKS=conf):
            with self.assertRaisesMessage(ImproperlyConfigured, "PUBLIC_KEY not found in settings for bank %s" % "swedbank"):
                settings.configure()

    def test_banklink_snd_id_missing(self):
        conf = self.get_banklink_config()
        del conf['swedbank']['SND_ID']

        with self.settings(BANKLINKS=conf):
            with self.assertRaisesMessage(ImproperlyConfigured, "SND_ID not found in settings for bank %s" % "swedbank"):
                settings.configure()

    def test_banklink_request_url_missing(self):
        conf = self.get_banklink_config()
        del conf['swedbank']['REQUEST_URL']

        with self.settings(BANKLINKS=conf):
            with self.assertRaisesMessage(ImproperlyConfigured, "REQUEST_URL not found in settings for bank %s" % "swedbank"):
                settings.configure()

    def test_banklink_no_private_key_file(self):
        conf = self.get_banklink_config()
        conf['swedbank']['PRIVATE_KEY'] = "rand_name_%d.key" % random.randint(1, 999999)

        with self.settings(BANKLINKS=conf):
            error_msg = "Private key file %s for bank swedbank does not exist." % conf['swedbank']['PRIVATE_KEY']
            with self.assertRaisesMessage(ImproperlyConfigured, error_msg):
                settings.configure()

    def test_banklink_no_public_key_file(self):
        conf = self.get_banklink_config()
        conf['swedbank']['PUBLIC_KEY'] = "rand_name_%d.key" % random.randint(1, 999999)

        with self.settings(BANKLINKS=conf):
            error_msg = "Public key file %s for bank swedbank does not exist." % conf['swedbank']['PUBLIC_KEY']
            with self.assertRaisesMessage(ImproperlyConfigured, error_msg):
                settings.configure()

    def test_getters(self):
        conf = self.get_banklink_config()

        with self.settings(BANKLINKS=conf):
            settings.configure()

            self.assertEqual(settings.get_private_key("swedbank"), conf["swedbank"]["PRIVATE_KEY"])
            self.assertEqual(settings.get_public_key("swedbank"), conf["swedbank"]["PUBLIC_KEY"])
            self.assertEqual(settings.get_snd_id("swedbank"), conf["swedbank"]["SND_ID"])
            self.assertEqual(settings.get_request_url("swedbank"), conf["swedbank"]["REQUEST_URL"])
            self.assertEqual(settings.get_link_type("swedbank"), conf["swedbank"]["TYPE"])

            self.assertEqual(settings.get_digest_counts_bytes("swedbank"), False)
            self.assertEqual(settings.get_digest_counts_bytes("seb"), True)

            self.assertEqual(settings.get_encoding("swedbank"), 'UTF-8')
            self.assertEqual(settings.get_encoding("danske"), conf["danske"]["ENCODING"])

            the_list = settings.get_bank_choices()
            self.assertTrue(isinstance(the_list, list))

            for item in the_list:
                self.assertTrue(isinstance(item, tuple))

                self.assertEqual(len(item), 4)
                self.assertTrue(item[0] in conf.keys())
                self.assertEqual(item[1], conf[item[0]]['PRINTABLE_NAME'])
                self.assertEqual(item[2], conf[item[0]]['IMAGE_PATH'])
                self.assertEqual(item[3], conf[item[0]].get('ORDER', 99))

    def test_ensure_imports(self):
        """ This test is currently used to make coverage report correctly for all files in this project.
        """


class TestTransactionModel(TestCase):
    def test_str_method(self):
        trans = settings.get_model('Transaction')(pk=1, currency='EUR', amount=15.67, bank_name='myBank')

        self.assertEqual(trans.__str__(), "Transaction 1 - EUR 15.67 from myBank [pending]")


class TestPaymentFlow(TestCase):
    def test_pingback_with_request(self):
        factory = RequestFactory()
        request = factory.get('/test', HTTP_HOST='127.0.0.1')

        ping_back = pingback_url(request=request)

        self.assertEqual(ping_back, 'http://%s%s' % (request.META['HTTP_HOST'], reverse('thorbanks_response')))

    def test_payment_request(self):
        conf = TestThorBanksSettings.get_banklink_config()

        with self.settings(BANKLINKS=conf):
            settings.configure()

            redirect_to = "http://example.com"
            ping_back = pingback_url(base_url=redirect_to)

            self.assertEqual(ping_back, redirect_to + reverse('thorbanks_response'))

            request = PaymentRequest(
                bank_name="swedbank",
                amount=13.99,
                currency='EUR',
                redirect_to=redirect_to,
                redirect_on_failure=redirect_to,
                message="My cool payment",
                url=ping_back,
            )

            self.assertEqual(request.transaction.bank_name, "swedbank")
            self.assertEqual(request.transaction.amount, 13.99)
            self.assertEqual(request.transaction.currency, 'EUR')
            self.assertEqual(request.transaction.redirect_after_success, redirect_to)
            self.assertEqual(request.transaction.redirect_on_failure, redirect_to)
            self.assertEqual(request['VK_RETURN'].value(), ping_back)

            self.assertEqual(request_digest(request.cleaned_data, request.transaction.bank_name),
                             b'0041002003008009uid513131001100513.99003EUR00213015My cool payment')

            # NOTE: This test will only work with the original certificate.
            self.assertEqual(request['VK_MAC'].value(),
                             b'pFNyPhXm4xRj7RIVwTSSDCFvhtMV/VksaeMIxPbeFXXNaOZtDeKGGOMVkWDWm4alMJ7v4gX'
                             b'0bVFadXeLH4FpDfaxawHcS+GLKxEh4l4QY6n+VtxVRmshymOkwrzhQYR4liYX7aS5lnVVS7'
                             b'vJdzF4f9hvVEmE3d7E7Ecj9A4d5mOOGmaR3h9J1eK+jllP1p64H5s/HVoKN7pB5ITkslbHr'
                             b'ybflAsPzqoCZlNiGL+N4SxIsV08MrHcKI7HgERqsOQzDyNwZHEwC9G04+nOTlwPQT/gE9gp'
                             b'MDpRwVkZrbLeePn/l5o9fBVX2nqL27GOaEBUXqTKlHAX1bRiwbly6bV+vg==')
