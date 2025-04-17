import bittensor as bt

subtensor = bt.subtensor('local')

netuid = 81

prev_adjustment_block = subtensor.query_map_subtensor(name='LastAdjustmentBlock',params=(),block=subtensor.block)[netuid][1].value
now_adjustment_block = prev_adjustment_block + 360 + 1
current_block = subtensor.block

print(now_adjustment_block)
print((now_adjustment_block - 5310699) % 360)

