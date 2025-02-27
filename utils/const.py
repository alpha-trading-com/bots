VALIDATOR_NAME = {
    "Rizzo" : "5F2CsUDVbRbVMXTh9fAzF9GacjVX7UapvRxidrxe7z8BYckQ",
    "RoundTable" : "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v",
    "Taostats" : "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1",
    "Opentensor" : "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3",
    "Yuma" : "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2",
    "tao5" : "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp",
    "WebGenieAI" : "5FcHYtdLLYSWUKbDgbZvvmCLRbnqwn3HUsWUAEmdQscW9dRW"
}

# Mapping of netuid to validator addresses
NETUID_TO_ADDRESS = {
    # focus sn valis
    4: VALIDATOR_NAME["Rizzo"],
    51: VALIDATOR_NAME["RoundTable"],
    48: VALIDATOR_NAME["Opentensor"],
    16: VALIDATOR_NAME["Opentensor"],
    
    # other valis
    8: VALIDATOR_NAME["Opentensor"],
    64: VALIDATOR_NAME["Rizzo"],
    41: VALIDATOR_NAME["Opentensor"],
    19: VALIDATOR_NAME["Opentensor"],
    11: VALIDATOR_NAME["RoundTable"],
    13: VALIDATOR_NAME["Opentensor"],
    9: VALIDATOR_NAME["Opentensor"],
    53: VALIDATOR_NAME["Opentensor"],
    54: VALIDATOR_NAME["WebGenieAI"],
    50: VALIDATOR_NAME["RoundTable"],
    
    # poor sn valis
    65: VALIDATOR_NAME["tao5"],
    66: VALIDATOR_NAME["Yuma"],
    67: VALIDATOR_NAME["Yuma"],
    68: VALIDATOR_NAME["Yuma"],
    69: VALIDATOR_NAME["Yuma"],
}


def sn_vali_addr(netuid: int) -> str:
    return NETUID_TO_ADDRESS.get(netuid, VALIDATOR_NAME["RoundTable"])
