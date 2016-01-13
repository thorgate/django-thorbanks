from __future__ import unicode_literals

import logging

from django.db import models
from django.dispatch.dispatcher import receiver

from thorbanks.signals import transaction_succeeded, transaction_failed


class Order(models.Model):
    amount = models.FloatField()

    transaction = models.OneToOneField('thorbanks.Transaction', null=True)
    is_paid = models.BooleanField(default=False)

    def complete(self):
        self.is_paid = True
        self.save()


@receiver(transaction_succeeded)
def banklink_success_callback(sender, transaction, **kwargs):
    """ Gets called when we have a confirmation from the bank that this transaction was completed.
         The logic should only be run on the first callback.
    """
    logging.info("Banklink transfer callback with transaction %s" % transaction.id)
    try:
        # Mark the order as paid
        if transaction.order:
            transaction.order.complete()

        logging.info("Transaction %d purchase completed", transaction.id)

    except Exception:
        # *WARNING*:
        # This is a very bad exception. It means the user gave us money, but for some reason we
        # couldn't give him the items(complete the purchase)
        # If this happens contact has to be made with the client to resolve the issue.
        logging.exception("Transaction %d purchase failed." % transaction.id)


@receiver(transaction_failed)
def banklink_failed_callback(sender, transaction, **kwargs):
    logging.warning("Transaction %d purchase failed." % transaction.id)
