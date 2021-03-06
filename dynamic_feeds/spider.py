from splinter import Browser
import numpy as np
import utils
from dynamic_feeds.scraper_deltas import scraper_deltas
from dynamic_feeds.rss_deltas import rss_deltas
from bs4 import BeautifulSoup
import newspaper
import feedparser
from fnmatch import fnmatch
from newspaper import Article
from datetime import datetime, timedelta
import sys, traceback

class Spider:
    def __init__(self, options):
        try:
            self.browser = Browser('firefox', headless=True, incognito=True, capabilities={'acceptSslCerts': True, 'javascriptEnabled': True, })
            # self.browser = Browser('firefox')
        except Exception as e:
            print(e)
            print(f'Failed to initialize browser for Spider {self}, is something wrong with the binary?')
        self.options = options
        print(f'Spider {self} initialized at {datetime.now()}')

    def crawl_rss(self, sym, aggregate_data):
        for source in rss_deltas:
            try:
                rss_feed = rss_deltas[source]
                for entry in feedparser.parse(rss_feed).entries:
                    print(entry.published_parsed)
                    print(entry.link)

                    self.process_link(entry.link, 'links_rss', sym, aggregate_data)

                    # if not entry.link in aggregate_data[symbol]:
                    #     article = Article(entry.link)
                    #     article_count += 1
                    #     article.download()
                    #     article.parse()
                    #     if ((datetime.today() - timedelta(days=ARTICLE_EXPIRATION_TIMEDELTA)).date()) <= article.publish_date.date():
                    #         self.aggregate_data[symbol][entry.link] = utils.analyze_text(article.text)
                    #         # print(aggregate_data)
                    #     print("\n")
                    # else:
                    #     print("DUPLICATE ARTICLE FOUND VIA RSS")


            except Exception as e:
                print(e)
                print("Moving on after failing to retrieve from RSS src:", source)
                continue
        return aggregate_data

    def crawl_direct(self, sym, aggregate_data):
        for source in scraper_deltas:
            try:
                info = scraper_deltas[source]
                print(f'\nSpider direct crawl from src: {source}')
                print('going to', info['url'].format(sym))
                self.browser.visit(info['url'].format(sym))
                soup = BeautifulSoup(self.browser.html, 'html.parser')

                link_containing_element = soup.find(class_=info['link_container_class']) if info['link_container_class'] != None else soup.find(id=info['link_container_id'])
                links = link_containing_element.find_all('a')
                print("links from ", info['url'].format(sym))
                for a in links:
                    if not a.get('href', None) == None and not utils.link_matches_blocklist(a['href'], info['blocked_url_fragments']):
                        # url = utils.ensure_full_url(a['href'])
                        self.process_link(utils.ensure_full_url(a['href'], info['url']), 'links_scrape', sym, aggregate_data)
                        print("scraped href=", utils.ensure_full_url(a['href'], info['url']))
            except Exception as e:
                print(e)
                traceback.print_exc(file=sys.stdout)
                print("Moving on after failing to retrieve from crawl src:", source)
                continue
        return aggregate_data

    def process_link(self, link, link_type, sym, aggregate_data):
        if not link in aggregate_data[sym]:
            article = Article(link)
            print("download article at link: ", link)
            article.download()
            article.parse()
            if article.publish_date == None:
                return
            elif ((datetime.today() - timedelta(days=self.options['ARTICLE_EXPIRATION_TIMEDELTA'])).date()) <= article.publish_date.date():
                aggregate_data[sym][link] = utils.analyze_text(article.text)
                aggregate_data['meta_'][link_type].append(link)
                print("agg data modded:", aggregate_data)
            print("\n")
        else:
            print("DUPLICATE ARTICLE FOUND @ url:", link)

    # def link_matches_blocklist(self, link, blocklist):
    #     for block in blocklist:
    #         if fnmatch(link, block): return True
    #     return False
