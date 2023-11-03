from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.commitment_config import CommitmentLevel
from solders.rpc.config import (
    RpcSimulateTransactionConfig,
    RpcSimulateTransactionAccountsConfig,
)
from solders.rpc.requests import SimulateVersionedTransaction, SimulateLegacyTransaction
from solders.rpc.responses import SimulateTransactionResp
from solders.transaction import VersionedTransaction


def simulate_body(txn, addresses):
    config = RpcSimulateTransactionConfig(
        sig_verify=True,
        commitment=CommitmentLevel.Confirmed,
        accounts=RpcSimulateTransactionAccountsConfig(addresses=addresses),
    )
    if isinstance(txn, Transaction):
        if txn.recent_blockhash is None:
            raise ValueError("transaction must have a valid blockhash")
        return SimulateLegacyTransaction(txn.to_solders(), config)
    return SimulateVersionedTransaction(txn, config)


async def custom_simulate(client: AsyncClient, txn, addresses):
    body = simulate_body(txn, addresses)
    return await client._provider.make_request(body, SimulateTransactionResp)
