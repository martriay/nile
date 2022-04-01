"""Utility for signing transactions for an Account on Starknet."""

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import private_to_stark_key, sign
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.core.os.transaction_hash import calculate_transaction_hash_common, TransactionHashPrefix
from starkware.starknet.definitions.general_config import StarknetChainId

TRANSACTION_VERSION = 0


class Signer:
    """Utility for signing transactions for an Account on Starknet."""

    def __init__(self, private_key):
        """Construct a Signer object. Takes a private key."""
        self.private_key = private_key
        self.public_key = private_to_stark_key(private_key)

    def sign(self, message_hash):
        """Sign a message hash."""
        return sign(msg_hash=message_hash, priv_key=self.private_key)

    def sign_transaction(self, sender, calls, nonce, max_fee=0):
        """Sign a transaction for an Account."""
        (call_array, calldata) = from_call_to_call_array(calls)
        message_hash = get_transaction_hash(
            int(sender, 16), call_array, calldata, nonce, max_fee
        )

        sig_r, sig_s = self.sign(message_hash)

        return (call_array, calldata, sig_r, sig_s)


# Auxiliary functions


def from_call_to_call_array(calls):
    """Transform from Call to CallArray."""
    call_array = []
    calldata = []
    for _, call in enumerate(calls):
        assert len(call) == 3, "Invalid call parameters"
        entry = (
            int(call[0], 16),
            get_selector_from_name(call[1]),
            len(calldata),
            len(call[2]),
        )
        call_array.append(entry)
        calldata.extend(call[2])
    return (call_array, calldata)


def hash_multicall(sender, calls, nonce, max_fee):
    """Hash a MultiCall."""
    hash_array = []
    for call in calls:
        call_elements = [int(call[0], 16), call[1], compute_hash_on_elements(call[2])]
        hash_array.append(compute_hash_on_elements(call_elements))

    message = [
        str_to_felt("StarkNet Transaction"),
        sender,
        compute_hash_on_elements(hash_array),
        nonce,
        max_fee,
        TRANSACTION_VERSION,
    ]
    return compute_hash_on_elements(message)


def get_transaction_hash(account, call_array, calldata, nonce, max_fee):
    execute_calldata = [
        len(call_array),
        *[x for t in call_array for x in t],
        len(calldata),
        *calldata,
        nonce]

    return calculate_transaction_hash_common(
        TransactionHashPrefix.INVOKE,
        TRANSACTION_VERSION,
        account,
        get_selector_from_name('__execute__'),
        execute_calldata,
        max_fee,
        StarknetChainId.TESTNET.value,
        []
    )


def str_to_felt(text):
    """Convert from string to felt."""
    b_text = bytes(text, "ascii")
    return int.from_bytes(b_text, "big")
