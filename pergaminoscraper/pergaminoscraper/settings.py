# Scrapy settings for pergaminoscraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
# Or you can copy and paste them from where they're defined in Scrapy:
#
#     scrapy/conf/default_settings.py
#

import os.path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


BOT_NAME = 'pergaminoscraper'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['pergaminoscraper.spiders']
DEFAULT_ITEM_CLASS = 'pergaminoscraper.items.CompraItem'
#USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)
USER_AGENT = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/534.2 (KHTML, like Gecko) Chrome/6.0.453.1 Safari/534.2'
DEFAULT_REQUEST_HEADERS = {'Accept-Language':'es'}

#ITEM_PIPELINES = ['pergaminoscraper.pipelines.ItemCounterPipeline', 'pergaminoscraper.pipelines.ComprasPersisterPipeline']
ITEM_PIPELINES = ['pergaminoscraper.pipelines.ComprasPersisterPipeline']

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pergaminoweb.settings')

SCHEDULER_MIDDLEWARES = {
    'scrapy.contrib.schedulermiddleware.duplicatesfilter.DuplicatesFilterMiddleware': None,
}

RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_DELAY = 1

LOG_LEVEL = 'DEBUG'
