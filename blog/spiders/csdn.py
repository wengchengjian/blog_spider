import scrapy
import re

from blog.items import BlogItem
from scrapy_redis.spiders import RedisSpider

from blog.util import stop_char_re, getOrDefault, parse_xpath


def getSource():
    return "csdn"


class CsdnBlogSpider(RedisSpider):
    name = "csdn"

    target_url_pattern = re.compile(r'https://blog.csdn.net/\w+/article/details/\d+')

    author_url_patterns = re.compile(r'https://blog.csdn.net/\w+')

    author_xpath_patterns = ['//div[@class="operation-c"]/a/@href', '//div[@class="profile-intro-name-boxTop"]/a/@href',
                             '//div[contains(@class,"info-box")]/div[@class="info"]/a/@href']
    next_page_patterns = ['//li[contains(@class,"ui-pager")]/@data-page']

    items_url_patterns = ['//div[contains(@class,"article-item-box")]/h4/a/@href']

    list_url_suffix = '/article/list'

    title_xpath = ["//div[@class='article-title-box']/h1/text()"]

    # category_xpath = "//div[@class='article-category']"

    tag_xpath = ["//div[contains(@class,'tags-box')]/a/text()"]

    content_xpath = ["//div[@id='content_views']/*"]

    author_xpath = ["//div[@class='profile-intro-name-boxTop']/a/span/text()"]

    redis_key = f"data:{name}:start_urls"

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
            item['tags'] = "外站文章,博客园" + ",".join(parse_xpath(response, self.tag_xpath).getall())
            yield item
        # 获取作者
        for author_xpath_pattern in self.author_xpath_patterns:
            for url in response.xpath(author_xpath_pattern).getall():
                # 如果提取的url符合要求
                if self.author_url_patterns.match(url):
                    yield scrapy.Request(url=url + self.list_url_suffix, callback=self.parse, priority=1)
        # 翻页
        for next_page_pattern in self.next_page_patterns:
            for page in response.xpath(next_page_pattern).getall():
                yield scrapy.Request(url=response.urljoin(page), callback=self.parse, priority=5)

        # 获取文章url
        for item_url_pattern in self.items_url_patterns:
            for url in response.xpath(item_url_pattern).getall():
                yield scrapy.Request(url=url, callback=self.parse, priority=10)
