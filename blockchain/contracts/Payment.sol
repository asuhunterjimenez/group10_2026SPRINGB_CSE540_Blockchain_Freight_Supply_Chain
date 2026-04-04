// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

import "@openzeppelin/contracts@4.9.6/access/Ownable.sol";

/// @title Payment Contract
/// @notice Handles creation, tracking, ETH forwarding, and email status of payments
contract Payment is Ownable {

    // Destination address where all incoming ETH payments are forwarded
    address public destination;

    constructor(address _destination) {
        require(_destination != address(0), "Invalid destination");
        destination = _destination;
    }

    /// @notice Struct representing a single payment
    struct PaymentRecord {
        string quote_request_id;     // Unique ID of the quote or request (string)
        string transaction_id;       // Unique transaction ID for this payment (string)
        string payment_type;         // Type of payment (e.g., "ETH") (string)
        uint256 amount;              // Amount paid in wei (uint256)
        string amount_purpose;       // Purpose of the payment (e.g., "initial_deposit") (string)
        uint256 blockchain_gas_amount; // Gas fees used for the transaction in wei (uint256)
        string source_wallet;        // Wallet address of payer (string)
        string status;               // Payment status (e.g., "completed", "pending") (string)
        uint256 created_at;          // Timestamp when payment was created on-chain (uint256)
        string created_by;           // User who created the payment record (string)
        bool payment_email_sent;     // Flag if payment email was sent (bool)
        string user_id;              // User ID (string) – must be sent as string from JS
        string transaction_hash;     // Blockchain transaction hash (string)
        uint256 confirmed_at;        // Timestamp when payment was confirmed (uint256)
    }

    // Mapping from transaction_id to payment record
    mapping(string => PaymentRecord) private payments;

    // Events
    event PaymentCreated(string indexed transaction_id, uint256 amount, string status);
    event EmailMarkedSent(string indexed transaction_id);

    /// @notice Create a new payment and forward ETH to the destination address
    /// @param _payment Struct containing all payment details
    function createPayment(PaymentRecord memory _payment) external payable {
        require(bytes(_payment.transaction_id).length > 0, "Transaction ID required");
        require(msg.value > 0, "ETH amount must be greater than zero");
        require(msg.value == _payment.amount, "Sent ETH must match payment amount");
        require(bytes(_payment.payment_type).length > 0, "Payment type required");

        // Forward ETH to the destination address
        (bool sent, ) = payable(destination).call{value: msg.value}("");
        require(sent, "Failed to forward ETH");

        // Store payment info on-chain
        PaymentRecord storage p = payments[_payment.transaction_id];
        p.quote_request_id = _payment.quote_request_id;
        p.transaction_id = _payment.transaction_id;
        p.payment_type = _payment.payment_type;
        p.amount = _payment.amount;
        p.amount_purpose = _payment.amount_purpose;
        p.blockchain_gas_amount = _payment.blockchain_gas_amount;
        p.source_wallet = _payment.source_wallet;
        p.status = _payment.status;
        p.created_at = block.timestamp;       // On-chain timestamp
        p.created_by = _payment.created_by;
        p.payment_email_sent = false;         // Always false on creation
        p.user_id = _payment.user_id;
        p.transaction_hash = _payment.transaction_hash;
        p.confirmed_at = _payment.confirmed_at;

        // Emit event for front-end / logging
        emit PaymentCreated(_payment.transaction_id, _payment.amount, _payment.status);
    }

    /// @notice Get payment info by transaction ID
    /// @param _transaction_id The unique transaction ID
    /// @return PaymentRecord struct
    function getPayment(string memory _transaction_id) external view returns (PaymentRecord memory) {
        PaymentRecord memory p = payments[_transaction_id];
        require(bytes(p.transaction_id).length > 0, "Payment does not exist");
        return p;
    }

    /// @notice Mark that the payment email has been sent
    function markEmailSent(string memory _transaction_id) external onlyOwner {
        PaymentRecord storage p = payments[_transaction_id];
        require(bytes(p.transaction_id).length > 0, "Payment does not exist");
        p.payment_email_sent = true;
        emit EmailMarkedSent(_transaction_id);
    }

    /// @notice Check if a payment exists
    function paymentExists(string memory _transaction_id) external view returns (bool) {
        return bytes(payments[_transaction_id].transaction_id).length > 0;
    }

    /// @notice Withdraw remaining ETH from the contract (if any)
    function withdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}