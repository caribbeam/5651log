def tc_kontrol(tc):
    """TC Kimlik algoritması kontrolü"""
    if not tc or len(tc) != 11 or not tc.isdigit() or tc[0] == '0':
        return False
    d = [int(x) for x in tc]
    if (sum(d[:10]) % 10 != d[10]):
        return False
    if (((sum(d[0:10:2]) * 7) - sum(d[1:9:2])) % 10 != d[9]):
        return False
    return True 