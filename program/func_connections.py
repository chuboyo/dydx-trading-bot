from dydx3 import Client
from web3 import Web3
from constants import (
    HOST, 
    DYDX_API_KEY,
    DYDX_API_PASSPHRASE, 
    DYDX_API_SECRET,
    STARK_PRIVATE_KEY,
    ETH_PRIVATE_KEY,
    ETHEREUM_ADDRESS, 
    HTTP_PROVIDER
)


def connect_dydx():
    client = Client(
    host=HOST,
    api_key_credentials={
        'key': DYDX_API_KEY,
        'secret': DYDX_API_SECRET,
        'passphrase': DYDX_API_PASSPHRASE
    },
    stark_private_key=STARK_PRIVATE_KEY,
    eth_private_key=ETH_PRIVATE_KEY,
    default_ethereum_address=ETHEREUM_ADDRESS,
    web3=Web3(Web3.HTTPProvider(HTTP_PROVIDER))

    )
    account = client.private.get_account()
    account_id = account.data['account']['id']
    quote_balance = account.data['account']['quoteBalance']
    print(account_id)
    print(quote_balance)
    return client