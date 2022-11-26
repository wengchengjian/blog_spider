# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import queue
import threading
import time
# useful for handling different item types with a single interface
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from blog.items import Article
from blog.utils.snowflake import IdWorker


def handle_error(session, failure):
    if failure:
        session.rollback()
        # 打印错误信息
        logging.error("execute sql failed, reason: %s", failure)


class BlogPipeline(object):

    def __init__(self,mysql_params):
        self.title_cache = set()
        self.q = queue.Queue(500)
        self.max_time = 5 * 60
        self.max_num = 100
        self.last_update_time = time.time()
        self.worker = IdWorker(1, 2, 0)
        self.engine = create_engine(f"mysql+pymysql://{mysql_params['user']}:{mysql_params['password']}@{mysql_params['host']}:{mysql_params['port']}/{mysql_params['db']}",
                                    encoding='utf-8',
                                    echo=False)
        title_result = self.engine.execute("select title from article")
        for title_rs in title_result.fetchall():
            self.title_cache.add(title_rs['title'])

    def open_spider(self, Spider):
        threading.Thread(target=self.do_insert, daemon=True).start()

    @classmethod
    def from_settings(cls, settings):
        """
                数据库建立连接
                :param settings: 配置参数
                :return: 实例化参数
                """
        mysql_params = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
        )
        # 返回实例化参数
        return cls(mysql_params)


    def is_expired(self):
        return time.time() > self.max_time + self.last_update_time

    def process_item(self, item, spider):
        if item["title"] not in self.title_cache:
            self.q.put(item)
            return item

    def do_insert(self):
        while True:
            if self.q.qsize() > self.max_num or self.is_expired():
                self.last_update_time = time.time()
                if not self.q.empty():
                    logging.info("满足条件,开始执行数据插入")
                    Session_class = sessionmaker(bind=self.engine)
                    session = Session_class()
                    try:
                        num = 0
                        articles = set()
                        local_title_cache = set()
                        while not self.q.empty() and num < self.max_num:
                            num += 1
                            item = self.q.get()
                            if item['title'] not in self.title_cache and item['title'] not in local_title_cache:
                                article = Article(id=self.worker.next(), title=item['title'], author=item['author'],
                                                  content_format=item['content_format'], reprint=1, tags=item['tags'],
                                                  source_type=item['source_type']
                                                  , source_url=item['source_url'], description=item['description'],
                                                  publish=0,
                                                  create_by="crawler", update_by="crawler")
                                local_title_cache.add(article.title)
                                articles.add(article)
                        if num != 0:
                            session.add_all(articles)
                            session.commit()
                            for item in local_title_cache:
                                self.title_cache.add(item)
                    except Exception as e:
                        handle_error(session, e)
                else:
                    logging.info("队列为空")
            # 休息一秒
            time.sleep(1)
