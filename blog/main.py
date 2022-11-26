import re
import sys

from scrapy import cmdline

if __name__ == '__main__':
    cmdline.execute("scrapy crawl cnblog".split())

