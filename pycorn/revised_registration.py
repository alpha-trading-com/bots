"""
This module provides functionalities for registering a wallet with the subtensor network using Proof-of-Work (PoW).

Extrinsics:
- register_extrinsic: Registers the wallet to the subnet.
- burned_register_extrinsic: Registers the wallet to chain by recycling TAO.
"""

import time
from typing import Optional, Union, TYPE_CHECKING

from bittensor.utils import unlock_key
from bittensor.utils.btlogging import logging
from bittensor.utils.registration import create_pow, log_no_torch_error, torch
from bittensor_wallet import Wallet
from bittensor.core.subtensor import Subtensor
from bittensor.utils.registration.pow import POWSolution


def quick_register(
    subtensor: "Subtensor",
    netuid: int,
    wallet: "Wallet",
    wait_for_inclusion: bool = False,
    wait_for_finalization: bool = True,
) -> tuple[bool, str]:
    """
    Performs a burned register extrinsic call to the Subtensor chain.

    This method sends a registration transaction to the Subtensor blockchain using the burned register mechanism.

    Args:
        subtensor (bittensor.core.subtensor.Subtensor): Subtensor instance.
        netuid (int): The network unique identifier to register on.
        wallet (bittensor_wallet.Wallet): The wallet to be registered.
        wait_for_inclusion (bool): Whether to wait for the transaction to be included in a block. Default is False.
        wait_for_finalization (bool): Whether to wait for the transaction to be finalized. Default is True.

    Returns:
        Tuple[bool, Optional[str]]: A tuple containing a boolean indicating success or failure, and an optional error
            message.
    """

    # create extrinsic call
    call = subtensor.substrate.compose_call(
        call_module="SubtensorModule",
        call_function="burned_register",
        call_params={
            "netuid": netuid,
            "hotkey": wallet.hotkey.ss58_address,
        },
    )
    return subtensor.sign_and_send_extrinsic(
        call=call,
        wallet=wallet,
        wait_for_inclusion=wait_for_inclusion,
        wait_for_finalization=wait_for_finalization,
    )


