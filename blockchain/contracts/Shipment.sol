// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @title Shipment Contract
/// @notice Handles creation, tracking, and status updates of shipments
contract Shipment is Ownable {

    /// @notice Constructor sets the deployer as the contract owner
    constructor() Ownable(msg.sender) {}  // Pass deployer as owner

    /// @notice Structure to store shipment details
    struct ShipmentRecord {
        string shipmentId;          // Unique ID for the shipment
        string quoteRequestId;      // Related quote request ID
        string origin;              // Shipment origin location
        string destination;         // Shipment destination location
        string containerType;       // Type of container (e.g., 20ft, 40ft)
        uint256 weight;             // Shipment weight in kg
        string status;              // Current shipment status (e.g., pending, in-transit, delivered)
        uint256 createdAt;          // Timestamp of shipment creation
        uint256 lastUpdatedAt;      // Timestamp of last status update
        bool deliveryConfirmed;     // Flag for delivery confirmation
        string carrierName;         // Name of shipping carrier
    }

    /// @notice Mapping to store ShipmentRecord by shipmentId
    mapping(string => ShipmentRecord) private shipments;

    /// @notice Event emitted when a new shipment is created
    event ShipmentCreated(string indexed shipmentId, string status);

    /// @notice Event emitted when a shipment status is updated
    event ShipmentStatusUpdated(string indexed shipmentId, string newStatus);

    /// @notice Event emitted when a shipment delivery is confirmed
    event DeliveryConfirmed(string indexed shipmentId);

    /// @notice Create a new shipment record
    /// @param _shipment The ShipmentRecord object containing shipment details
    /// @dev Only callable by the contract owner
    function createShipment(ShipmentRecord memory _shipment) external onlyOwner {
        require(bytes(_shipment.shipmentId).length > 0, "Shipment ID required");   // Validate shipmentId
        require(bytes(_shipment.origin).length > 0, "Origin required");             // Validate origin
        require(bytes(_shipment.destination).length > 0, "Destination required");   // Validate destination

        ShipmentRecord storage s = shipments[_shipment.shipmentId];  // Store shipment in mapping

        // Copy fields from input ShipmentRecord
        s.shipmentId = _shipment.shipmentId;
        s.quoteRequestId = _shipment.quoteRequestId;
        s.origin = _shipment.origin;
        s.destination = _shipment.destination;
        s.containerType = _shipment.containerType;
        s.weight = _shipment.weight;
        s.status = _shipment.status;
        s.createdAt = block.timestamp;
        s.lastUpdatedAt = block.timestamp;
        s.deliveryConfirmed = false;  // Initialize delivery as not confirmed
        s.carrierName = _shipment.carrierName;

        emit ShipmentCreated(_shipment.shipmentId, _shipment.status); // Emit creation event
    }

    /// @notice Retrieve a shipment record by shipmentId
    /// @param _shipmentId Unique ID of the shipment
    /// @return ShipmentRecord associated with the shipmentId
    /// @dev Reverts if shipment does not exist
    function getShipment(string memory _shipmentId) external view returns (ShipmentRecord memory) {
        ShipmentRecord memory s = shipments[_shipmentId];
        require(bytes(s.shipmentId).length > 0, "Shipment does not exist");
        return s;
    }

    /// @notice Update the status of a shipment
    /// @param _shipmentId Unique shipment ID
    /// @param _newStatus New status string (e.g., in-transit, delivered)
    /// @dev Only callable by the contract owner
    function updateShipmentStatus(string memory _shipmentId, string memory _newStatus) external onlyOwner {
        ShipmentRecord storage s = shipments[_shipmentId];
        require(bytes(s.shipmentId).length > 0, "Shipment does not exist");
        s.status = _newStatus;
        s.lastUpdatedAt = block.timestamp;

        emit ShipmentStatusUpdated(_shipmentId, _newStatus); // Emit status update event
    }

    /// @notice Confirm delivery of a shipment
    /// @param _shipmentId Unique shipment ID
    /// @dev Only callable by the contract owner
    function confirmDelivery(string memory _shipmentId) external onlyOwner {
        ShipmentRecord storage s = shipments[_shipmentId];
        require(bytes(s.shipmentId).length > 0, "Shipment does not exist");
        s.deliveryConfirmed = true;
        s.status = "delivered";
        s.lastUpdatedAt = block.timestamp;

        emit DeliveryConfirmed(_shipmentId); // Emit delivery confirmation event
    }

    /// @notice Check if a shipment exists
    /// @param _shipmentId Unique shipment ID
    /// @return True if shipment exists, false otherwise
    function shipmentExists(string memory _shipmentId) external view returns (bool) {
        return bytes(shipments[_shipmentId].shipmentId).length > 0;
    }
}