# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from sqlalchemy.dialects.mssql import TINYINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker

# 生成基类 所有表构建的类都是基类之上的 继承这个基类
Base = declarative_base()


class BlogItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    content_format = scrapy.Field()
    tags = scrapy.Field()
    source_type = scrapy.Field()
    source_url = scrapy.Field()
    description = scrapy.Field()


class Article(Base):
    __tablename__ = 'article'  # 表名
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    content_format = Column(String)
    reprint = Column(TINYINT)
    tags = Column(String)
    source_type = Column(TINYINT)
    source_url = Column(String)
    description = Column(String)
    publish = Column(TINYINT)
    create_by = Column(String)
    update_by = Column(String)

    def __hash__(self):
        return hash(self.title)

    def __eq__(self, other):
        return True if self == other or self.title == other.title else False


