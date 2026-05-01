from django.test import TestCase
from unittest.mock import patch, MagicMock

# Import your function
from apps.Payments.blockchain_service import save_payment_to_blockchain


class BlockchainServiceTests(TestCase):

    @patch("apps.Payments.blockchain_service.w3")
    @patch("apps.Payments.blockchain_service.contract")
    def test_save_payment_success(self, mock_contract, mock_w3):
        """
        ✅ Test successful blockchain transaction
        """

        # --- Mock account ---
        mock_account = MagicMock()
        mock_account.address = "0x123"

        mock_w3.eth.account.from_key.return_value = mock_account

        # --- Mock nonce ---
        mock_w3.eth.get_transaction_count.return_value = 1

        # --- Mock contract function ---
        mock_function = MagicMock()
        mock_contract.functions.createPayment.return_value = mock_function

        mock_tx = {"tx": "data"}
        mock_function.build_transaction.return_value = mock_tx

        # --- Mock signing ---
        mock_signed_tx = MagicMock()
        mock_signed_tx.raw_transaction = b"signed"

        mock_w3.eth.account.sign_transaction.return_value = mock_signed_tx

        # --- Mock tx hash ---
        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = "0xabc123"

        mock_w3.eth.send_raw_transaction.return_value = mock_tx_hash

        # --- Mock receipt ---
        mock_receipt = {"status": 1}
        mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

        # --- Call function ---
        tx_hash, receipt = save_payment_to_blockchain(
            payment_data="test_payment",
            owner_private_key="fake_private_key"
        )

        # --- Assertions ---
        self.assertEqual(tx_hash, "0xabc123")
        self.assertEqual(receipt, mock_receipt)

        mock_contract.functions.createPayment.assert_called_once_with("test_payment")
        mock_function.build_transaction.assert_called_once()
        mock_w3.eth.account.sign_transaction.assert_called_once()
        mock_w3.eth.send_raw_transaction.assert_called_once()

    @patch("apps.Payments.blockchain_service.w3")
    @patch("apps.Payments.blockchain_service.contract")
    def test_transaction_failure_raises_exception(self, mock_contract, mock_w3):
        """
        ❌ Test failure when sending transaction fails
        """

        mock_account = MagicMock()
        mock_account.address = "0x123"
        mock_w3.eth.account.from_key.return_value = mock_account

        mock_w3.eth.get_transaction_count.return_value = 1

        mock_function = MagicMock()
        mock_contract.functions.createPayment.return_value = mock_function
        mock_function.build_transaction.return_value = {}

        mock_w3.eth.account.sign_transaction.return_value = MagicMock(
            raw_transaction=b"signed"
        )

        # Simulate failure
        mock_w3.eth.send_raw_transaction.side_effect = Exception("Blockchain error")

        with self.assertRaises(Exception):
            save_payment_to_blockchain(
                payment_data="fail_test",
                owner_private_key="fake_key"
            )

    @patch("apps.Payments.blockchain_service.w3")
    def test_invalid_private_key(self, mock_w3):
        """
        ❌ Test invalid private key handling
        """

        mock_w3.eth.account.from_key.side_effect = Exception("Invalid key")

        with self.assertRaises(Exception):
            save_payment_to_blockchain(
                payment_data="data",
                owner_private_key="bad_key"
            )

    @patch("apps.Payments.blockchain_service.w3")
    @patch("apps.Payments.blockchain_service.contract")
    def test_receipt_wait_called(self, mock_contract, mock_w3):
        """
        ✅ Ensure receipt waiting is triggered
        """

        mock_account = MagicMock(address="0x123")
        mock_w3.eth.account.from_key.return_value = mock_account
        mock_w3.eth.get_transaction_count.return_value = 1

        mock_function = MagicMock()
        mock_contract.functions.createPayment.return_value = mock_function
        mock_function.build_transaction.return_value = {}

        mock_w3.eth.account.sign_transaction.return_value = MagicMock(
            raw_transaction=b"signed"
        )

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = "0xhash"
        mock_w3.eth.send_raw_transaction.return_value = mock_tx_hash

        mock_w3.eth.wait_for_transaction_receipt.return_value = {"status": 1}

        save_payment_to_blockchain("data", "key")

        mock_w3.eth.wait_for_transaction_receipt.assert_called_once()

    @patch("apps.Payments.blockchain_service.w3")
    @patch("apps.Payments.blockchain_service.contract")
    def test_gas_and_gas_price_set(self, mock_contract, mock_w3):
        """
        ✅ Ensure gas + gasPrice are included in transaction
        """

        mock_account = MagicMock(address="0x123")
        mock_w3.eth.account.from_key.return_value = mock_account
        mock_w3.eth.get_transaction_count.return_value = 1

        mock_function = MagicMock()
        mock_contract.functions.createPayment.return_value = mock_function

        captured_tx = {}

        def capture_tx(tx):
            captured_tx.update(tx)
            return tx

        mock_function.build_transaction.side_effect = capture_tx

        mock_w3.eth.account.sign_transaction.return_value = MagicMock(
            raw_transaction=b"signed"
        )

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = "0xhash"
        mock_w3.eth.send_raw_transaction.return_value = mock_tx_hash
        mock_w3.eth.wait_for_transaction_receipt.return_value = {"status": 1}

        save_payment_to_blockchain("data", "key")

        self.assertIn("gas", captured_tx)
        self.assertIn("gasPrice", captured_tx)