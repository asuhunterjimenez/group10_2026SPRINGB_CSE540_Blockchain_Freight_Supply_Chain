// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title Freight Shipment Smart Contract (Role-Based Access: Admin + Sales Team)

contract FreightShipment {

    address public owner;

    // ------------------------------------
    // ROLE MANAGEMENT
    // ------------------------------------
    mapping(address => bool) public isAdmin;
    mapping(address => bool) public isSalesTeam;

    // Shipment ownership (security layer)
    mapping(uint256 => address) public shipmentOwner;

    // ------------------------------------
    // CONSTRUCTOR
    // ------------------------------------
    constructor() {
        owner = msg.sender;
        isAdmin[msg.sender] = true; // deployer is default admin
    }

    // ------------------------------------
    // MODIFIERS
    // ------------------------------------
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAdmin() {
        require(isAdmin[msg.sender] || msg.sender == owner, "Not admin");
        _;
    }

    modifier onlySales() {
        require(isSalesTeam[msg.sender] || isAdmin[msg.sender] || msg.sender == owner, "Not sales");
        _;
    }

    modifier onlyShipmentOwner(uint256 bookingId) {
        require(
            shipmentOwner[bookingId] == msg.sender ||
            isAdmin[msg.sender] ||
            msg.sender == owner,
            "Not shipment owner"
        );
        _;
    }

    // ------------------------------------
    // ROLE MANAGEMENT FUNCTIONS
    // ------------------------------------
    function addAdmin(address user) external onlyOwner {
        require(user != address(0), "Invalid address");
        isAdmin[user] = true;
    }

    function addSalesTeam(address user) external onlyAdmin {
        require(user != address(0), "Invalid address");
        isSalesTeam[user] = true;
    }

    // ------------------------------------
    // STRUCTS
    // ------------------------------------
    struct Party {
        string companyName;
        string fullName;
        string phone;
        string email;
        string addressInfo;
    }

    struct CargoItem {
        string itemType;
        string description;
        string vinOrQty;
        uint256 declaredValueWei;
    }

    struct Shipment {
        uint256 bookingId;
        string quoteReference;
        string freightType;
        string freightRoute;
        string status;
        uint256 createdAt;
        string txHash;
    }

    struct ShipmentParties {
        Party shipper;
        Party receiver;
    }

    // ------------------------------------
    // STORAGE
    // ------------------------------------
    mapping(uint256 => Shipment) public shipments;
    mapping(uint256 => ShipmentParties) public parties;
    mapping(uint256 => CargoItem[]) public cargo;

    // ------------------------------------
    // EVENTS
    // ------------------------------------
    event ShipmentCreated(uint256 bookingId);
    event CargoAdded(uint256 bookingId);

    // ------------------------------------
    // VALIDATION HELPERS
    // ------------------------------------
    function _str(string memory v, string memory msg_) internal pure {
        require(bytes(v).length > 0, msg_);
    }

    function _email(string memory e) internal pure {
        bytes memory b = bytes(e);
        bool at;
        bool dot;

        for (uint i = 0; i < b.length; i++) {
            if (b[i] == "@") at = true;
            if (b[i] == ".") dot = true;
        }

        require(at && dot, "Invalid email format");
    }

    // ------------------------------------
    // ROLE-BASED ERROR MESSAGES
    // ------------------------------------
    function _party(Party memory p, string memory role) internal pure {

        require(
            bytes(p.companyName).length > 0,
            string(abi.encodePacked(role, " company required"))
        );

        require(
            bytes(p.fullName).length > 0,
            string(abi.encodePacked(role, " name required"))
        );

        require(
            bytes(p.phone).length > 0,
            string(abi.encodePacked(role, " phone required"))
        );

        require(
            bytes(p.email).length > 0,
            string(abi.encodePacked(role, " email required"))
        );

        _email(p.email);

        require(
            bytes(p.addressInfo).length > 0,
            string(abi.encodePacked(role, " address required"))
        );
    }

    // ------------------------------------
    // CREATE SHIPMENT (SALES ONLY)
    // ------------------------------------
    function createShipment(
        uint256 bookingId,
        string memory quoteReference,
        string memory freightType,
        string memory freightRoute,
        string memory txHash,
        Party memory shipper,
        Party memory receiver
    ) external onlySales {

        require(bookingId > 0, "Invalid bookingId");
        require(shipments[bookingId].bookingId == 0, "Shipment exists");

        _str(quoteReference, "Quote required");
        _str(freightType, "Freight type required");
        _str(freightRoute, "Route required");
        _str(txHash, "TX hash required");

        _party(shipper, "Shipper");
        _party(receiver, "Receiver");

        shipmentOwner[bookingId] = msg.sender;

        shipments[bookingId] = Shipment(
            bookingId,
            quoteReference,
            freightType,
            freightRoute,
            "CREATED",
            block.timestamp,
            txHash
        );

        parties[bookingId] = ShipmentParties(shipper, receiver);

        emit ShipmentCreated(bookingId);
    }

    // ------------------------------------
    // ADD CARGO (OWNER OR ADMIN ONLY)
    // ------------------------------------
    function addCargo(
        uint256 bookingId,
        string memory itemType,
        string memory description,
        string memory vinOrQty,
        uint256 declaredValueWei
    ) external onlyShipmentOwner(bookingId) {

        require(shipments[bookingId].bookingId != 0, "Shipment not found");

        _str(itemType, "Item required");
        _str(description, "Description required");
        _str(vinOrQty, "VIN/QTY required");

        require(declaredValueWei > 0, "Invalid value");

        cargo[bookingId].push(
            CargoItem(itemType, description, vinOrQty, declaredValueWei)
        );

        emit CargoAdded(bookingId);
    }

    // ------------------------------------
    // GETTERS
    // ------------------------------------
    function getCargoCount(uint256 bookingId) external view returns (uint256) {
        require(shipments[bookingId].bookingId != 0, "Shipment not found");
        return cargo[bookingId].length;
    }
}