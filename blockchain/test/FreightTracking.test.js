const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("📦 TrackingContract - Full Security & Logic Tests", function () {

    let contract;
    let owner, admin, warehouse, attacker;

    const bookingRef = "REQAE35F0AF5613";

    beforeEach(async function () {
        [owner, admin, warehouse, attacker] = await ethers.getSigners();

        const Tracking = await ethers.getContractFactory("TrackingContract");
        contract = await Tracking.deploy();
        await contract.waitForDeployment();

        // Setup roles
        await contract.addAdmin(admin.address);
        await contract.connect(admin).addWarehouse(warehouse.address);
    });

    // ---------------------------------------------------
    // ROLE TESTS
    // ---------------------------------------------------

    it("❌ Should block unauthorized user", async function () {
        await expect(
            contract.connect(attacker).updateTracking(
                bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
            )
        ).to.be.revertedWith("Not authorized");
    });

    it("✅ Admin should update tracking", async function () {
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        const data = await contract.getTracking(bookingRef);
        expect(data.length).to.equal(1);
    });

    it("✅ Warehouse should update tracking", async function () {
        await contract.connect(warehouse).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        const data = await contract.getTracking(bookingRef);
        expect(data.length).to.equal(1);
    });

    // ---------------------------------------------------
    // OWNERSHIP TESTS
    // ---------------------------------------------------

    it("❌ Should block different user updating same booking", async function () {
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        await expect(
            contract.connect(warehouse).updateTracking(
                bookingRef, "Loc2", 2, 0, 1000, 1000, 0, 0
            )
        ).to.be.revertedWith("Not booking owner");
    });

    it("✅ Same owner can continue updates", async function () {
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        await contract.connect(admin).updateTracking(
            bookingRef, "Loc2", 2, 0, 1000, 1000, 0, 0
        );

        const data = await contract.getTracking(bookingRef);
        expect(data.length).to.equal(2);
    });

    // ---------------------------------------------------
    // VALIDATION TESTS
    // ---------------------------------------------------

    it("❌ Should fail empty booking reference", async function () {
        await expect(
            contract.connect(admin).updateTracking(
                "", "Loc", 1, 1, 1000, 1000, 0, 0
            )
        ).to.be.revertedWith("Booking ref required");
    });

    it("❌ Should fail empty location", async function () {
        await expect(
            contract.connect(admin).updateTracking(
                bookingRef, "", 1, 1, 1000, 1000, 0, 0
            )
        ).to.be.revertedWith("Location required");
    });

    it("❌ Should fail invalid sequence", async function () {
        await expect(
            contract.connect(admin).updateTracking(
                bookingRef, "Loc", 0, 1, 1000, 1000, 0, 0
            )
        ).to.be.revertedWith("Invalid sequence");
    });

    it("❌ Should enforce sequence order", async function () {
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        await expect(
            contract.connect(admin).updateTracking(
                bookingRef, "Loc2", 3, 0, 1000, 1000, 0, 0
            )
        ).to.be.revertedWith("Invalid sequence order");
    });

    // ---------------------------------------------------
    // COORDINATE VALIDATION
    // ---------------------------------------------------

    it("❌ Should reject invalid latitude", async function () {
        await expect(
            contract.connect(admin).updateTracking(
                bookingRef, "Loc", 1, 1, 99999999, 1000, 0, 0
            )
        ).to.be.revertedWith("Invalid latitude");
    });

    it("❌ Should reject invalid longitude", async function () {
        await expect(
            contract.connect(admin).updateTracking(
                bookingRef, "Loc", 1, 1, 1000, 99999999, 0, 0
            )
        ).to.be.revertedWith("Invalid longitude");
    });

    // ---------------------------------------------------
    // STATUS TRANSITION TESTS
    // ---------------------------------------------------

    it("✅ Should allow only one CURRENT and move previous to PASSED", async function () {
        // First current
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        // New current
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc2", 2, 1, 1000, 1000, 0, 0
        );

        const data = await contract.getTracking(bookingRef);

        expect(data[0].status).to.equal(2); // PASSED
        expect(data[1].status).to.equal(1); // CURRENT
    });

    // ---------------------------------------------------
    // EVENT TEST
    // ---------------------------------------------------

    it("✅ Should emit TrackingUpdated event", async function () {
        await expect(
            contract.connect(admin).updateTracking(
                bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
            )
        ).to.emit(contract, "TrackingUpdated");
    });

    // ---------------------------------------------------
    // GETTERS TESTS
    // ---------------------------------------------------

    it("❌ Should fail getLatestStatus if no data", async function () {
        await expect(
            contract.getLatestStatus("EMPTY")
        ).to.be.revertedWith("No data");
    });

    it("✅ Should return latest status", async function () {
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        const status = await contract.getLatestStatus(bookingRef);
        expect(status).to.equal(1);
    });

    it("❌ Should fail getCurrentLocation if no data", async function () {
        await expect(
            contract.getCurrentLocation("EMPTY")
        ).to.be.revertedWith("No data");
    });

    it("✅ Should return current location", async function () {
        await contract.connect(admin).updateTracking(
            bookingRef, "Loc1", 1, 1, 1000, 1000, 0, 0
        );

        const loc = await contract.getCurrentLocation(bookingRef);
        expect(loc.location).to.equal("Loc1");
    });

});