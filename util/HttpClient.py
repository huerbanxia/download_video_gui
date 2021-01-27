import configparser
import requests
import random
from bs4 import BeautifulSoup
import json


class HttpClient(object):

    def __init__(self, proxy_path='127.0.0.1:1080'):
        # 解析配置文件
        conf = configparser.ConfigParser()
        # 初始化请求session
        self.session = requests.session()
        # 设置简体
        self.session.cookies['mangabz_lang'] = '2'
        # 全局超时时间
        self.timeout = 30
        # 代理地址
        self.proxy_path = proxy_path
        # 代理对象
        self.proxies = {
            "http": "http://%(proxy)s/" % {'proxy': self.proxy_path},
            "https": "http://%(proxy)s/" % {'proxy': self.proxy_path}
        }
        self.user_agent_pc = [
            # 谷歌
            'Mozilla/5.0.html (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.html.2171.71 Safari/537.36',
            'Mozilla/5.0.html (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.html.1271.64 Safari/537.11',
            'Mozilla/5.0.html (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.html.648.133 Safari/534.16',
            # 火狐
            'Mozilla/5.0.html (Windows NT 6.1; WOW64; rv:34.0.html) Gecko/20100101 Firefox/34.0.html',
            'Mozilla/5.0.html (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
            # opera
            'Mozilla/5.0.html (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.html.2171.95 Safari/537.36 OPR/26.0.html.1656.60',
            # qq浏览器
            'Mozilla/5.0.html (compatible; MSIE 9.0.html; Windows NT 6.1; WOW64; Trident/5.0.html; SLCC2; .NET CLR 2.0.html.50727; .NET CLR 3.5.30729; .NET CLR 3.0.html.30729; Media Center PC 6.0.html; .NET4.0C; .NET4.0E; QQBrowser/7.0.html.3698.400)',
            # 搜狗浏览器
            'Mozilla/5.0.html (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.html.963.84 Safari/535.11 SE 2.X MetaSr 1.0.html',
            # 360浏览器
            'Mozilla/5.0.html (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.html.1599.101 Safari/537.36',
            'Mozilla/5.0.html (Windows NT 6.1; WOW64; Trident/7.0.html; rv:11.0.html) like Gecko',
            # uc浏览器
            'Mozilla/5.0.html (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.html.2125.122 UBrowser/4.0.html.3214.0.html Safari/537.36',
        ]

    def __get_random_headers(self):
        return {
            "User_Agent": random.choice(self.user_agent_pc),
            "Referer": "http://www.mangabz.com/"
        }

    # 使用同一会话发起请求方法
    def get(self, url: str, params=None, referer=None, is_proxies=False, timeout=None, stream=False):
        if params is None:
            params = {}
        headers = self.__get_random_headers()
        headers['Referer'] = referer
        if is_proxies:
            proxies = self.proxies
        else:
            proxies = {}
        if timeout is None:
            timeout = self.timeout
        return self.session.get(url, timeout=timeout, proxies=proxies, headers=headers, params=params, stream=stream)

    def reset(self):
        self.session.close()
        self.session = requests.session()
        # 设置简体
        self.session.cookies['mangabz_lang'] = '2'

    def get_html_format(self, url: str, params=None, referer=None, is_proxies=False, timeout=None):
        res = self.get(url, params, referer, is_proxies, timeout)
        soup = BeautifulSoup(res.content, "lxml")
        return soup

    def get_json(self, url: str, params=None, referer=None, is_proxies=False, timeout=None):
        res = self.get(url, params, referer, is_proxies, timeout)
        return json.loads(res.content)
