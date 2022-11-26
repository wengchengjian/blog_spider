import re

stop_char_re = re.compile(r'[*\/:?"<>|]')


def getOrDefault(val, defaultValue):
    return val if val is not None else defaultValue



def parse_xpath(response, xpaths):
    if xpaths is not None and len(xpaths) != 0:
        for xpath in xpaths:
            res = response.xpath(xpath)
            if res is not None:
                return res
        raise Exception("Could not parse xpath: %s" % xpath)
    else:
        raise Exception("xpaths must not be empty")