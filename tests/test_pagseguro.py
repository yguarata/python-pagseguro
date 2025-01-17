# -*- coding: utf-8 -*-
import pytest

from pagseguro import PagSeguro, PagSeguroTransactionSearchResult
from pagseguro.config import Config
from pagseguro.exceptions import PagSeguroValidationError
from pagseguro.utils import is_valid_email, is_valid_cpf

TOKEN = '123456'
EMAIL = 'seu@email.com'


@pytest.fixture
def pagseguro():
    return PagSeguro(token=TOKEN, email=EMAIL)


@pytest.fixture
def xml():
    return """
<transactionSearchResult>
    <date>2011-02-16T20:14:35.000-02:00</date>
    <currentPage>1</currentPage>
    <resultsInThisPage>2</resultsInThisPage>
    <totalPages>1</totalPages>
    <transactions>
        <transaction>
            <date>2011-02-05T15:46:12.000-02:00</date>
            <lastEventDate>2011-02-15T17:39:14.000-03:00</lastEventDate>
            <code>9E884542-81B3-4419-9A75-BCC6FB495EF1</code>
            <reference>REF1234</reference>
            <type>1</type>
            <status>3</status>
            <paymentMethod>
                <type>1</type>
            </paymentMethod>
            <grossAmount>49900.00</grossAmount>
            <discountAmount>0.00</discountAmount>
            <feeAmount>0.00</feeAmount>
            <netAmount>49900.00</netAmount>
            <extraAmount>0.00</extraAmount>
        </transaction>
        <transaction>
            <date>2011-02-07T18:57:52.000-02:00</date>
            <lastEventDate>2011-02-14T21:37:24.000-03:00</lastEventDate>
            <code>2FB07A22-68FF-4F83-A356-24153A0C05E1</code>
            <reference>REF5678</reference>
            <type>3</type>
            <status>4</status>
            <paymentMethod>
                <type>3</type>
            </paymentMethod>
            <grossAmount>26900.00</grossAmount>
            <discountAmount>0.00</discountAmount>
            <feeAmount>0.00</feeAmount>
            <netAmount>26900.00</netAmount>
            <extraAmount>0.00</extraAmount>
        </transaction>
    </transactions>
</transactionSearchResult>"""


def test_pagseguro_class(pagseguro):
    assert isinstance(pagseguro, PagSeguro)


def test_pagseguro_initial_attrs(pagseguro):
    assert isinstance(pagseguro.config, Config)
    assert isinstance(pagseguro.data, dict)
    assert 'email' in pagseguro.data
    assert 'token' in pagseguro.data
    assert pagseguro.data['email'] == EMAIL
    assert pagseguro.data['token'] == TOKEN
    assert isinstance(pagseguro.items, list)
    assert isinstance(pagseguro.sender, dict)
    assert isinstance(pagseguro.shipping, dict)
    assert pagseguro._reference == ''
    assert pagseguro.extra_amount is None
    assert pagseguro.redirect_url is None
    assert pagseguro.notification_url is None
    assert pagseguro.abandon_url is None


def test_build_checkout_params_with_all_params(pagseguro, sender, shipping,
                                               items):
    pagseguro.sender = sender
    pagseguro.shipping = shipping
    pagseguro.extra_amount = 12.50
    pagseguro.redirect_url = '/redirecionando/'
    pagseguro.abandon_url = '/abandonando/'
    pagseguro.items = items
    pagseguro.build_checkout_params()

    # check all data fields
    assert isinstance(pagseguro.data, dict)
    keys = ['email', 'token', 'senderName', 'senderAreaCode',
            'senderPhone', 'senderEmail', 'senderCPF', 'senderBornDate',
            'shippingType', 'shippingAddressStreet',
            'shippingAddressNumber', 'shippingAddressComplement',
            'shippingAddressDistrict', 'shippingAddressPostalCode',
            'shippingAddressCity', 'shippingAddressState',
            'shippingAddressCountry', 'shippingCost', 'extraAmount',
            'redirectURL', 'abandonURL']
    # items
    item_keys = ['itemId{}', 'itemDescription{}', 'itemAmount{}',
                 'itemQuantity{}', 'itemWeight{}']

    for key in keys:
        assert key in pagseguro.data

    for i, key in enumerate(pagseguro.items, 1):
        keys_to_compare = [x.format(i) for x in item_keys]
        for item_key in keys_to_compare:
            assert item_key in pagseguro.data


def test_add_items_util(items):
    pagseguro = PagSeguro(token=TOKEN, email=EMAIL)
    pagseguro.add_item(**items[0])
    pagseguro.add_item(**items[1])
    assert len(pagseguro.items) == 2


def test_reference(pagseguro):
    pagseguro.reference = '12345'
    assert pagseguro.reference == u'REF12345'


def test_clean_none_params(sender):
    pagseguro = PagSeguro(email=EMAIL, token=TOKEN)
    sender_copy = sender.copy()
    sender_copy['cpf'] = None
    sender_copy['born_date'] = None
    pagseguro.sender = sender_copy
    pagseguro.build_checkout_params()
    assert 'senderCPF' not in pagseguro.data
    assert 'senderBornData' not in pagseguro.data


def test_is_valid_email(sender):
    bad_email = 'john.com'
    pagseguro = PagSeguro(email=bad_email, token=TOKEN)
    pagseguro.sender = {'email': bad_email}
    with pytest.raises(PagSeguroValidationError):
        pagseguro.build_checkout_params()

    # Now testing with a valid email
    pagseguro.sender['email'] = sender['email']
    assert is_valid_email(pagseguro.sender['email']) == sender['email']


def test_is_valid_cpf():
    bad_cpf = '123.456.267-45'
    pagseguro = PagSeguro(email=EMAIL, token=TOKEN)
    pagseguro.sender = {'cpf': bad_cpf}

    with pytest.raises(PagSeguroValidationError):
        pagseguro.build_checkout_params()

    # Now testing with a valid email
    pagseguro.sender['cpf'] = '482.268.465-28'
    assert is_valid_cpf(pagseguro.sender['cpf']) == pagseguro.sender['cpf']

    pagseguro.sender['cpf'] = '48226846528'
    assert is_valid_cpf(pagseguro.sender['cpf']) == pagseguro.sender['cpf']


def test_parse_xml(xml):
    pg = PagSeguro(email=EMAIL, token=TOKEN)
    result = PagSeguroTransactionSearchResult(xml, pg.config)
    assert result.current_page == 1
    assert result.results_in_page == 2
    assert result.total_pages == 1
    assert len(result.transactions) == 2


def test_pagseguro_with_bad_config():
    with pytest.raises(Exception):
        PagSeguro(email=EMAIL, token=TOKEN, config=2)
