import re

import scrapy
from scrapy_redis.spiders import RedisSpider
from blog.items import BlogItem
from blog.util import getOrDefault, stop_char_re, parse_xpath
from blog.utils.snowflake import IdWorker





def getSource():
    return "cnblog"


class CnblogSpider(RedisSpider):
    name = 'cnblog'

    allowed_domains = ['cnblogs.com']

    redis_key = f'blog:{name}:start_urls'

    target_url_pattern = re.compile(r'https://www.cnblogs.com/\w+/p/\d+\.html')

    author_url_patterns = re.compile(r'https://www.cnblogs.com/\w+')

    author_xpath_patterns = ['//div[@class="post-item-foot"]/a/@href']

    next_page_patterns = ['//div[@class="pager"]/a/@href','//div[@class="nav_next_page"]/a/@href']

    items_url_patterns = ['//div[@class="post-item-text"]/a/@href', '//div[@class="postTitle"]/a/@href']

    list_url_suffix = '/default.html?page=1'

    title_xpath = ["//h1[@class='postTitle']//span/text()", "//span[@role='heading']/text()"]

    # category_xpath = "//div[@class='article-category']"

    tag_xpath = []

    content_xpath = ["//div[@id='cnblogs_post_body']/*"]

    author_xpath = ["//a[@id='Header1_HeaderTitle']/text()", "//div[@class='articleSuffix-right']//a/text()"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.worker = IdWorker(1, 1, 0)

    def parse(self, response):
        # 解析符合条件的数据
        if self.target_url_pattern.match(response.url):
            item = BlogItem()
            item['title'] = stop_char_re.sub('-', getOrDefault(parse_xpath(response, self.title_xpath).get(),
                                                               f"未知标题#{self.worker.next()}"))
            item['author'] = stop_char_re.sub('-', getOrDefault(parse_xpath(response, self.author_xpath).get(),
                                                                f"未知作者#{self.worker.next()}"))
            item['content_format'] = ''.join(parse_xpath(response, self.content_xpath).getall())
            item['source_type'] = getOrDefault(getSource(), f"未知来源#{self.worker.next()}")
            item['description'] = "Hello,World!"
            item['source_url'] = response.url
            item['tags'] = "外站文章,博客园"

            yield item
        # 获取作者
        for author_xpath_pattern in self.author_xpath_patterns:
            for url in response.xpath(author_xpath_pattern).getall():
                # 如果提取的url符合要求
                if self.author_url_patterns.match(url):
                    yield scrapy.Request(url=url + self.list_url_suffix, callback=self.parse, priority=10)
        # 翻页
        for next_page_pattern in self.next_page_patterns:
            for page in response.xpath(next_page_pattern).getall():
                yield scrapy.Request(url=response.urljoin(page), callback=self.parse, priority=5)

        # 获取文章url
        for item_url_pattern in self.items_url_patterns:
            for url in response.xpath(item_url_pattern).getall():
                yield scrapy.Request(url=url, callback=self.parse, priority=1)
