import { Wallet } from "zksync-web3";
import { HardhatRuntimeEnvironment } from "hardhat/types";
import { Deployer } from "@matterlabs/hardhat-zksync-deploy";
import * as dotenv from "dotenv";
import { readFileSync, writeFileSync } from "fs";

const DEPLOYED = "deployed.json"

// An example of a deploy script that will deploy.
export default async function (hre: HardhatRuntimeEnvironment) {
    console.log(`Running deploy script for the contracts`);
    dotenv.config({path:"../.env"});

    // Initialize the wallet.

    const wallet = new Wallet(process.env.PRIVATE_KEY);

    // Create deployer object and load the artifact of the contract we want to deploy.
    const deployer = new Deployer(hre, wallet);

    const owner = deployer.zkWallet.address;

    let deployed = function (path) {
        try {
            return JSON.parse(readFileSync(path,'utf8'))
        } catch {
            return {}
        }
    }(DEPLOYED)

    let artifact
    let contract

    ///===== facet start ====
    /// DiamondCutFacet
    artifact = await deployer.loadArtifact("DiamondCutFacet");
    contract = await deployer.deploy(artifact);
    const DiamondCutFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${DiamondCutFacet}`);
    deployed["DiamondCutFacet"] = DiamondCutFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// DiamondLoupeFacet
    artifact = await deployer.loadArtifact("DiamondLoupeFacet");
    contract = await deployer.deploy(artifact);
    const DiamondLoupeFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${DiamondLoupeFacet}`);
    deployed["DiamondLoupeFacet"] = DiamondLoupeFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// LibSoFeeBoolV2
    artifact = await deployer.loadArtifact("LibSoFeeBoolV2");
    contract = await deployer.deploy(artifact, ["0xd3c21bcecceda1000000",
    "0xb5e620f48000", "0xD4c56833A6D4C83A81972dA7e0eDA924F0729989"]);
    const LibSoFeeBoolV2 = contract.address;
    console.log(`${artifact.contractName} was deployed to ${LibSoFeeBoolV2}`);
    deployed["LibSoFeeBoolV2"] = LibSoFeeBoolV2
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

       /// BoolFacet
    artifact = await deployer.loadArtifact("BoolFacet");
    contract = await deployer.deploy(artifact, []);
    const BoolFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${BoolFacet}`);
    deployed["BoolFacet"] = BoolFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))
}

