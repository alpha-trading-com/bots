import bittensor as bt

sub = bt.subtensor('finney')
meta = sub.metagraph(81)
print(meta.last_step + meta.tempo)