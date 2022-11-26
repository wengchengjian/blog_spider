import re

stop_char_re = re.compile(r'[*\/:?"<>|]')

def getOrDefault(val, defaultValue):
    return val if val is not None else defaultValue
