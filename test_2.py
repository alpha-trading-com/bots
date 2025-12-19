import bittensor as bt


if __name__ == '__main__':
    subtensor = bt.Subtensor(network="archive")
    block_hash = subtensor.substrate.get_block_hash(block_id=7133632)
    extrinsics = subtensor.substrate.get_extrinsics(block_hash=block_hash)
    subnet_infos = subtensor.all_subnets()
    owner_coldkeys = [subnet_info.owner_coldkey for subnet_info in subnet_infos]
    for ex in extrinsics:
        call = ex.value.get('call', {})
        if (
            call.get('call_module') == 'SubtensorModule' and
            call.get('call_function') == 'set_subnet_identity'
        ):
            # Get the new coldkey from call_args
            address = ex.value.get('address', None)
            subnet_id = owner_coldkeys.index(address)
            # To get the old identity, use the current subnet identity from subnet_infos[subnet_id].
            # To get the new identity, get from call_args['subnet_name'].
            old_identity = subnet_infos[subnet_id].subnet_name
            call_args = call.get('call_args', [])
            new_identity = next((a['value'] for a in call_args if a['name'] == 'subnet_name'), None)
            print(f"Subnet {subnet_id} changing identity from '{old_identity}' to '{new_identity}'")