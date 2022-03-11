#!/usr/bin/env python3

import base64
import click
import json
from box import Box
from construct import Struct as CStruct, Int8ul, Int64ul, Switch
from enum import IntEnum
from nacl.public import PrivateKey
from solana.rpc.api import Client, Keypair
from solana.rpc.types import TxOpts
from solana.system_program import (
    create_account_with_seed,
    AccountMeta,
    CreateAccountWithSeedParams,
    PublicKey,
    Transaction,
    TransactionInstruction,
)


class InstructionType(IntEnum):
    NOOP = 0
    MINT = 1


NOOP_LAYOUT = CStruct()

MINT_LAYOUT = CStruct(
    'amount' / Int64ul
)

INSTRUCTION_LAYOUT = CStruct(
    'code' / Int8ul,
    'data' / Switch(lambda self: self.code,
                    {
                        InstructionType.NOOP: NOOP_LAYOUT,
                        InstructionType.MINT: MINT_LAYOUT
                    }
    )
)
ACCOUNT_LAYOUT = CStruct('amount' / Int64ul)


class SolanaProgramApi:
    SEED = 'Samples'

    def __init__(self, client: Client, program_id: PublicKey):
        self.client = client
        self.program_id = program_id

    def noop(self, wallet: Keypair):
        instruction = TransactionInstruction(
            keys=[],
            program_id=self.program_id,
            data=INSTRUCTION_LAYOUT.build(dict(code=InstructionType.NOOP, data=dict())),
        )
        return self.send_transaction(instruction, wallet)

    def mint(self, wallet: Keypair, amount: int):
        program = self.ensure_account(wallet)
        instruction = TransactionInstruction(
            keys=[AccountMeta(pubkey=program, is_signer=False, is_writable=True)],
            program_id=self.program_id,
            data=INSTRUCTION_LAYOUT.build(dict(code=InstructionType.MINT, data=dict(amount=amount))),
        )
        return self.send_transaction(instruction, wallet)

    def send_transaction(self, instruction: TransactionInstruction, *signers):
        txn = Transaction()
        txn.add(instruction)

        click.echo('Sending transaction...')
        opts = TxOpts(skip_confirmation=False)
        response = Box(self.client.send_transaction(txn, *signers, opts=opts))

        click.echo(f'Transaction {response.result} has been confirmed.')
        return Box(self.client.get_transaction(response['result']))

    def ensure_account(self, owner: Keypair):
        program = PublicKey.create_with_seed(owner.public_key, self.SEED, self.program_id)
        program_account = Box(self.client.get_account_info(program))
        if not program_account.result.value:
            space = len(INSTRUCTION_LAYOUT.build(dict(code=InstructionType.MINT, data=dict(amount=0))))
            lamports = self.client.get_minimum_balance_for_rent_exemption(space)

            txn = Transaction()
            txn.add(
                create_account_with_seed(
                    CreateAccountWithSeedParams(
                        from_pubkey=owner.public_key,
                        base_pubkey=owner.public_key,
                        seed=dict(length=len(self.SEED), chars=self.SEED),
                        new_account_pubkey=program,
                        lamports=lamports['result'],
                        space=space,
                        program_id=self.program_id,
                    )
                )
            )

            response = self.client.send_transaction(txn, owner)
        return program

    def get_account(self, owner: PublicKey) -> ACCOUNT_LAYOUT:
        program = PublicKey.create_with_seed(owner, self.SEED, self.program_id)
        program_account = Box(self.client.get_account_info(program))
        program_data = program_account.result.value.data[0]

        account = ACCOUNT_LAYOUT.parse(base64.decodebytes(program_data.encode('ascii')))
        return account


def load_wallet(filename: str) -> Keypair:
    with open(filename, 'r') as f:
        data = f.read()

    keypair = bytearray(json.loads(data))
    return Keypair(PrivateKey(bytes(keypair[:32])))


def echo_transaction(txn: Box):
    click.echo(f'Status: {txn.result.meta.status}')
    for message in txn.result.meta.logMessages:
        click.echo(message)


@click.group()
@click.option('--url', default='http://localhost:8899')
@click.argument('program_id', required=True, type=PublicKey)
@click.pass_context
def cli(ctx: click.Context, url: str, program_id: PublicKey):
    client = Client(url)
    ctx.obj = SolanaProgramApi(client, program_id)


@cli.command()
@click.option('--wallet', default='wallets/wallet_1.json', type=load_wallet)
@click.pass_context
def noop(ctx: click.Context, wallet: Keypair):
    program: SolanaProgramApi = ctx.obj

    txn = program.noop(wallet)
    echo_transaction(txn)


@cli.command()
@click.option('--wallet', default='wallets/wallet_1.json', type=load_wallet)
@click.option('--amount', required=True, type=int)
@click.pass_context
def mint(ctx: click.Context, wallet: Keypair, amount: int):
    program: SolanaProgramApi = ctx.obj

    txn = program.mint(wallet, amount)
    echo_transaction(txn)

    click.echo(program.get_account(wallet.public_key))


@cli.command()
@click.option('--program-wallet', default='wallets/wallet_1.json', type=load_wallet)
@click.pass_context
def set_rate(ctx: click.Context, wallet: Keypair):
    pass


def deposit():
    pass


def withdraw():
    pass


if __name__ == '__main__':
    cli()
