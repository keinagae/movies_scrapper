# Scrapy settings for movies_scrapper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from scrapy.utils.reactor import install_reactor

BOT_NAME = 'movies_scrapper'

SPIDER_MODULES = ['movies_scrapper.spiders']
NEWSPIDER_MODULE = 'movies_scrapper.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'movies_scrapper (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 30

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#     # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#     # 'Accept-Language': 'en',
#     'Cookie': 'PHPSESSID=9ts0udburo7801t0q07kobvu9e; CUID=N,1612435690061:ALHGLuQAAAAPTiwxNjEyNDM1NjkwMDYxwl7OM62GK8gCTrOheeOOKVhyk50IT6oC/Ss9MyXn39SOy+M+4htNkpFybldArzYhKfCcQSfvJ3j9aSpBChFMnoOWGGfT1Zbf4SNXEnLgW7fd5Cd3qJIHmOyPhBKk8CZZjYYBXJr6akvFQdkteLpuQYDiqoQnDwjlJjW8FBwbelZlgcJk3uj5rkh9cYKZ3+HKJZ/VlMXF/VmlNtaeVNhvFU4NtfHN+FKG2nwuoPIuqWBhwyuuQ5vsMFItBjr3XW3WDGO21USOBtBaQgmxOmbALzYMsFrc930vCO3OYZygWXgysqS1RU6nwrbr8uosHpmgs51CE/B2Zj/OtPTk/c2YSQ==',
#     'x-csrf-token': '$2y$10$7EeYSlFbTPlKTHCeKxRdCO2Tc9tAUtAkcY3v9muw4EGsHYrvOBklS'
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'movies_scrapper.middlewares.MoviesScrapperSpiderMiddleware': 543,
# }


# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'movies_scrapper.middlewares.MoviesScrapperDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   # 'movies_scrapper.pipelines.MoviesScrapperPipeline': 300,
   'movies_scrapper.pipelines.IMDBIdScrapperPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 3.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = True

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 300
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# async

TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
import asyncio

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')

# Logs level
LOG_LEVEL = 'ERROR'
