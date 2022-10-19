"""nile common module."""
import io
import json
import os
import re
import sys
from types import SimpleNamespace

from starkware.starknet.cli.starknet_cli import NETWORKS

from nile.utils import normalize_number, str_to_felt

CONTRACTS_DIRECTORY = "contracts"
BUILD_DIRECTORY = "artifacts"
TEMP_DIRECTORY = ".temp"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}/abis"
DEPLOYMENTS_FILENAME = "deployments.txt"
DECLARATIONS_FILENAME = "declarations.txt"
ACCOUNTS_FILENAME = "accounts.json"
NODE_FILENAME = "node.json"
RETRY_AFTER_SECONDS = 30


def get_gateway():
    """Get the StarkNet node details."""
    try:
        with open(NODE_FILENAME, "r") as f:
            gateway = json.load(f)
            return gateway

    except FileNotFoundError:
        with open(NODE_FILENAME, "w") as f:
            f.write('{"localhost": "http://127.0.0.1:5050/"}')


GATEWAYS = get_gateway()


def get_all_contracts(ext=None, directory=None):
    """Get all cairo contracts in the default contract directory."""
    if ext is None:
        ext = ".cairo"

    files = list()
    for (dirpath, _, filenames) in os.walk(
        directory if directory else CONTRACTS_DIRECTORY
    ):
        files += [
            os.path.join(dirpath, file) for file in filenames if file.endswith(ext)
        ]

    return files


def parse_information(x):
    """Extract information from deploy/declare command."""
    # address is 64, tx_hash is 64 chars long
    address, tx_hash = re.findall("0x[\\da-f]{1,64}", str(x))
    return normalize_number(address), normalize_number(tx_hash)


def stringify(x, process_short_strings=False):
    """Recursively convert list or tuple elements to strings."""
    if isinstance(x, list) or isinstance(x, tuple):
        return [stringify(y, process_short_strings) for y in x]
    else:
        if process_short_strings and is_string(x):
            return str(str_to_felt(x))
        return str(x)


def prepare_params(params):
    """Sanitize call, invoke, and deploy parameters."""
    if params is None:
        params = []
    return stringify(params, True)


def is_string(param):
    """Identify a param as string if is not int or hex."""
    is_int = True
    is_hex = True

    # convert to integer
    try:
        int(param)
    except Exception:
        is_int = False

    # convert to hex (starting with 0x)
    try:
        assert param.startswith("0x")
        int(param, 16)
    except Exception:
        is_hex = False

    return not is_int and not is_hex


def is_alias(param):
    """Identiy param as alias (instead of address)."""
    return is_string(param)


def get_gateway_url(network):
    """Return gateway URL for specified network."""
    if network == "localhost":
        return GATEWAYS.get(network)
    else:
        network = "alpha-" + network
        return f"https://{NETWORKS[network]}/gateway"


def get_feeder_url(network):
    """Return feeder gateway URL for specified network."""
    if network == "localhost":
        return GATEWAYS.get(network)
    else:
        network = "alpha-" + network
        return f"https://{NETWORKS[network]}/feeder_gateway"


async def capture_stdout(func):
    """Return the stdout during the passed function call."""
    stdout = sys.stdout
    sys.stdout = io.StringIO()
    await func
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    result = output.rstrip()
    return result


def set_args(network):
    """Set context args for StarkNet CLI call."""
    args = {
        "gateway_url": get_gateway_url(network),
        "feeder_gateway_url": get_feeder_url(network),
        "wallet": "",
        "network_id": network,
        "account_dir": None,
        "account": None,
    }
    ret_obj = SimpleNamespace(**args)
    return ret_obj
