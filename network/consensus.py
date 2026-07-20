from enum import Enum

class ForkResolution(Enum):
    ADOPTED = "adopted"
    REJECTED_INVALID = "rejected_invalid"
    REJECTED_SHORTER = "rejected_shorter_or_equal"

def resolve_fork(lib,local_chain,new_chain):
    if not new_chain or not lib.is_chain_valid(new_chain):
        return ForkResolution.REJECTED_INVALID, None,None
    
    local_len = lib.get_chain_length(local_chain)
    received_len = lib.get_chain_length(new_chain)

    if received_len > local_len:
        return ForkResolution.ADOPTED, local_len,received_len
    
    return ForkResolution.REJECTED_SHORTER, local_len, received_len
