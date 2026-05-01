async function main() {
  const Tracking = await ethers.getContractFactory("TrackingContract");

  const tracking = await Tracking.deploy();

  await tracking.waitForDeployment();

  console.log("Tracking deployed to:", await tracking.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});