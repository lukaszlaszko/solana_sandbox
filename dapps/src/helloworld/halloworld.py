import asyncio
import base64
import json
import os
from argparse import ArgumentParser
from box import Box
from construct import Struct as CStruct, Int32ul
from loguru import logger
from nacl.public import PrivateKey
from solana.rpc.async_api import AsyncClient, Keypair
from solana.rpc.types import TxOpts
from solana.system_program import (
    create_account_with_seed,
    AccountMeta,
    CreateAccountWithSeedParams,
    PublicKey,
    Transaction,
    TransactionInstruction,
)
from typing import Tuple


ACCOUNT_LAYOUT = CStruct('counter' / Int32ul)


def load_wallet(filename: str) -> Keypair:
    with open(filename, 'r') as f:
        data = f.read()

    keypair = bytearray(json.loads(data))
    return Keypair(PrivateKey(bytes(keypair[:32])))


async def main():
    async with AsyncClient(args.url) as client:
        connected = await client.is_connected()
        if not connected:
            logger.error(f'Client not connected to {args.url}')
            return os.EX_NOHOST

        version = await client.get_version()
        logger.info(f'api: {version}')

        payer = load_wallet(args.wallet)
        logger.info(f'wallet loaded from `{args.wallet}`: pub key: {payer.public_key}')

        balance = await client.get_balance(payer.public_key)
        logger.info(f'available balance: {balance}')

        seed = 'hello'
        program = PublicKey.create_with_seed(payer.public_key, seed, args.program_id)
        program_account = Box(await client.get_account_info(program), default_box=True)
        if not program_account.result.value:
            logger.info(f'program account for : {payer.public_key} doesnt exist. creating...')

            space = len(ACCOUNT_LAYOUT.build(dict(counter=0)))
            lamports = await client.get_minimum_balance_for_rent_exemption(space)

            txn = Transaction()
            txn.add(
                create_account_with_seed(
                    CreateAccountWithSeedParams(
                        from_pubkey=payer.public_key,
                        base_pubkey=payer.public_key,
                        seed=dict(length=len(seed), chars=seed),
                        new_account_pubkey=program,
                        lamports=lamports['result'],
                        space=space,
                        program_id=args.program_id,
                    )
                )
            )

            response = await client.send_transaction(txn, payer)
            logger.info(f'Create account response: {response}')

            program_account = Box(await client.get_account_info(program))
        logger.info(f'Program account: {program_account.result.value}')

        txn = Transaction()
        instruction = TransactionInstruction(
            keys=[AccountMeta(pubkey=program, is_signer=False, is_writable=True)],
            program_id=args.program_id,
            data=bytearray(),
        )

        txn.add(instruction)

        opts = TxOpts(skip_confirmation=False)
        response = Box(await client.send_transaction(txn, payer, opts=opts))
        logger.info(f'Transaction response: {response}')

        tx_info = await client.get_transaction(response.result)
        logger.info(f'Tx info: {tx_info}')

        program_account = Box(await client.get_account_info(program))
        program_data = program_account.result.value.data[0]
        account = ACCOUNT_LAYOUT.parse(base64.decodebytes(program_data.encode('ascii')))
        logger.info(f'Count: {account.counter}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8899')
    parser.add_argument('--wallet', default='wallets/wallet_1.json')
    parser.add_argument('program_id', type=PublicKey)

    args = parser.parse_args()
    asyncio.run(main())
