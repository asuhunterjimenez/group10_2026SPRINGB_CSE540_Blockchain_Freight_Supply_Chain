const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("🚚 FreightShipment Contract - Full Security & Role Tests", function () {

  let contract, owner, sales, user;

  beforeEach(async function () {
    [owner, sales, user] = await ethers.getSigners();

    const C = await ethers.getContractFactory("FreightShipment");
    contract = await C.deploy();
    await contract.waitForDeployment();

    await contract.addSalesTeam(sales.address);
  });

  const party = {
    companyName: "Group10 Block-chain Freight System",
    fullName: "Geoffrey Kasibante",
    phone: "1 250 666666",
    email: "gkasibante@test.com",
    addressInfo: "Street 1,Common wealthRD,Canada"
  };

  // ---------------- ROLE TESTS ----------------

  it("❌ Should prevent non-sales from creating shipment", async function () {
    await expect(
      contract.connect(user).createShipment(
        1, "Q1", "Air", "Route", "tx", party, party
      )
    ).to.be.revertedWith("Not sales");
  });

  it("✅ Sales should create shipment successfully", async function () {
    await contract.connect(sales).createShipment(
      1, "Q1", "Air", "Route", "tx", party, party
    );

    const s = await contract.shipments(1);
    expect(s.bookingId).to.equal(1n);
  });

  it("❌ Should prevent duplicate shipment creation", async function () {
    await contract.connect(sales).createShipment(
      2, "Q1", "Air", "Route", "tx", party, party
    );

    await expect(
      contract.connect(sales).createShipment(
        2, "Q1", "Air", "Route", "tx", party, party
      )
    ).to.be.revertedWith("Shipment exists");
  });

  it("❌ Should fail invalid booking ID", async function () {
    await expect(
      contract.connect(sales).createShipment(
        0, "Q", "Air", "Route", "tx", party, party
      )
    ).to.be.revertedWith("Invalid bookingId");
  });

  it("❌ Should fail empty quote reference", async function () {
    await expect(
      contract.connect(sales).createShipment(
        3, "", "Air", "Route", "tx", party, party
      )
    ).to.be.revertedWith("Quote required");
  });

  it("❌ Should fail invalid email format", async function () {
    const bad = { ...party, email: "wrongemail" };

    await expect(
      contract.connect(sales).createShipment(
        4, "Q", "Air", "Route", "tx", bad, party
      )
    ).to.be.revertedWith("Invalid email format");
  });

  // ---------------- CARGO TESTS ----------------

  it("❌ Should not allow cargo on non-existent shipment", async function () {
    await expect(
      contract.addCargo(999, "Item", "Desc", "10", 100)
    ).to.be.revertedWith("Shipment not found");
  });

  it("❌ Should prevent zero value cargo", async function () {
    await contract.connect(sales).createShipment(
      5, "Q", "Air", "Route", "tx", party, party
    );

    await expect(
      contract.addCargo(5, "Item", "Desc", "10", 0)
    ).to.be.revertedWith("Invalid value");
  });

  it("❌ Should prevent unauthorized cargo injection", async function () {
    await contract.connect(sales).createShipment(
      6, "Q", "Air", "Route", "tx", party, party
    );

    await expect(
      contract.connect(user).addCargo(6, "Item", "Desc", "10", 100)
    ).to.be.revertedWith("Not shipment owner");
  });

  it("✅ Should allow shipment owner to add cargo", async function () {
    await contract.connect(sales).createShipment(
      7, "Q", "Air", "Route", "tx", party, party
    );

    await contract.connect(sales).addCargo(
      7, "Electronics", "Phones", "10", 500
    );

    const count = await contract.getCargoCount(7);
    expect(count).to.equal(1n);
  });

  it("❌ Should fail reading non-existent shipment cargo", async function () {
    await expect(
      contract.getCargoCount(999)
    ).to.be.revertedWith("Shipment not found");
  });

});