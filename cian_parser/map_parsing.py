import requests
import time
import random
import csv
import re
import os
import sqlite3
import concurrent.futures
import threading
import signal
from sys import argv


signal.signal(signal.SIGCHLD, signal.SIG_IGN)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')


def get_headers():
    with open(f'{MEDIA_DIR}/user-agents/user_agents_for_chrome_pk.txt') as u_a:
        user_agent = random.choice([row.strip() for row in u_a.readlines()])
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                  'q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'ru,ru-RU;q=0.9,kk-RU;q=0.8,kk;q=0.7,uz-RU;q=0.6,uz;q=0.5,en-RU;q=0.4,en-US;q=0.3,en;q=0.2',
        'connection': '0',
        'origin': 'https://www.cian.ru',
        # 'referer': 'https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=2&region=1',
        'cache-control': 'max-age=0',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-Agent': user_agent
    }
    return headers


def get_json(price):
    time.sleep(random.uniform(0.5, 1.5))
    min_price = price[0]
    max_price = price[1]
    url = f'https://www.cian.ru/ajax/map/roundabout/?engine_version=2&deal_type=sale&offer_type=flat&region=1&' \
          f'in_polygon[0]=55.566274_37.137084,55.566274_37.954192,55.912587_37.954192,55.912587_37.137084&' \
          f'minprice={min_price}&maxprice={max_price}'
    request = requests.get(
        url=url,
        headers=get_headers(),
        proxies=proxies.get_new_proxy()[0]
    )

    data = request.json()
    if 300 < int(data['data']['offers_count']) <= 1500:
        print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , mod 1")
        # read_json(data)
        db.insert(data)
        for p in [2, 3, 4, 5]:
            new_url_p = f'{url}&p={p}'
            print(new_url_p)
            request = requests.get(
                url=new_url_p,
                headers=get_headers(),
                proxies=proxies.get_new_proxy()[0]
            )
            new_data = request.json()
            if int(len(new_data['data']['points'])) > 0:
                # read_json(new_data)
                db.insert(data)
            else:
                break
    elif 0 < int(data['data']['offers_count']) <= 300:
        print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , mod 2")
        # read_json(data)
        db.insert(data)
    elif int(len(data['data']['points'])) == 0 or int(data['data']['offers_count']) == 0:
        print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']}, PASS")
        pass
    elif int(data['data']['offers_count']) > 1500:
        print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , mod 3")
        for rm in ['room1=1', 'room2=1', 'room3=1', 'room4=1', 'room5=1', 'room6=1', 'room9=1']:
            new_url = f'{url}&{rm}'
            print(new_url)
            for p in [1, 2, 3, 4, 5]:
                new_url_p = f'{new_url}&p={p}'
                print(new_url_p)
                request = requests.get(
                    url=new_url_p,
                    headers=get_headers(),
                    proxies=proxies.get_new_proxy()[0]
                )
                new_data = request.json()
                if int(len(new_data['data']['points'])) > 0:
                    # read_json(new_data)
                    db.insert(data)
                else:
                    break
    else:
        print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , BROKEN")


class Proxy:
    def __init__(self):
        with open(f'{MEDIA_DIR}/proxies/proxy.txt', 'r', encoding='utf-8') as proxy_file:
            all_proxies = [row.strip() for row in proxy_file.readlines()]
            self.proxies = sorted(all_proxies, key=lambda *args: random.random())

        self.block_proxies = []

    def get_new_proxy(self):
        new_proxy = False
        k = 0
        while new_proxy is False or k < len(self.proxies):
            new_proxy = self.proxies.pop(0).split(':')
            if new_proxy not in self.block_proxies:
                break
            else:
                new_proxy = False
                k += 1
        if new_proxy is not False:
            ip, port, login, password = new_proxy[0], new_proxy[1], new_proxy[2], new_proxy[3]

            proxy_setting = {
                "http": f"http://{login}:{password}@{ip}:{port}",
                "https": f"https://{login}:{password}@{ip}:{port}"
            }

            if len(self.proxies) < 1:
                with open(f'{MEDIA_DIR}/proxies/proxy.txt', 'r', encoding='utf-8') as proxy_file:
                    all_proxies = [row.strip() for row in proxy_file.readlines()]
                    not_block_proxies = []
                    for p in all_proxies:
                        if p not in self.block_proxies:
                            not_block_proxies.append(p)

                    self.proxies = sorted(not_block_proxies, key=lambda *args: random.random())

            return proxy_setting, new_proxy
        else:
            return False

    def add_block_proxy(self, block_proxy):
        self.block_proxies.append(f"{block_proxy[0]}:{block_proxy[1]}:{block_proxy[2]}:{block_proxy[3]}")
        print(self.block_proxies)


class DataBase:
    def __init__(self):
        self.all_urls = []

    @staticmethod
    def insert(data):
        for d in data['data']['points']:
            address = data['data']['points'][d]['content']['text']
            for obj in data['data']['points'][d]['offers']:
                url = str(re.findall(r'href="\S+"', obj['link_text'][4])[0]).replace(r'href="', '').replace(r'"', '')
                pk = url.split('/')[-1]
                values = [obj['link_text'][0], obj['link_text'][2], obj['link_text'][1].replace('<sup>2</sup>', ''),
                          obj['link_text'][3], address, url, pk, int(new_map_parser_id)]
                try:
                    lock.acquire(True)
                    c.execute(
                        """INSERT INTO cian_parser_mapparserdetails (
                        title, price, area, floor, address, url, object_id, parser_id
                        ) VALUES (?,?,?,?,?,?,?,?);""", values
                    )
                    conn.commit()
                except Exception as err:
                    print(err)
                finally:
                    lock.release()

    def get_all_urls(self):
        try:
            for row in c.execute("""SELECT url FROM results_table"""):
                self.all_urls.append(row[0])
            return self.all_urls
        except Exception as err:
            print(err)

    @staticmethod
    def get_all_data():
        try:
            for row in c.execute("""SELECT * FROM test_table"""):
                # print(row)
                new_row = [row[1], '', '', row[2], row[3], row[4], row[5], row[6], row[7], row[8], '', row[9]]
                print(new_row)

                DataBase.insert(new_row)
        except Exception as err:
            print(err)


def start():
    all_price = [0, 2000000]
    # for _ in range(0, 10):
    #     all_price.append(all_price[-1] + 50000)
    for _ in range(0, 800):
        all_price.append(all_price[-1] + 50000)

    for _ in range(0, 120):
        all_price.append(all_price[-1] + 500000)

    # with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    #     executor.map(get_json, ([all_price[i-1] + 1, all_price[i]] for i in range(1, len(all_price))))


proxies = Proxy()
fieldnames = ['Заголовок', 'Цена', 'Площадь', 'Этаж', 'Адрес', 'URL', 'PK']
new_map_parser_id = argv[1]
conn = sqlite3.connect(f'{BASE_DIR}/db.sqlite3', check_same_thread=False)
c = conn.cursor()
db = DataBase()

lock = threading.Lock()

start()

c.close()
