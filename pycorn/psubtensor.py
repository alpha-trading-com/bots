import bittensor as bt
import json
import time
from typing import Optional
from async_substrate_interface.types import ScaleType, ScaleObj
from async_substrate_interface.utils import hex_to_bytes

from utils import get_next_id


class PSubtensor:
    @staticmethod
    def make_payload(id_: str, method: str, params: list) -> dict:
        return {
            "id": id_,
            "payload": {"jsonrpc": "2.0", "method": method, "params": params},
        }
    

    def __init__(self, network: str = 'finney'):
        self.subtensor = bt.subtensor(network=network)
        self.ws = self.subtensor.substrate.ws

    def _make_rpc_request(
        self,
        payload,
    ):
        item_id = get_next_id()
        self.ws.send(json.dumps({**payload["payload"], **{"id": item_id}}))
        response = json.loads(self.ws.recv())   
        return response
    

    def get_block_number(self):
        try:
            response = self._make_rpc_request(
                self.make_payload("rpc_request", "chain_getHeader", [None]),
            )
            return int(response["result"]["number"],0)
        except Exception as e:
            print(e)
            return None

    def get_chain_head(self) -> str:
        try:
            response = self._make_rpc_request(
                self.make_payload(
                    "rpc_request",
                    "chain_getHead",
                    [],
                )
            )
            return response["result"]
        except Exception as e:
            print(e)
            return None

    def runtime_call(
        self,
        api: str,
        method: str,
        params: Optional[Union[list, dict]] = None,
        block_hash: Optional[str] = None,
    ) -> ScaleType:
        """
        Calls a runtime API method

        Args:
            api: Name of the runtime API e.g. 'TransactionPaymentApi'
            method: Name of the method e.g. 'query_fee_details'
            params: List of parameters needed to call the runtime API
            block_hash: Hash of the block at which to make the runtime API call

        Returns:
             ScaleType from the runtime call
        """
        self.init_runtime(block_hash=block_hash)

        if params is None:
            params = {}

        try:
            metadata_v15_value = self.runtime.metadata_v15.value()

            apis = {entry["name"]: entry for entry in metadata_v15_value["apis"]}
            api_entry = apis[api]
            methods = {entry["name"]: entry for entry in api_entry["methods"]}
            runtime_call_def = methods[method]
        except KeyError:
            raise ValueError(f"Runtime API Call '{api}.{method}' not found in registry")

        if _determine_if_old_runtime_call(runtime_call_def, metadata_v15_value):
            result = self._do_runtime_call_old(api, method, params, block_hash)

            return result

        if isinstance(params, list) and len(params) != len(runtime_call_def["inputs"]):
            raise ValueError(
                f"Number of parameter provided ({len(params)}) does not "
                f"match definition {len(runtime_call_def['inputs'])}"
            )

        # Encode params
        param_data = b""
        for idx, param in enumerate(runtime_call_def["inputs"]):
            param_type_string = f"scale_info::{param['ty']}"
            if isinstance(params, list):
                param_data += self.encode_scale(param_type_string, params[idx])
            else:
                if param["name"] not in params:
                    raise ValueError(f"Runtime Call param '{param['name']}' is missing")

                param_data += self.encode_scale(
                    param_type_string, params[param["name"]]
                )

        # RPC request
        result_data = self.rpc_request(
            "state_call", [f"{api}_{method}", param_data.hex(), block_hash]
        )
        output_type_string = f"scale_info::{runtime_call_def['output']}"

        # Decode result
        result_bytes = hex_to_bytes(result_data["result"])
        result_obj = ScaleObj(self.decode_scale(output_type_string, result_bytes))

        return result_obj

    def get_subnet_info(self, netuid: int):
        try:
            block_hash = self.get_chain_head()
            response = self._make_rpc_request(
                self.make_payload("rpc_request", "chain_getHead", [block_hash]),
            )
            return response["result"]
        except Exception as e:
            print(e)
            return None
        

if __name__ == "__main__":
    psubtensor = PSubtensor()
    while True:
        print(psubtensor.get_chain_head())