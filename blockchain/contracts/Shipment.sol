// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title Freight Shipment Smart Contract
/// @author Geoffrey
/// @notice Stores shipment, shipper, receiver, cargo, payment, and gas fee data on blockchain
/// @dev Designed for Django + Ganache + Remix integration
contract FreightShipment {

    /// @notice Stores shipper or receiver details
    struct Party {
        string companyName;   // Company name
        string fullName;      // Contact person full name
        string phone;         // Phone number
        string email;         // Email address
        string addressInfo;   // Full address
    }

    /// @notice Stores vehicle or goods details
    struct CargoItem {
        string itemType;          // Vehicle or Goods
        string description;       // Cargo description
        string vinOrQty;          // VIN for vehicles OR quantity for goods
        uint256 declaredValueWei; // Declared cargo value in Wei
    }

    /// @notice Stores core shipment information
    struct Shipment {
        uint256 bookingId;        // Internal booking ID from Django
        string quoteReference;    // Freight quotation reference
        string freightType;       // Air, Ocean, RoRo, Brokerage, etc.
        string freightRoute;      // Example: Vancouver -> Dubai
        string status;            // Current shipment status
        uint256 paidAmountWei;    // Payment made by customer
        uint256 gasFeeWei;        // Blockchain gas used
        uint256 createdAt;        // Timestamp
        string txHash;            // Blockchain transaction hash
    }

    /// Reduce stack depth by grouping shipper + receiver
    struct ShipmentParties {
        Party shipper;
        Party receiver;
    }

    /// @notice Stores shipment details by booking ID
    mapping(uint256 => Shipment) public shipments;

    /// @notice Stores parties (shipper + receiver) by booking ID
    mapping(uint256 => ShipmentParties) public parties;

    /// @notice Stores all cargo items linked to a booking ID
    mapping(uint256 => CargoItem[]) public cargo;

    /// @notice Triggered whenever a shipment is created
    event ShipmentCreated(
        uint256 bookingId,
        string freightType,
        string status
    );

    /// @notice Creates a new shipment booking on blockchain
    function createShipment(
        uint256 bookingId,
        string memory quoteReference,
        string memory freightType,
        string memory freightRoute,
        string memory txHash,
        uint256 paidAmountWei,
        uint256 gasFeeWei,

        /// Shipper
        Party memory shipper,

        /// Receiver
        Party memory receiver
    ) public {

        // Save shipment record
        shipments[bookingId] = Shipment(
            bookingId,
            quoteReference,
            freightType,
            freightRoute,
            "Shipment",
            paidAmountWei,
            gasFeeWei,
            block.timestamp,
            txHash
        );

        // Save shipper + receiver together
        parties[bookingId] = ShipmentParties(shipper, receiver);

        // Emit blockchain event log
        emit ShipmentCreated(
            bookingId,
            freightType,
            "Shipment"
        );
    }

    /// @notice Adds cargo item to an existing shipment
    function addCargo(
        uint256 bookingId,
        string memory itemType,
        string memory description,
        string memory vinOrQty,
        uint256 declaredValueWei
    ) public {
        cargo[bookingId].push(
            CargoItem(
                itemType,
                description,
                vinOrQty,
                declaredValueWei
            )
        );
    }

    /// @notice Returns number of cargo items in a shipment
    function getCargoCount(uint256 bookingId)
        public
        view
        returns (uint256)
    {
        return cargo[bookingId].length;
    }
}