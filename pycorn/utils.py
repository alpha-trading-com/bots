import string
import itertools
import random


id_cycle = itertools.count(1)
rng = random.Random()
def get_next_id() -> str:
    """
    Generates a pseudo-random ID by returning the next int of a range from 1-998 prepended with
    two random ascii characters.
    """
    random_letters = "".join(rng.choices(string.ascii_letters, k=2))
    return f"{random_letters}{next(id_cycle)}"
