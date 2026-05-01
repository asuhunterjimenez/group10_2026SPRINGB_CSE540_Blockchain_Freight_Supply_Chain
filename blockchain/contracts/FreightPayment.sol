// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @title Payment Contract (Secure Role-Based System: Finance + Sales + Client Payments)
contract Payment is Ownable {

    // ---------------------------------------------------
    // CORE CONFIG
    // ---------------------------------------------------
    address public destination;

    constructor(address _destination) {
        require(_destination != address(0), "Invalid destination");
        destination = _destination;

        // Owner is default finance (bootstrap access)
        isFinance[msg.sender] = true;
    }

    // ---------------------------------------------------
    // ROLES (SECURITY LAYER)
    // ---------------------------------------------------
    mapping(address => bool) public isFinance;
    mapping(address => bool) public isSales;

    // ---------------------------------------------------
    // MODIFIERS
    // ---------------------------------------------------
    modifier onlyFinance() {
        require(isFinance[msg.sender] || msg.sender == owner(), "Not finance");
        _;
    }

    modifier onlySalesOrAbove() {
        require(
            isSales[msg.sender] || isFinance[msg.sender] || msg.sender == owner(),
            "Not sales"
        );
        _;
    }

    // ---------------------------------------------------
    // ROLE MANAGEMENT (OWNER ONLY)
    // ---------------------------------------------------
    function addFinance(address user) external onlyOwner {
        require(user != address(0), "Invalid address");
        isFinance[user] = true;
    }

    function removeFinance(address user) external onlyOwner {
        isFinance[user] = false;
    }

    function addSales(address user) external onlyOwner {
        require(user != address(0), "Invalid address");
        isSales[user] = true;
    }

    function removeSales(address user) external onlyOwner {
        isSales[user] = false;
    }

    // ---------------------------------------------------
    // PAYMENT STRUCTURE
    // ---------------------------------------------------
    struct PaymentRecord {
        string quote_request_id;
        string transaction_id;
        string payment_type;
        uint256 amount;
        string amount_purpose;
        uint256 blockchain_gas_amount;

        address payer; // REAL WALLET (msg.sender enforced)

        string status; // pending | verified | rejected
        uint256 created_at;
        string created_by;
        bool payment_email_sent;
        string user_id;
        string transaction_hash;
        uint256 confirmed_at;
    }

    mapping(string => PaymentRecord) private payments;

    // ---------------------------------------------------
    // EVENTS
    // ---------------------------------------------------
    event PaymentCreated(
        string indexed transaction_id,
        uint256 amount,
        address payer
    );

    event PaymentVerified(
        string indexed transaction_id,
        string status
    );

    event EmailMarkedSent(
        string indexed transaction_id
    );

    // ---------------------------------------------------
    // CREATE PAYMENT (CLIENT ONLY)
    // ---------------------------------------------------
    function createPayment(PaymentRecord memory _payment) external payable {

        require(bytes(_payment.transaction_id).length > 0, "Transaction ID required");
        require(msg.value > 0, "ETH required");
        require(msg.value == _payment.amount, "Amount mismatch");
        require(bytes(_payment.payment_type).length > 0, "Payment type required");

        // SECURITY: real wallet identity enforced
        address payer = msg.sender;

        // Prevent duplicate payments
        require(bytes(payments[_payment.transaction_id].transaction_id).length == 0, "Payment exists");

        // Forward ETH to destination securely
        (bool sent, ) = payable(destination).call{value: msg.value}("");
        require(sent, "Transfer failed");

        // Store payment
        PaymentRecord storage p = payments[_payment.transaction_id];

        p.quote_request_id = _payment.quote_request_id;
        p.transaction_id = _payment.transaction_id;
        p.payment_type = _payment.payment_type;
        p.amount = _payment.amount;
        p.amount_purpose = _payment.amount_purpose;
        p.blockchain_gas_amount = _payment.blockchain_gas_amount;

        p.payer = payer;

        p.status = "pending";
        p.created_at = block.timestamp;
        p.created_by = _payment.created_by;
        p.payment_email_sent = false;
        p.user_id = _payment.user_id;
        p.transaction_hash = _payment.transaction_hash;
        p.confirmed_at = 0;

        emit PaymentCreated(_payment.transaction_id, _payment.amount, payer);
    }

    // ---------------------------------------------------
    // FINANCE: VERIFY PAYMENT
    // ---------------------------------------------------
    function verifyPayment(
        string memory _transaction_id,
        string memory _status,
        uint256 _confirmed_at
    ) external onlyFinance {

        PaymentRecord storage p = payments[_transaction_id];
        require(bytes(p.transaction_id).length > 0, "Payment not found");

        require(
            keccak256(bytes(_status)) == keccak256(bytes("verified")) ||
            keccak256(bytes(_status)) == keccak256(bytes("rejected")),
            "Invalid status"
        );

        p.status = _status;
        p.confirmed_at = _confirmed_at;

        emit PaymentVerified(_transaction_id, _status);
    }

    // ---------------------------------------------------
    // SALES: VIEW PAYMENT (READ ONLY)
    // ---------------------------------------------------
    function getPayment(string memory _transaction_id)
        external
        view
        onlySalesOrAbove
        returns (PaymentRecord memory)
    {
        PaymentRecord memory p = payments[_transaction_id];
        require(bytes(p.transaction_id).length > 0, "Not found");
        return p;
    }

    // ---------------------------------------------------
    // CHECK PAYMENT EXISTS (PUBLIC SAFE)
    // ---------------------------------------------------
    function paymentExists(string memory _transaction_id)
        external
        view
        returns (bool)
    {
        return bytes(payments[_transaction_id].transaction_id).length > 0;
    }

    // ---------------------------------------------------
    // EMAIL MARKING (FINANCE ONLY)
    // ---------------------------------------------------
    function markEmailSent(string memory _transaction_id)
        external
        onlyFinance
    {
        PaymentRecord storage p = payments[_transaction_id];
        require(bytes(p.transaction_id).length > 0, "Not found");

        p.payment_email_sent = true;

        emit EmailMarkedSent(_transaction_id);
    }

    // ---------------------------------------------------
    // EMERGENCY WITHDRAW (OWNER ONLY)
    // ---------------------------------------------------
    function withdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}