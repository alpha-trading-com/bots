VALIDATOR_NAME = {
    "Rizzo" : "5F2CsUDVbRbVMXTh9fAzF9GacjVX7UapvRxidrxe7z8BYckQ",
    "RoundTable" : "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v",
    "Taostats" : "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1",
    "Opentensor" : "5F4tQyWrhfGVcNhoqeiNsR6KjD4wMZ2kfhLj4oHYuyHbZAc3",
    "Yuma" : "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2",
    "tao5" : "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp",
    "CrucibleLabs" : "5HYk8DMKWK8TJyPzZJ9vmZk7B5NPCgjnZoyZ1ZsB54RXdN47",
    "MinersUnionValidator" : "5DQ2Geab6G25wiZ4jGH6wJM8fekrm1QhV9hrRuntjBVxxKZm",
    "BittensorGuru" : "5HK5tp6t2S59DywmHRWPBVJeJ86T61KjurYqeooqj8sREpeN",
    "TensorplexLabs" : "5E4z3h9yVhmQyCFWNbY9BPpwhx4xFiPwq3eeqmBgVF6KULde",
    "TaoValidator" : "5Fy3MjrdKRvUWSuJa4Yd5dmBYunzKNmXnLcvP22NfaTvhQCY",
    "Polychain" : "5FxcZraZACr4L78jWkcYe3FHdiwiAUzrKLVtsSwkvFobBKqq",
    "Unit410" : "5CBDhkBxf3u7rSZqbcBW59NCpGbCsZSDFBgToEc4owqk8S3A",
    "AryvanderTouw" : "5CVS9d1NcQyWKUyadLevwGxg6LgBcF9Lik6NSnbe5q59jwhE",
    "ReadyAIValidator" : "5GQyFzvtVMw9X45t6dvUFgR9unFpDCccPPCiAoqJrtPuC8my",
    "Microcosmos" : "5Cg5QgjMfRqBC6bh8X4PDbQi7UzVRn9eyWXsB8gkyfppFPPy",
    "Love" : "5F27Eqz2PhyMtGMEce898x31DokNqRVxkm5AhDDe6rDGNvoY",
    "Tatsu" : "5D4gEn5S422dTGR5NJJKZ93FNV6hDmfwDPfxFNgcoVnUkZ4f",
    "Datura" : "5GP7c3fFazW9GXK8Up3qgu2DJBk8inu4aK9TZy3RuoSWVCMi",
    "WebGenieAI" : "5CiPKkqrBuuuapd3sKQQ8MhvaXSyGXaw4b2g9AKQp6V5iVvm",
    "51": "5E1nK3myeWNWrmffVaH76f2mCFCbe9VcHGwgkfdcD7k3E8D1",
    "NovaOwner" : "5F1tQr8K2VfBr2pG5MpAQf62n5xSAsjuCZheQUy82csaPavg",
    "TAO.com" : "5FKz1PAcB1y5vn3aGqNog2vyxagrKMjbkMRpdjY9cuXAG6pD"
}

# Mapping of netuid to validator addresses
NETUID_TO_ADDRESS = {
    # focus sn valis
    4: VALIDATOR_NAME["tao5"],
    51: VALIDATOR_NAME["51"],
    48: VALIDATOR_NAME["Opentensor"],
    16: VALIDATOR_NAME["Opentensor"],
    34: VALIDATOR_NAME["tao5"],
    64: VALIDATOR_NAME["tao5"],
    13: VALIDATOR_NAME["CrucibleLabs"],
    
    # other valis
    8: VALIDATOR_NAME["CrucibleLabs"],
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
    68: VALIDATOR_NAME["NovaOwner"],
    69: VALIDATOR_NAME["Yuma"],
    76: VALIDATOR_NAME["RoundTable"],
    81: VALIDATOR_NAME["TAO.com"],
}

def sn_vali_addr(netuid: int) -> str:
    return NETUID_TO_ADDRESS.get(netuid, VALIDATOR_NAME["RoundTable"])
