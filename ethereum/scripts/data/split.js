const fs = require("fs");
const {MerkleTree} = require("merkletreejs");
const keccak256 = require("keccak256");
const {utils} = require("ethers");
const BigNumber = require("bignumber.js");


const elementWithIndexAmount = function (data) {
    return data.map((x) =>
        utils.solidityKeccak256(["uint256", "address", "uint256"], [x[0], x[1], BigInt(x[2])])
    );
}

function logWithTimestamp(message) {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${message}`);
}

const generateChunk = () => {
    let jsonData = require("./op_account_20231115.json");
    jsonData.sort((a, b) => a[0].toLowerCase() < b[0].toLowerCase() ? -1 : 1)
    jsonData = jsonData.map((d, index) => {
        return [index, d[0], d[1]];
    })

    const DESIRED_COHORT_SIZE = 101

    const addressChunks = {}

    logWithTimestamp("Create Tree")
    const nodes = elementWithIndexAmount(jsonData)
    const merkleTree = new MerkleTree(nodes, keccak256, {sort: true});

    logWithTimestamp("Generate Proof")
    for (let i = 0; i < jsonData.length; i += DESIRED_COHORT_SIZE) {
        const lastIndex = Math.min(i + DESIRED_COHORT_SIZE - 1, jsonData.length - 1)
        addressChunks[jsonData[i][1].toLowerCase()] = jsonData[lastIndex][1].toLowerCase()
        const addressProofs = {}
        for (let j = i; j <= lastIndex; j += 1) {
            addressProofs[jsonData[j][1]] = {
                "index": jsonData[j][0],
                "amount": jsonData[j][2],
                "proof": merkleTree.getHexProof(nodes[j])
            }
            if (j % 2000 === 0) {
                logWithTimestamp(`Process ${Math.floor(j / jsonData.length * 100)}%`)
            }
        }

        fs.writeFile(`./chunks/${jsonData[i][1].toLowerCase()}.json`, JSON.stringify(addressProofs, null, 2), (err) => {
            if (err) {
                console.error('Error writing JSON file:', err);
            } else {
                console.log('JSON file has been written.');
            }
        });

    }

    fs.writeFile(`./chunks/mapping.json`, JSON.stringify(addressChunks, null, 2), (err) => {
        if (err) {
            console.error('Error writing JSON file:', err);
        } else {
            console.log('JSON file has been written.');
        }
    });

    fs.writeFile(`./chunks/root.json`, JSON.stringify({"root": merkleTree.getHexRoot()}, null, 2), (err) => {
        if (err) {
            console.error('Error writing JSON file:', err);
        } else {
            console.log('JSON file has been written.');
        }
    });
    logWithTimestamp("Generate End")
}


generateChunk()
