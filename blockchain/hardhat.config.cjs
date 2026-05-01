/* used for testing contracts */
/*require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
/* commented this line out
module.exports = {
  solidity: "0.8.20"
};
*/
/* used for deploying contracts to ganache */
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.20",
  networks: {
    ganache: {
      url: "http://127.0.0.1:7545",
      accounts: [
        "0x433f7a3338ea49710663dfd3bc9defba6c764082d6eb890da122b7ca2faf5113"
      ]
    }
  }
};