#  🚢 Blockchain Freight Supplychain Project
**App Name:** Group10 Shippers Inc<br>
**Team:** Group10 <br>
**Course:** CSE 540: Engineering Blockchain Applications <br> 
**Semester:** 2026 Spring B  <br>
**University:** Arizona State University, Tempe, AZ, USA <br>
👥**Team Members:** *Ebrain Mirambeau, Neha Shivashankar Prasad, Hunter Jimenez, Geoffrey Kasibante, Twinkle Patel*

---

## Project Overview
This project is designed and developed by group10 with the aim of implementing a hybrid blockchain Django solution for freight supply chain management. It enables secure product creation for known clients or producers,shipment tracking, booking confirmations, and payments using Ethereum smart contracts, while providing a user friendly interface with Django and Stripe integration. Key features include immutable payment records, shipment provenance, and automated reporting for admins and users.<br>
The project tracks product creation for registered company clients and producers, freight shipments, booking confirmations, and payments using a hybrid architecture:
- **Django backend** for authentication, quotes, bookings, and system configuration (PostgreSQL database)
- **Local Ethereum blockchain (Ganache)** for immutable storage of products, payments, shipment records, and status updates
- **MetaMask** for ETH-based payments and transaction signing or pay for gas
- **Remix + MetaMask** for smart contract deployment and interaction on Ethereum test networks
  
### 🔑 CRM Access Levels & Stakeholder Mapping – Group10 Shippers Inc

| Role          | Stakeholder Mapping              | Description                                                                 | Example Username | Example Password      |
|---------------|---------------------------------|-----------------------------------------------------------------------------|-----------------|----------------------|
| **Producer**  | Producer / Manufacturer         | Creates and registers shipments/products on blockchain,request quotes, initiating the provenance record | producer1       | your_password_here   |
| **Admin**     | Regulator / System Authority    | Full system access, manages users, roles, permissions, and audits blockchain events | admin_user      | your_password_here   |
| **Client**    | Retailer / Consumer             | Views shipments,request quotes, confirms bookings, tracks delivery, verifies product authenticity | client_user     | your_password_here   |
| **Finance**   | Financial Authority / Support   | Handles payments, monitors transactions, and generates financial reports    | finance_user    | your_password_here   |
| **Sales**     | Distributor / Supplier          | Manages bookings, quotations, and coordinates shipment operations           | sales1          | your_password_here   |
| **Warehouse** | Storage / Logistics Handler     | Updates shipment status (received, stored, dispatched)                     | warehouse1      | your_password_here   |

> Table 1: **Note:** For security, real passwords are not included. Admins can create users or set test credentials in the Django admin panel.

## Dependencies

### 🖥️ Backend & Core
- **Python 3.11+** – Core programming language <a href="https://www.python.org/downloads/release/python-3110/" target="_blank">Download</a>
- **Django 4.x** – Backend web framework <a href="https://docs.djangoproject.com/en/6.0/releases/4.0/" target="_blank">Download</a> 
- **PostgreSQL** – Database for storing application data. <a href="https://www.postgresql.org/" target="_blank">Download</a>
- Optional: **Docker** – Containerize the backend, database, and blockchain nodes for easy local or production deployment. <a href="https://www.docker.com/" target="_blank">Download</a>  

### ⛓️ Blockchain
- **Web3.py** – Interaction with Ethereum blockchain  
- **Ganache** – Local Ethereum blockchain for testing. <a href="https://archive.trufflesuite.com/ganache/" target="_blank">Download</a> 
- **MetaMask Wallet** – User wallet for blockchain transactions and ETH based shipping fee payments. <a href="https://metamask.io/download" target="_blank">Download</a>   
- **Remix IDE** – Smart contract development and deployment. <a href="https://remix.ethereum.org/" target="_blank">Download</a>   

### 📄 Reporting & Email
- **requirements.txt packages**:
  - `docx`, `docx2pdf`, `reportlab==4.4.3` – Generate invoices and convert reports to PDF (from Blockchain & PostgreSQL data)  
  - `django-anymail` – Sending email notifications from the system  

### 🎨 Frontend
- **Bootstrap** – Responsive UI design  
- **Vue.js** – Dynamic frontend interactions  

## Locate Settings.py and local_settings.py
Note: File with settings and configurations are always hidden for security reasons but for the case of the project, group10 will be providing a clear path to the files
 - files Location : Blockchain-Freight-SupplyChain/Jenik_freight_crm/**

## Project Folder and File structure
This section describes the main folders and files in the project and their purposes.
<br>
<pre>
<b>Blockchain-Freight-SupplyChain/</b> <span style="color:gray;font-style:italic;"># Root folder of the Django + Blockchain project</span>
│
├─ <b>apps/</b> <span style="color:gray;font-style:italic;"># Django apps for different modules of the system</span>
│  ├─ Account_settings/ <span style="color:gray;font-style:italic;"># User account management (profile, preferences)</span>
│  ├─ Bookings/ <span style="color:gray;font-style:italic;"># Freight booking functionalities</span>
│  ├─ Documentations/ <span style="color:gray;font-style:italic;"># Documentation forms and handling</span>
│  ├─ Home/ <span style="color:gray;font-style:italic;"># Home page and dashboard</span>
│  ├─ Login/ <span style="color:gray;font-style:italic;"># Authentication and login/logout</span>
│  ├─ Payments/ <span style="color:gray;font-style:italic;"># Stripe payments, webhook handling</span>
│  ├─ Quotings/ <span style="color:gray;font-style:italic;"># Freight quotes and price calculations</span>
│  ├─ Reports/ <span style="color:gray;font-style:italic;"># Generating reports (CSV, PDF, etc.)</span>
   ├─ Products/ <span style="color:gray;font-style:italic;"># Manages Products for Known clients,producers,suppliers</span>
│  ├─ Shipments/ <span style="color:gray;font-style:italic;"># Shipment tracking and details</span>
│  └─ Helpers/ <span style="color:gray;font-style:italic;"># Shared helper functions and utilities across apps</span>
│
├─ <b>blockchain/</b> <span style="color:gray;font-style:italic;"># Smart contract related files</span>
│  ├─ contracts/ <span style="color:gray;font-style:italic;"># Solidity smart contracts</span>
│  │  ├─ Freight.sol <span style="color:gray;font-style:italic;"># Freight-related smart contract</span>
│  │  └─ Payment.sol <span style="color:gray;font-style:italic;"># Payment storage and tracking contract</span>
│  └─ migrations/ <span style="color:gray;font-style:italic;"># Blockchain migrations (local/testnet deployments)</span>
│
├─ <b>dependencies/</b> <span style="color:gray;font-style:italic;"># Shared resources and project-wide variables</span>
├─ <b>static/</b> <span style="color:gray;font-style:italic;"># CSS, JS, images, and other static files</span>
├─ <b>templates/</b> <span style="color:gray;font-style:italic;"># Django HTML templates</span>
├─ global_variables.py <span style="color:gray;font-style:italic;"># Project-wide Python variables/settings</span>
│
├─ <b>Jenik_freight_crm/</b> <span style="color:gray;font-style:italic;"># Main Django project folder</span>
│  ├─ manage.py <span style="color:gray;font-style:italic;"># Django management script</span>
│  ├─ local_settings.py <span style="color:gray;font-style:italic;"># Configurations like local database or debug settings</span>
│  ├─ requirements.txt <span style="color:gray;font-style:italic;"># Python dependencies</span>
│  └─ settings.py <span style="color:gray;font-style:italic;"># Django project configuration (databases, apps, middleware, etc.)</span>
│
├─ <b>media/</b> <span style="color:gray;font-style:italic;"># Uploaded files, videos, and other media assets</span>
├─ <b>Tests/</b> <span style="color:gray;font-style:italic;"># Pytests and testing scripts</span>
├─ <b>Docker/</b> <span style="color:gray;font-style:italic;"># Docker configurations and deployment scripts</span>
│  ├─ Dockerfile <span style="color:gray;font-style:italic;"># Instructions to build the Docker image</span>
│  ├─ docker-compose.yml <span style="color:gray;font-style:italic;"># Multi-container setup (Django, Postgres, blockchain nodes)</span>
│  └─ .dockerignore <span style="color:gray;font-style:italic;"># Files/folders to ignore when building Docker image</span>
│
├─ README.md <span style="color:gray;font-style:italic;"># Project documentation, setup instructions, code explanations, and figures</span>
</pre>
*Figure 1: Overview of the project folder structure showing all main apps, blockchain folder, and supporting Django files.*


## Setup Instructions

1. **Setup PostgreSQL database and update**
   - Update/edit settings.py file
   - PostgreSQL database will be handling off-Chain services like Bookings,Quoting,Documentation,User Accounts Settings
     
2. **Clone the repository**
   ```bash
   git clone https://github.com/asuhunterjimenez/group10_2026SPRINGB_CSE540_Blockchain_Freight_Supply_Chain.git

3. **Install python Python 3.11+**

4. **Create and activate a virtual environment**
    python -m venv venv
    source venv/bin/activate   # Linux/Mac
    venv\Scripts\activate      # Windows

5. **Install dependencies pip install -r requirements.txt**
   - requirements.txt contains, django,docx,docx2pdf,reportlab==4.4.3,stripe
     
6. **Run Django and it's migrations**
   Open Command Line. you can either use cmd or windows power shell and do the following
    - locate your django instalation example: cd C:\Django_installation\django_activation\Scripts
       - then: .\activate  #This will activate you django enviroment,
       - After, Locate your django folder for  example: cd C:\Blockchain-Freight-SupplyChain
       - Run below commands
          - python manage.py makemigrations #this will create your tables ready to be uploaded on postgreeDB (the files run are in models.py)
          - python manage.py migrate #this will upload create a database and your table schemas on postgreeDB
          - Create Admin Accounts:
             -  python manage.py createsuperuser #Run the createsuperuser command
             -  python manage.py createsuperuser --username admin --email admin@example.com #Enter the required info
          - python runserver # this will run your settings.py and provide a link to your application for your browser <br><br>
            <img width="1247" height="211" alt="image" src="https://github.com/user-attachments/assets/3d41ec8e-60ce-4eac-a674-ed54c30ff719" />
            <br>*Figure 2: Output of python manage.py runserver showing the local server URL to access the application.*
            
6a. **Optional: Run the Project Using Docker**  
- If you prefer not to manually install Python, PostgreSQL, or Ganache, you can use Docker to run the entire application in containers:

   - Make sure Docker Desktop is installed and running.
   - Navigate to the project root folder:  
      ```bash
      cd Blockchain-Freight-SupplyChain
      ```
   - Build the Docker containers:  
      ```bash
      docker-compose build
      ```
  - Start the application stack (Django + PostgreSQL + Ganache):  
      ```bash
      docker-compose up
      ```
  - Access your application using the URL shown in the terminal (usually http://localhost:8000)
  - Stop the containers anytime with:  
      ```bash
      docker-compose down
      ```
    
7.  **Install**
     - Web3.py via virtual Python environment. so as to open up communication between our appliactaion and blockchain service(Ganache)
     - Vscode: To edit and write your python codes
     - Remix IDE : is a browser-based development environment used to write, edit, compile, run, and deploy smart contracts written in Solidity. It provides built-in tools for testing, debugging, and interacting with contracts, making it especially useful for beginners and rapid prototyping. Remix supports deployment to local blockchains, test networks, and the Ethereum mainnet, and integrates easily with wallets like MetaMask for transaction signing
     - MetaMask Wallet : is a popular crypto wallet and browser extension that allows users to store, send, and receive cryptocurrencies like Ethereum. It also acts as a gateway to decentralized applications, enabling secure interaction with blockchain networks directly from a web browser or mobile device.
     - Ganache : is a local blockchain simulator used for testing smart contracts.
  
 8. **Deploy smart contracts via Remix connected to Ganache or Polygon Amoy Testnet**

## Usage

- **Producer / Manufacturer** can create and register new shipments/products on the blockchain, request quotes, initiating the provenance record. Each creation triggers a `ProductCreated` blockchain event.  
- **Admin** (Regulator / System Authority) can manage users, roles, system settings, and audit all blockchain records for compliance.  
- **Clients / Consumers** can view their shipments, request quotes, confirm bookings, track delivery status, and verify product authenticity.  
- **Finance** team can handle payments, monitor transactions, generate financial reports, and verify payments on-chain.  
- **Sales / Distributor** team can create and manage bookings, quotations, and coordinate shipment operations.  
- **Warehouse / Logistics Handler** can update shipment status during storage and delivery (e.g., received, stored, dispatched), triggering `StatusUpdated` events on the blockchain.  

- Users can make payments shipping and block chain transaction fees using **ETH via MetaMask**. **Django --> MetaMask --> Solidity --> Ganache**
- All payment transactions and shipment status updates are **recorded on blockchain** for traceability, auditability, and provenance.  
- Account settings, quoting, documentation, and bookings are stored in **PostgreSQL** as off-chain services to optimize storage and performance.  
- Every shipment and payment action generates blockchain events (e.g., **`ProductCreated`, `OwnershipTransferred`, `StatusUpdated`**) to ensure a full **provenance trail** across the product lifecycle.
  
## Notes
- Smart contract logic is stored in blockchain/contracts/
- Smart contract Django-Ganache-MetaMask for **Payments transactions** is stored in **apps/Payments/**
- Smart contract Django-Ganache for **Shipment transactions** is stored in **apps/Shipments/**

## Smart Contract Structure & Interfaces
Our project uses three smart contracts on Ethereum to handle payments, shipments and product creation for known producers or clients securely:<br>

### Payment.sol

  - Manages all payment transactions for freight bookings.
  - Tracks each payment with details such as sessionId, transactionId, amount, currency, status (success/failed), payer, and associated shipmentId.
  - Supports payments via ETH through **MetaMask integration**.
  - Emits events like **PaymentCreated, PaymentProcessed, and EmailMarkedSent** to notify the system when a payment occurs, is confirmed, or a confirmation email is sent.
  - Ensures **traceability and auditability** by recording all payment events on-chain.
  - Only the contract owner can create and update payments, enforcing controlled and secure management through Django Interface.
  - Provides functions to query payment history for a shipment or blockchain transaction fees, supporting transparency for stakeholders.

### Shipment.sol
  - Handles creation, tracking, and status updates of shipments.
  - Stores shipment information like shipmentId, origin, destination, containerType, weight, status, and delivery confirmation.
  - Emits events such as ShipmentCreated, ShipmentStatusUpdated, and DeliveryConfirmed for real-time monitoring.
  - Only the contract owner can create or update shipments, maintaining integrity of shipment data.

### How Payment.sol and Shipment.sol work together:
- When a customer makes a payment (Payment.sol), it is linked to a freight quote.
- Once the payment is confirmed, a shipment record (Shipment.sol) is created and tracked until delivery.
- Events from both contracts allow the frontend to update the UI in real-time.

### ProducerProduct.sol
- Manages decentralized product registration and storage for supply chain systems.
  - Restricts product creation to **approved producers** only, ensuring controlled and secure access.
  - Allows the **contract owner (admin/producer/client)** to add or remove producers from the approved list.
  - Stores each product with details such as `id`, `name`, `description`, `timestamp`, and `producer address`.
  - Maintains an on-chain array of all products for transparent, immutable, and tamper-proof record keeping.
  - Provides read functions like `getProductCount` and `getProduct` to efficiently retrieve product data.
  - Emits `ProductCreated` events whenever a new product is added, enabling seamless integration with backend systems (e.g., Django) and real-time tracking.
    <br><br>
### Booking --> Payment --> Shipment Blockchain Flow
## 🚢 Blockchain Freight Payment & Shipment Flow

```text
User (MetaMask Wallet)
        │
        │ 1️⃣ Connect Wallet
        │
        ▼
Shipping App (Django Frontend)
        │
        │ 2️⃣ User confirms booking
        │ 3️⃣ Booking saved in PostgreSQL
        │
        ▼
Deposit Payment Screen
        │
        │ 4️⃣ User clicks "Pay Initial Deposit"
        │
        ▼
MetaMask Popup
        │
        │ 5️⃣ Shows deposit amount + gas fee
        │ 6️⃣ User clicks "Confirm"
        │
        ▼
Ganache Local Blockchain
        │
        │ 7️⃣ ETH sent to Payment.sol
        │ 8️⃣ Transaction mined
        │
        ▼
Payment.sol Smart Contract
        │
        │ 9️⃣ Stores:
        │    - wallet address
        │    - booking ID
        │    - shipment ID
        │    - deposit amount
        │    - tx hash
        │    - payment stage = DEPOSIT
        │
        ▼
Shipment.sol / Provenance Contract
        │
        │ 🔟 Save shipment booking hash
        │    linked to payment record
        │
        ▼
Django Backend
        │
        │ 1️⃣1️⃣ Verifies tx receipt from Ganache
        │ 1️⃣2️⃣ Updates PostgreSQL:
        │      status = Deposit Paid
        │      balance_due = remaining amount
        │
        ▼
Shipment Operations Continue
        │
        │ 1️⃣3️⃣ Air / Sea / Customs / Delivery continues
        │
        ▼
Remaining Balance Payment (Later)
        │
        │ 1️⃣4️⃣ User opens Django Payments GUI
        │ 1️⃣5️⃣ Clicks "Pay Remaining Balance"
        │
        ▼
MetaMask Popup
        │
        │ 1️⃣6️⃣ Confirms remaining ETH amount
        │
        ▼
Ganache → Payment.sol
        │
        │ 1️⃣7️⃣ Stores second transaction:
        │      payment stage = FINAL
        │
        ▼
Django Backend
        │
        │ 1️⃣8️⃣ Marks shipment = Fully Paid
        │ 1️⃣9️⃣ Release final documents / delivery proof
        │
        ▼
Dashboard / User Interface
        │
        │ 2️⃣0️⃣ User sees:
        │      Deposit Paid ✅
        │      Final Paid ✅
        │      Shipment Delivered 🚢
```
   *Figure 3: Flow of ProducerProduct.sol showing producer approval, product creation, and on-chain product retrieval.*
## Code Documentation & Comments
Each Django model and smart contract function should have comments explaining:
- Purpose
- Parameters
- Returns or effects
- Example usage
  <br>**Example in Django model:**<br>
  <img width="1150" height="331" alt="image" src="https://github.com/user-attachments/assets/fdb6356f-32ff-4390-849e-bfd02cc609c6" /><br>
  *Figure 4: Example of properly commented Django model explaining purpose, parameters, and usage.*
  
  ---
Developed by **Group10**, Spring 2026, Arizona State University

        



