



def get_from_dict(d, key_list):
    """ 
        Go deeper into the dictionary layer by layer 
        and return the value of the key or None
    """
    if not d:
        return None

    d_inner = d
    for key in key_list:
        d_inner = d_inner.get(key)
        if d_inner is None:
            return None

    return d_inner