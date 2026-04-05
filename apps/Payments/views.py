from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from web3 import Web3
from django.conf import settings
from .models import blockchain_payment
from django.utils import timezone
from decimal import Decimal
from django.core.mail import send_mail
from apps.Helpers.decorators import send_quote_email

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider(settings.GANACHE_URL))

# Contract info
contract_address = Web3.to_checksum_address(settings.PAYMENT_CONTRACT_ADDRESS)
contract_abi = settings.PAYMENT_CONTRACT_ABI
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Destination account where ETH will be sent
DESTINATION_ACCOUNT = settings.COMPANY_MAIN_WALLET  #ganache account 2


@login_required
def create_blockchain_payment(request):
    """
    Save ETH payment to Ganache and store off-chain safely.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    try:
        # Extract data from POST
        booking_id = request.POST.get("booking_id")
        quote_request_id = request.POST.get("quote_request_id")
        total_payment = Decimal(request.POST.get("total_charges", "0"))
        amount = Decimal(request.POST.get("amount", "0"))
        wallet_address = Web3.to_checksum_address(request.POST.get("wallet_address"))
        transaction_id = request.POST.get("transaction_id")

        # Connect Web3
        web3 = w3
        amount_wei = web3.to_wei(amount, 'ether')

        # Send ETH to destination account using user's MetaMask (frontend already sends TX)
        # Just validate transaction hash
        transaction_hash = request.POST.get("transaction_hash")

        # Gas fees from frontend (Wei)
        blockchain_gas_amount = int(request.POST.get("blockchain_gas_amount", 0))
        gas_fee_eth = Decimal(web3.from_wei(blockchain_gas_amount, 'ether'))

        #Save off-chain safely in DB
        balance_after_payment = total_payment - amount

        blockchain_payment.objects.create(
            user=request.user.username,
            quote_request_id=quote_request_id,
            transaction_id=transaction_id,
            total_charges=total_payment,
            paid_amount=amount,
            balance=balance_after_payment,
            blockchain_gas_fees=gas_fee_eth,
            date_created=timezone.now()
        )

        return JsonResponse({
            "success": True,
            "transaction_id": transaction_id,
            "transaction_hash": transaction_hash
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@login_required
def payment_success(request):
    try:
        # Fetch latest payment for the logged-in user
        latest_payment = blockchain_payment.objects.filter(user=request.user.username) \
                                                  .order_by('-id').first()
        if not latest_payment:
            messages.error(request, "No payment record found.")
            return render(request, "Payments/cancel.html")

        # Call smart contract for on-chain info
        tx_id = latest_payment.transaction_id
        payment_on_chain = contract.functions.getPayment(tx_id).call()

        # Safe type conversions
        amount_wei = int(payment_on_chain[3])
        amount_eth = Decimal(w3.from_wei(amount_wei, 'ether'))
        blockchain_gas_eth = Decimal(latest_payment.blockchain_gas_fees)

        payment_data = {
            "quote_request_id": payment_on_chain[0],
            "transaction_id": payment_on_chain[1],
            "payment_type": payment_on_chain[2],
            "amount_purpose": payment_on_chain[4],
            "total_charges": latest_payment.total_charges,
            "amount_eth": amount_eth,
            "balance_after_payment": latest_payment.balance,
            "blockchain_gas_eth": blockchain_gas_eth,
            "your_wallet_was_charged": amount_eth + blockchain_gas_eth,
            "source_wallet": payment_on_chain[6],
            "status": "Success" if payment_on_chain[7] == "completed" else payment_on_chain[7],
            "created_by": payment_on_chain[9],
            "transaction_hash": payment_on_chain[12],
            "created_at_dt": latest_payment.date_created,
            "transacted_by": request.user.get_full_name()
        }
        
        # Send email notification
        send_quote_email(
            record,
            service_type,
            request_id,
            first_hidden.capitalize(),
            user_email_hidden,
            company_email_hidden
        )

        return render(request, "Payments/success.html", payment_data)

    except Exception as e:
        messages.error(request, f"Blockchain payment not found: {e}")
        return render(request, "Payments/cancel.html")

@login_required
def payment_cancel(request):
    messages.error(request, "Payment not completed or already processed.")
    return render(request, "Payments/cancel.html")