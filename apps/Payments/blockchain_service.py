# apps/Payments/blockchain_service.py
import json
from web3 import Web3
from django.conf import settings

w3 = Web3(Web3.HTTPProvider(settings.GANACHE_URL))

contract = w3.eth.contract(
    address=Web3.to_checksum_address(settings.PAYMENT_CONTRACT_ADDRESS),
    abi=settings.PAYMENT_CONTRACT_ABI
)

def save_payment_to_blockchain(payment_data, owner_private_key):
    owner = w3.eth.account.from_key(owner_private_key)

    nonce = w3.eth.get_transaction_count(owner.address)

    tx = contract.functions.createPayment(payment_data).build_transaction({
        "from": owner.address,
        "nonce": nonce,
        "gas": 3000000,
        "gasPrice": w3.to_wei("20", "gwei")
    })

    signed_tx = w3.eth.account.sign_transaction(tx, owner_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_hash.hex(), receipt