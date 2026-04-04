from web3 import Web3
from django.conf import settings

w3 = Web3(Web3.HTTPProvider(settings.GANACHE_URL))
contract_address = Web3.to_checksum_address(settings.PAYMENT_CONTRACT_ADDRESS)

contract = w3.eth.contract(address=contract_address, abi=settings.PAYMENT_CONTRACT_ABI)

payment = contract.functions.getPayment("TXN-154-1-1700000000").call()
print(payment)