"""Wrappers for transactions for adding Nile extra logic."""

import dataclasses
from typing import List

from nile.core.declare import declare
from nile.core.deploy import deploy_account, deploy_contract


@dataclasses.dataclass
class BaseTxWrapper:
    """Base Wrapper logic."""

    tx: object
    account: object

    async def execute(self, watch_mode=None):
        """Execute the wrapped transaction."""
        return await self.tx.execute(signer=self.account.signer, watch_mode=watch_mode)

    async def estimate_fee(self):
        """Estimate the fee of the wrapped transaction."""
        return await self.tx.estimate_fee(signer=self.account.signer)

    async def simulate(self):
        """Simulate the wrapped transaction."""
        return await self.tx.simulate(signer=self.account.signer)


@dataclasses.dataclass
class InvokeTxWrapper(BaseTxWrapper):
    """Wrapper for send."""

    pass


@dataclasses.dataclass
class DeclareTxWrapper(BaseTxWrapper):
    """
    Wrapper for declare.

    Handle registrations and other Nile specific logic.
    """

    alias: str = None
    overriding_path: List[str] = None

    async def execute(self, watch_mode=None):
        """Execute the wrapped transaction."""
        return await declare(
            transaction=self.tx,
            signer=self.account.signer,
            alias=self.alias,
            overriding_path=self.overriding_path,
            watch_mode=watch_mode,
        )


@dataclasses.dataclass
class DeployContractTxWrapper(BaseTxWrapper):
    """
    Wrapper for deploy_contract.

    Handle registrations and other Nile specific logic.
    """

    alias: str = None
    contract_name: str = None
    predicted_address: int = 0
    overriding_path: List[str] = None
    abi: str = None

    async def execute(self, watch_mode=None):
        """Execute the wrapped transaction."""
        return await deploy_contract(
            transaction=self.tx,
            signer=self.account.signer,
            contract_name=self.contract_name,
            alias=self.alias,
            predicted_address=self.predicted_address,
            overriding_path=self.overriding_path,
            abi=self.abi,
            watch_mode=watch_mode,
        )


@dataclasses.dataclass
class DeployAccountTxWrapper(BaseTxWrapper):
    """
    Wrapper for deploy_account.

    Handle registrations and other Nile specific logic.
    """

    alias: str = None
    contract_name: str = None
    predicted_address: int = 0
    overriding_path: List[str] = None
    abi: str = None

    async def execute(self, watch_mode=None):
        """Execute the wrapped transaction."""
        return await deploy_account(
            transaction=self.tx,
            signer=self.account.signer,
            contract_name=self.contract_name,
            alias=self.alias,
            predicted_address=self.predicted_address,
            overriding_path=self.overriding_path,
            abi=self.abi,
            watch_mode=watch_mode,
        )
