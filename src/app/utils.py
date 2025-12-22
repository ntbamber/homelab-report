#Human readable byte size
def human_bytes(n: int) -> str:
    units = ["B","KB","MB","GB","TB","PB"]
    s = 0
    f = float(n)
    while f >= 1024 and s < len(units)-1:
        f /= 1024.0
        s += 1
    return f"{f:.2f} {units[s]}"
