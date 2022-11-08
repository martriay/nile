#!/usr/bin/env python
"""Nile CLI entry point."""
import logging

import click

from nile.common import is_alias
from nile.core.account import Account
from nile.core.call_or_invoke import call_or_invoke as call_or_invoke_command
from nile.core.clean import clean as clean_command
from nile.core.compile import compile as compile_command
from nile.core.deploy import deploy as deploy_command
from nile.core.init import init as init_command
from nile.core.node import node as node_command
from nile.core.plugins import load_plugins
from nile.core.run import run as run_command
from nile.core.test import test as test_command
from nile.core.version import version as version_command
from nile.utils import normalize_number
from nile.utils.debug import debug as debug_command
from nile.utils.get_accounts import get_accounts as get_accounts_command
from nile.utils.get_accounts import (
    get_predeployed_accounts as get_predeployed_accounts_command,
)
from nile.utils.get_nonce import get_nonce as get_nonce_command

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

NETWORKS = ("localhost", "integration", "goerli", "goerli2", "mainnet")


def network_option(f):
    """Configure NETWORK option for the cli."""
    return click.option(  # noqa: E731
        "--network",
        envvar="STARKNET_NETWORK",
        default="localhost",
        help=f"Select network, one of {NETWORKS}",
        callback=_validate_network,
    )(f)


def mainnet_token_option(f):
    """Configure TOKEN option for the cli."""
    return click.option(
        "--token",
        help="Used for deploying contracts in Alpha Mainnet.",
    )(f)


def _validate_network(_ctx, _param, value):
    """Normalize network values."""
    # check if value is known
    if value in NETWORKS:
        return value
    # normalize goerli
    if "testnet" == value:
        return "goerli"
    # normalize localhost
    if "127.0.0.1" == value:
        return "localhost"
    # raise if value is invalid
    raise click.BadParameter(f"'{value}'. Use one of {NETWORKS}")


@click.group()
def cli():
    """Nile CLI group."""
    pass


@cli.command()
def init():
    """Nile CLI group."""
    init_command()


@cli.command()
@click.argument("path", nargs=1)
@network_option
def run(path, network):
    """Run Nile scripts with NileRuntimeEnvironment."""
    run_command(path, network)


@cli.command()
@click.argument("contract_name", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--max_fee", nargs=1)
@click.option("--salt", nargs=1, default=0)
@click.option("--unique", is_flag=True)
@click.option("--account")
@click.option("--alias")
@click.option("--abi")
@click.option("--udc_address")
@mainnet_token_option
@network_option
def deploy(
    contract_name,
    salt,
    params,
    max_fee,
    unique,
    account,
    alias,
    abi,
    udc_address,
    token,
    network,
):
    """Deploy StarkNet smart contract."""
    if account is not None:
        account = Account(account, network)
        account.deploy_contract(
            contract_name,
            salt,
            unique,
            params,
            alias,
            deployer_address=udc_address,
            max_fee=max_fee,
            abi=abi,
        )
    else:
        deploy_command(
            contract_name, params, network, alias, abi=abi, mainnet_token=token
        )


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("contract_name", nargs=1)
@click.option("--max_fee", nargs=1)
@click.option("--alias")
@click.option("--overriding_path")
@mainnet_token_option
@network_option
def declare(
    signer,
    contract_name,
    network,
    max_fee=None,
    alias=None,
    overriding_path=None,
    token=None,
):
    """Declare a StarkNet smart contract through an Account."""
    account = Account(signer, network)
    account.declare(
        contract_name,
        alias=alias,
        max_fee=max_fee,
        overriding_path=overriding_path,
        mainnet_token=token,
    )


@cli.command()
@click.argument("signer", nargs=1)
@network_option
def setup(signer, network):
    """Set up an Account contract."""
    Account(signer, network)


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("address_or_alias", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--max_fee", nargs=1)
@click.option("--simulate", "query", flag_value="simulate")
@click.option("--estimate_fee", "query", flag_value="estimate_fee")
@network_option
def send(signer, address_or_alias, method, params, network, max_fee=None, query=None):
    """Invoke a contract's method through an Account."""
    account = Account(signer, network)
    print(
        "Calling {} on {} with params: {}".format(
            method, address_or_alias, [x for x in params]
        )
    )
    # address_or_alias is not normalized first here because
    # Account.send is part of Nile's public API and can accept hex addresses
    out = account.send(
        address_or_alias, method, params, max_fee=max_fee, query_type=query
    )

    print(out)


@cli.command()
@click.argument("address_or_alias", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@network_option
def call(address_or_alias, method, params, network):
    """Call functions of StarkNet smart contracts."""
    if not is_alias(address_or_alias):
        address_or_alias = normalize_number(address_or_alias)
    out = call_or_invoke_command(address_or_alias, "call", method, params, network)
    print(out)


@cli.command()
@click.argument("contracts", nargs=-1)
def test(contracts):
    """
    Run cairo test contracts.

    $ nile test
      Compiles all test contracts in CONTRACTS_DIRECTORY

    $ nile test contracts/MyContract.test.cairo
      Runs tests in MyContract.test.cairo

    $ nile test contracts/foo.test.cairo contracts/bar.test.cairo
      Runs tests in foo.test.cairo and bar.test.cairo
    """
    test_command(contracts)


@cli.command()
@click.argument("contracts", nargs=-1)
@click.option("--directory")
@click.option("--cairo_path")
@click.option("--account_contract", is_flag="True")
@click.option("--disable-hint-validation", is_flag=True)
def compile(
    contracts, directory, cairo_path, account_contract, disable_hint_validation
):
    """
    Compile cairo contracts.

    $ compile.py
      Compiles all contracts in CONTRACTS_DIRECTORY

    $ compile.py contracts/MyContract.cairo
      Compiles MyContract.cairo

    $ compile.py contracts/foo.cairo contracts/bar.cairo
      Compiles foo.cairo and bar.cairo
    """
    compile_command(
        contracts, directory, cairo_path, account_contract, disable_hint_validation
    )


@cli.command()
def clean():
    """Remove default build directory."""
    clean_command()


@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=5050)
@click.option("--seed", type=int)
@click.option("--lite_mode", is_flag=True)
def node(host, port, seed, lite_mode):
    """Start StarkNet local network.

    $ nile node
      Start StarkNet local network at port 5050

    $ nile node --host HOST --port 5001
      Start StarkNet network on address HOST listening at port 5001

    $ nile node --seed SEED
      Start StarkNet local network with seed SEED

    $ nile node --lite_mode
      Start StarkNet network on lite-mode
    """
    node_command(host, port, seed, lite_mode)


@cli.command()
@click.version_option()
def version():
    """Print out toolchain version."""
    version_command()


@cli.command()
@click.argument("tx_hash", nargs=1)
@network_option
@click.option("--contracts_file", nargs=1)
def debug(tx_hash, network, contracts_file):
    """Locate an error in a transaction using contracts."""
    debug_command(normalize_number(tx_hash), network, contracts_file)


@cli.command()
@network_option
@click.option("--predeployed/--registered", default=False)
def get_accounts(network, predeployed):
    """Retrieve and manage deployed accounts."""
    if not predeployed:
        return get_accounts_command(network)
    else:
        return get_predeployed_accounts_command(network)


@cli.command()
@click.argument("contract_address")
@network_option
def get_nonce(contract_address, network):
    """Retrieve the nonce for a contract."""
    return get_nonce_command(normalize_number(contract_address), network)


cli = load_plugins(cli)


if __name__ == "__main__":
    cli()
