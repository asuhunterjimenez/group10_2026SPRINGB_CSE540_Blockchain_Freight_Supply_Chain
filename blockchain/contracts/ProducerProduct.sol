// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Producer Product Management
/// @notice Allows only registered producers to create and manage products
contract ProducerProduct {

    // =========================
    // STATE VARIABLES
    // =========================

    /// @notice Address of the contract owner (admin)
    address public owner;

    /// @notice Mapping to track approved producers (true = approved)
    mapping(address => bool) public producers;

    /// @notice Structure representing a product
    struct Product {
        uint256 id;           // Unique product ID
        string name;          // Product name
        string description;   // Product description
        uint256 timestamp;    // Time when product was created (block timestamp)
        address producer;     // Address of the producer who created it
    }

    /// @notice Array to store all products
    Product[] public products;

    // =========================
    // EVENTS
    // =========================

    /// @notice Emitted when a new product is created
    /// @param id Product ID
    /// @param name Product name
    /// @param producer Address of creator
    event ProductCreated(uint256 id, string name, address producer);

    // =========================
    // MODIFIERS (ACCESS CONTROL)
    // =========================

    /// @notice Restricts function to only contract owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    /// @notice Restricts function to only approved producers
    modifier onlyProducer() {
        require(producers[msg.sender], "Only approved producers can call this");
        _;
    }

    // =========================
    // CONSTRUCTOR
    // =========================

    /// @notice Sets the deployer as the contract owner
    constructor() {
        owner = msg.sender; // person deploying contract becomes admin
    }

    // =========================
    // ADMIN FUNCTIONS
    // =========================

    /// @notice Add a new producer (only owner/admin can call)
    /// @param _producer Address of producer to approve
    function addProducer(address _producer) external onlyOwner {
        producers[_producer] = true; // mark address as approved
    }

    /// @notice Remove an existing producer (only owner/admin)
    /// @param _producer Address of producer to remove
    function removeProducer(address _producer) external onlyOwner {
        producers[_producer] = false; // revoke approval
    }

    // =========================
    // CORE FUNCTIONALITY
    // =========================

    /// @notice Create a new product (only approved producers)
    /// @param _name Name of the product
    /// @param _description Description of the product
    function createProduct(
        string calldata _name, 
        string calldata _description
    ) 
        external 
        onlyProducer 
    {
        // Generate product ID based on current array length
        uint256 productId = products.length;

        // Store product in blockchain
        products.push(Product({
            id: productId,
            name: _name,
            description: _description,
            timestamp: block.timestamp, // current block time
            producer: msg.sender        // address creating the product
        }));

        // Emit event for frontend / Django / logs
        emit ProductCreated(productId, _name, msg.sender);
    }

    // =========================
    // READ FUNCTIONS (VIEW)
    // =========================

    /// @notice Get total number of products stored on blockchain
    /// @return Total count of products
    function getProductCount() external view returns (uint256) {
        return products.length;
    }

    /// @notice Retrieve product details using product ID
    /// @param _id Product ID
    /// @return Product struct containing all details
    function getProduct(uint256 _id) external view returns (Product memory) {
        // Ensure product exists
        require(_id < products.length, "Product does not exist");

        // Return product data
        return products[_id];
    }
}