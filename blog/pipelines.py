# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import os
import re
import uuid

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from os import path

from scrapy.utils.serialize import ScrapyJSONEncoder


class BlogPipeline:
    dir = "data"

    def open_spider(self, spider):
        if not path.exists(self.dir):
            os.makedirs(path.curdir + "/" + self.dir)

    def get_file_dir(self, item):
        return f'{path.curdir}/{self.dir}/{item["sourceType"]}/{item["author"]}'

    def process_item(self, item, spider):
        pdir = self.get_file_dir(item)

        filepath = f"{pdir}/{item['title']}.json"
        # 已经有了则返回
        if path.exists(filepath):
            return item

        if not path.exists(pdir):
            os.makedirs(pdir)

        with open(filepath, "w+", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False, indent=2, cls=ScrapyJSONEncoder)
        return item
