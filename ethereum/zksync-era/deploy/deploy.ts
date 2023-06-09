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

    /// DexManagerFacet
    artifact = await deployer.loadArtifact("DexManagerFacet");
    contract = await deployer.deploy(artifact);
    const DexManagerFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${DexManagerFacet}`);
    deployed["DexManagerFacet"] = DexManagerFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// CelerFacet
    artifact = await deployer.loadArtifact("CelerFacet");
    contract = await deployer.deploy(artifact);
    const CelerFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${CelerFacet}`);
    deployed["CelerFacet"] = CelerFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// WithdrawFacet
    artifact = await deployer.loadArtifact("WithdrawFacet");
    contract = await deployer.deploy(artifact);
    const WithdrawFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${WithdrawFacet}`);
    deployed["WithdrawFacet"] = WithdrawFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// OwnershipFacet
    artifact = await deployer.loadArtifact("OwnershipFacet");
    contract = await deployer.deploy(artifact);
    const OwnershipFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${OwnershipFacet}`);
    deployed["OwnershipFacet"] = OwnershipFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// GenericSwapFacet
    artifact = await deployer.loadArtifact("GenericSwapFacet");
    contract = await deployer.deploy(artifact);
    const GenericSwapFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${GenericSwapFacet}`);
    deployed["GenericSwapFacet"] = GenericSwapFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// SerdeFacet
    artifact = await deployer.loadArtifact("SerdeFacet");
    contract = await deployer.deploy(artifact);
    const SerdeFacet = contract.address;
    console.log(`${artifact.contractName} was deployed to ${SerdeFacet}`);
    deployed["SerdeFacet"] = SerdeFacet
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    ///===== facet end ====

    /// SoDiamond
    artifact = await deployer.loadArtifact("SoDiamond");
    contract = await deployer.deploy(artifact, [owner, deployed["DiamondCutFacet"]]);
    const SoDiamond = contract.address;
    console.log(`${artifact.contractName} was deployed to ${SoDiamond}`);
    deployed["SoDiamond"] = SoDiamond
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// LibSoFeeCelerV1
    artifact = await deployer.loadArtifact("LibSoFeeCelerV1");
    contract = await deployer.deploy(artifact);
    const LibSoFeeCelerV1 = contract.address;
    console.log(`${artifact.contractName} was deployed to ${LibSoFeeCelerV1}`);
    deployed["LibSoFeeCelerV1"] = LibSoFeeCelerV1
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))

    /// LibCorrectSwapV1
    artifact = await deployer.loadArtifact("LibCorrectSwapV1");
    contract = await deployer.deploy(artifact);
    const LibCorrectSwapV1 = contract.address;
    console.log(`${artifact.contractName} was deployed to ${LibCorrectSwapV1}`);
    deployed["LibCorrectSwapV1"] = LibCorrectSwapV1
    writeFileSync(DEPLOYED, JSON.stringify(deployed, null, 4))
}

