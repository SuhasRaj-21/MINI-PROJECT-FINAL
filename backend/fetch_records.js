const { ethers } = require('ethers');

async function main() {
    const rpcUrl = 'http://localhost:8545';
    const contractAddress = '0x5FbDB2315678afecb367f032d93F642f64180aa3';
    const provider = new ethers.JsonRpcProvider(rpcUrl);

    const abi = [
        "function getAllRecords() external view returns (tuple(string zone, uint256 aqi, string riskLevel, uint256 timestamp, string dataHash)[])",
        "function totalRecords() external view returns (uint256)"
    ];

    const contract = new ethers.Contract(contractAddress, abi, provider);

    try {
        const total = await contract.totalRecords();
        console.log(`Total records on Blockchain: ${total}`);

        const records = await contract.getAllRecords();
        console.log("\nBlockchain Records:");
        records.forEach((record, index) => {
            console.log(`\n--- Record #${index + 1} ---`);
            console.log(`Zone:       ${record.zone}`);
            console.log(`AQI:        ${record.aqi.toString()}`);
            console.log(`Risk Level: ${record.riskLevel}`);
            console.log(`Timestamp:  ${new Date(Number(record.timestamp) * 1000).toLocaleString()}`);
            console.log(`Data Hash:  ${record.dataHash}`);
        });
    } catch (error) {
        console.error("Error reading blockchain:", error);
    }
}

main();
