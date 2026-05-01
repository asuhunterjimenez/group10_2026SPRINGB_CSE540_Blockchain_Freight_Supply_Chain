const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("💰 Payment Contract - Full Security & Role Tests", function () {

    let contract;
    let owner, finance, sales, client, attacker, destination;

    const txId = "TXN-216-1776609533"; // sample transaction Id

    beforeEach(async function () {
        [owner, finance, sales, client, attacker, destination] = await ethers.getSigners();

        const Payment = await ethers.getContractFactory("Payment");
        contract = await Payment.deploy(destination.address);
        await contract.waitForDeployment();

        // Setup roles
        await contract.addFinance(finance.address);
        await contract.addSales(sales.address);
    });

    // -------------------------------------------
    // HELPER
    // -------------------------------------------
    const buildPayment = (amount) => ({
        quote_request_id: "Q1",
        transaction_id: txId,
        payment_type: "ETH",
        amount: amount,
        amount_purpose: "deposit",
        blockchain_gas_amount: 0,
        payer: ethers.ZeroAddress, 
        status: "",
        created_at: 0,
        created_by: "client",
        payment_email_sent: false,
        user_id: "U1",
        transaction_hash: "0xhash",
        confirmed_at: 0
    });

    // -------------------------------------------
    // DEPLOYMENT TESTS
    // -------------------------------------------

    it("❌ Should fail deployment with zero address destination", async function () {
        const Payment = await ethers.getContractFactory("Payment");

        await expect(
            Payment.deploy(ethers.ZeroAddress)
        ).to.be.revertedWith("Invalid destination");
    });

    // -------------------------------------------
    // CREATE PAYMENT TESTS
    // -------------------------------------------

    it("✅ Should create payment successfully", async function () {
        const amount = ethers.parseEther("1");

        await expect(
            contract.connect(client).createPayment(
                buildPayment(amount),
                { value: amount }
            )
        ).to.emit(contract, "PaymentCreated");

        expect(await contract.paymentExists(txId)).to.equal(true);
    });

    it("❌ Should reject zero ETH payments (security: free transaction attempt)", async function () {
        await expect(
            contract.connect(client).createPayment(
                buildPayment(0),
                { value: 0 }
            )
        ).to.be.revertedWith("ETH required");
    });

    it("❌ Should fail if amount mismatch (anti-fraud check)", async function () {
        const realValue = ethers.parseEther("1");
        const fakeValue = ethers.parseEther("5");

        await expect(
            contract.connect(client).createPayment(
                buildPayment(fakeValue), // fake declared
                { value: realValue }     // actual sent
            )
        ).to.be.revertedWith("Amount mismatch");
    });

    it("❌ Should not allow empty transaction ID", async function () {
        const payment = buildPayment(1000);
        payment.transaction_id = "";

        await expect(
            contract.connect(client).createPayment(payment, { value: 1000 })
        ).to.be.revertedWith("Transaction ID required");
    });

    it("❌ Should prevent duplicate payments (replay attack)", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        await expect(
            contract.connect(client).createPayment(
                buildPayment(amount),
                { value: amount }
            )
        ).to.be.revertedWith("Payment exists");
    });

    it("❌ Should not allow negative ETH (uint256 enforced)", async function () {
        const invalidAmount = -100;

        await expect(
            contract.connect(client).createPayment(
                buildPayment(invalidAmount),
                { value: invalidAmount }
            )
        ).to.be.rejected; // fails before hitting contract
    });

    it("✅ Should enforce payer as msg.sender (wallet integrity)", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        const payment = await contract.connect(sales).getPayment(txId);
        expect(payment.payer).to.equal(client.address);
    });

    // -------------------------------------------
    // ROLE-BASED ACCESS TESTS
    // -------------------------------------------

    it("❌ Should block unauthorized user from viewing payment", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        await expect(
            contract.connect(attacker).getPayment(txId)
        ).to.be.revertedWith("Not sales");
    });

    it("✅ Sales should view payment", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        const payment = await contract.connect(sales).getPayment(txId);
        expect(payment.transaction_id).to.equal(txId);
    });

    it("❌ Non-finance cannot verify payment", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        await expect(
            contract.connect(sales).verifyPayment(txId, "verified", 123)
        ).to.be.revertedWith("Not finance");
    });

    // -------------------------------------------
    // VERIFY PAYMENT TESTS
    // -------------------------------------------

    it("✅ Finance can verify payment", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        await expect(
            contract.connect(finance).verifyPayment(txId, "verified", 123)
        ).to.emit(contract, "PaymentVerified");

        const payment = await contract.connect(finance).getPayment(txId);
        expect(payment.status).to.equal("verified");
    });

    it("❌ Should reject invalid status", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        await expect(
            contract.connect(finance).verifyPayment(txId, "invalid", 123)
        ).to.be.revertedWith("Invalid status");
    });

    it("❌ Should fail verifying non-existent payment", async function () {
        await expect(
            contract.connect(finance).verifyPayment("BAD", "verified", 123)
        ).to.be.revertedWith("Payment not found");
    });

    // -------------------------------------------
    // EMAIL MARKING
    // -------------------------------------------

    it("✅ Finance can mark email sent", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        await expect(
            contract.connect(finance).markEmailSent(txId)
        ).to.emit(contract, "EmailMarkedSent");

        const payment = await contract.connect(finance).getPayment(txId);
        expect(payment.payment_email_sent).to.equal(true);
    });

    it("❌ Non-finance cannot mark email", async function () {
        const amount = ethers.parseEther("1");

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        await expect(
            contract.connect(sales).markEmailSent(txId)
        ).to.be.revertedWith("Not finance");
    });

    // -------------------------------------------
    // DESTINATION TRANSFER TEST
    // -------------------------------------------

    it("✅ Should forward ETH to destination", async function () {
        const amount = ethers.parseEther("1");

        const before = await ethers.provider.getBalance(destination.address);

        await contract.connect(client).createPayment(
            buildPayment(amount),
            { value: amount }
        );

        const after = await ethers.provider.getBalance(destination.address);

        expect(after - before).to.equal(amount);
    });

    // -------------------------------------------
    // EDGE CASES
    // -------------------------------------------

    it("❌ Should fail getting non-existent payment", async function () {
        await expect(
            contract.connect(sales).getPayment("BAD")
        ).to.be.revertedWith("Not found");
    });

    it("✅ paymentExists should return false for unknown", async function () {
        expect(await contract.paymentExists("NONE")).to.equal(false);
    });

});