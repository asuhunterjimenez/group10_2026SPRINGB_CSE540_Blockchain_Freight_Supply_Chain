// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TrackingContract {

    address public owner;

    // Roles
    // NB - Admins manages Warehouse Users and also can transact
    //    - warehouse users only Transact
    mapping(address => bool) public isAdmin;
    mapping(address => bool) public isWarehouse;

    // NEW: Booking ownership (prevents random users from updating others' shipments)
    mapping(string => address) public bookingOwner;

    enum Status { Pending, Current, Passed }

    struct TrackingPoint {
        string bookingReference;
        string location;
        uint256 sequence;
        Status status;
        int256 latitude;
        int256 longitude;
        uint256 arrivalTime;
        uint256 departureTime;
        address updatedBy;
        uint256 updatedAt;
    }

    // NOTE: Still using string for readability (can optimize to bytes32 later if needed)
    mapping(string => TrackingPoint[]) public trackingData;

    // Track current index (avoids loops)
    mapping(string => uint256) public currentIndex;

    // ---------------------------------------------------
    // EVENTS (for frontend & monitoring)
    // ---------------------------------------------------
    event TrackingUpdated(
        string bookingReference,
        string location,
        uint256 sequence,
        Status status,
        address updatedBy,
        uint256 timestamp
    );

    // ---------------------------------------------------
    // MODIFIERS
    // ---------------------------------------------------

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAdmin() {
        require(isAdmin[msg.sender] || msg.sender == owner, "Not admin");
        _;
    }

    modifier onlyAuthorized() {
        require(
            isWarehouse[msg.sender] || 
            isAdmin[msg.sender] || 
            msg.sender == owner,
            "Not authorized"
        );
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // ---------------------------------------------------
    // ADMIN MANAGEMENT
    // ---------------------------------------------------

    function addAdmin(address user) external onlyOwner {
        require(user != address(0), "Invalid address");
        isAdmin[user] = true;
    }

    function removeAdmin(address user) external onlyOwner {
        isAdmin[user] = false;
    }

    // ---------------------------------------------------
    // WAREHOUSE MANAGEMENT
    // ---------------------------------------------------

    function addWarehouse(address user) external onlyAdmin {
        require(user != address(0), "Invalid address");
        isWarehouse[user] = true;
    }

    function removeWarehouse(address user) external onlyAdmin {
        isWarehouse[user] = false;
    }

    // ---------------------------------------------------
    // MAIN FUNCTION
    // ---------------------------------------------------

    function updateTracking(
        string memory bookingReference,
        string memory location,
        uint256 sequence,
        Status status,
        int256 latitude,
        int256 longitude,
        uint256 arrivalTime,
        uint256 departureTime
    ) external onlyAuthorized {

        // ---------------------------------------------------
        // BASIC VALIDATIONS (keep lightweight)
        // ---------------------------------------------------
        require(bytes(bookingReference).length > 0, "Booking ref required");
        require(bytes(location).length > 0, "Location required");
        require(sequence > 0, "Invalid sequence");

        //Validate coordinates (basic sanity check)
        require(latitude >= -9000000 && latitude <= 9000000, "Invalid latitude");
        require(longitude >= -18000000 && longitude <= 18000000, "Invalid longitude");

        TrackingPoint[] storage points = trackingData[bookingReference];

        // ---------------------------------------------------
        // BOOKING OWNERSHIP CONTROL
        // ---------------------------------------------------
        if (bookingOwner[bookingReference] == address(0)) {
            // First update → assign ownership
            bookingOwner[bookingReference] = msg.sender;
        } else {
            require(
                bookingOwner[bookingReference] == msg.sender,
                "Not booking owner"
            );
        }

        // ---------------------------------------------------
        // ENFORCE SEQUENCE ORDER
        // ---------------------------------------------------
        if (points.length > 0) {
            require(
                sequence == points.length + 1,
                "Invalid sequence order"
            );
        }

        // ---------------------------------------------------
        // Only ONE current (optimized)
        // ---------------------------------------------------
        if (status == Status.Current) {
            if (points.length > 0) {
                uint256 prevIndex = currentIndex[bookingReference];

                if (prevIndex < points.length) {
                    // Mark previous current as Passed
                    points[prevIndex].status = Status.Passed;
                }
            }

            // Update current index to latest
            currentIndex[bookingReference] = points.length;
        }

        // ---------------------------------------------------
        // SAVE DATA
        // ---------------------------------------------------
        points.push(TrackingPoint({
            bookingReference: bookingReference,
            location: location,
            sequence: sequence,
            status: status,
            latitude: latitude,
            longitude: longitude,
            arrivalTime: arrivalTime,
            departureTime: departureTime,
            updatedBy: msg.sender,
            updatedAt: block.timestamp
        }));

        // ---------------------------------------------------
        //EMIT EVENT (for frontend / monitoring)
        // ---------------------------------------------------
        emit TrackingUpdated(
            bookingReference,
            location,
            sequence,
            status,
            msg.sender,
            block.timestamp
        );
    }

    // ---------------------------------------------------
    // GET ALL TRACKING
    // ---------------------------------------------------
    function getTracking(string memory bookingReference)
        external
        view
        returns (TrackingPoint[] memory)
    {
        return trackingData[bookingReference];
    }

    // ---------------------------------------------------
    // GET LATEST STATUS
    // ---------------------------------------------------
    function getLatestStatus(string memory bookingReference)
        external
        view
        returns (Status)
    {
        TrackingPoint[] memory points = trackingData[bookingReference];
        require(points.length > 0, "No data");

        return points[points.length - 1].status;
    }

    // ---------------------------------------------------
    //GET CURRENT LOCATION 
    // ---------------------------------------------------
    function getCurrentLocation(string memory bookingReference)
        external
        view
        returns (TrackingPoint memory)
    {
        TrackingPoint[] memory points = trackingData[bookingReference];
        require(points.length > 0, "No data");

        uint256 index = currentIndex[bookingReference];
        require(index < points.length, "Invalid index");

        return points[index];
    }
}