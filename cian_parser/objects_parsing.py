from seleniumwire import webdriver
from bs4 import BeautifulSoup
from threading import Thread
from sys import argv
import unicodedata
import random
import os
import time
import sqlite3
import signal
import threading
import requests
import re
import sys


signal.signal(signal.SIGCHLD, signal.SIG_IGN)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')

proxy_file_name = argv[1]


class Bot(Thread):
    def __init__(self):
        """Создаем экземпляр бота"""
        Thread.__init__(self)

        self.no_proxy = False

        if use_proxy == 2:
            self.proxy = ''
        else:
            self.proxy, clean_proxy = proxies.get_new_proxy()

        """Подключаем настройки прокси к экземпляру бота"""
        options = {
            'proxy': self.proxy
        }

        wind_width = random.randint(1000, 1920)
        wind_height = random.randint(750, 1080)

        with open(f'{MEDIA_DIR}/user-agents/user_agents_for_chrome_pk.txt', 'r', encoding='utf-8') as f:
            user_agent = random.choice([line.strip() for line in f])

        self.options = webdriver.ChromeOptions()
        self.options.add_argument("ignore-certificate-errors")
        self.options.add_argument(f'window-size={wind_width},{wind_height}')
        self.options.add_argument("--disable-blink-features")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--headless")
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--profile-directory=Default')

        """Добавялем юзер агент из списка"""
        self.options.add_argument(f"user-agent={user_agent}")

        """Создаем экземпляр браузера"""
        if use_proxy == 1:
            self.driver = webdriver.Chrome(
                options=self.options,
                executable_path=f'{MEDIA_DIR}/drivers/chromedriver',
                seleniumwire_options=options,
            )
        else:
            self.driver = webdriver.Chrome(
                options=self.options,
                executable_path=f'{MEDIA_DIR}/drivers/chromedriver',
            )

        """Создаем необходимые переменные для работы"""
        self.reboot = False
        self.search_status = False
        self.step = 0
        self.target = []

    def run(self):
        self.get_new_price()

    def reload_bot(self):
        """Clear the cookies and cache for the ChromeDriver instance."""
        self.driver.quit()

        wind_width = random.randint(1000, 1920)
        wind_height = random.randint(750, 1080)

        self.options.add_argument(f'window-size={wind_width},{wind_height}')

        self.proxy, clean_proxy = proxies.get_new_proxy()
        options = {
            'proxy': self.proxy
        }

        self.driver = webdriver.Chrome(
            options=self.options,
            executable_path=f'{MEDIA_DIR}/drivers/chromedriver',
            seleniumwire_options=options,
        )

        self.step = 0

    def get_new_price(self):
        # Получаем новый диапазон цен для поиска объектов по картам
        while True:
            new_price = price.get_new_value()
            if new_price is False:
                # Цен больше нет, останавливаем цикл
                break
            else:
                # Если диапазон существует тогда находим объекты на картах которые соответсвуют запросу
                self.target = get_json(new_price)
                if self.target:
                    # Объекты найдены, запускаем браузер для парсинга объектов
                    self.create_new_window()
        self.driver.quit()

    def create_new_window(self):
        while True:
            try:
                # Выполняем парсинг пока не закончатся урлы
                data = self.target.pop(0)
            except:
                break

            if data['url'] not in all_done_urls:
                # Если этот урл еще не парсили, начинаем парсинг
                url = data['url']
                # Меняем прокси если количество запросов больше цели
                if use_proxy == 1 and self.step == 20:
                    self.reload_bot()

                k = 0
                while k < 10:
                    # Получаем суп страницы через selenium
                    soup = self.get_page(url)
                    if soup:
                        # Суп взят, берем из него нужные данные
                        all_done_urls.add(url)
                        self.get_data_from_page(soup, url)
                        break
                    else:
                        k += 1
            else:
                # Урл уже парсили раньше, обновляем цену на объект если она менялась
                page_data = db.get_object(data['url'])
                if page_data is not None:
                    new_price = ''.join(re.findall(r'\d+', data['price']))
                    if int(new_price) != page_data[4]:
                        db.update_price(page_data[0], new_price)

    def get_data_from_page(self, soup, url):
        try:
            # Проверка не снято ли объявление
            check = soup.find('div', {'data-name': 'OfferUnpublished'})
            check_status = 'Активно'
            if check:
                check_status = 'Объявление снято с публикации'

            main_div = soup.find('section', {'data-name': 'Main'})

            name_h1 = main_div.find('h1', {'data-name': 'OfferTitle'})
            if name_h1:
                name = name_h1.text
            else:
                name = ''

            parent = main_div.find('div', {'data-name': 'Parent'})
            if parent:
                parent_text = parent.getText(strip=True)
            else:
                parent_text = ''

            geo = main_div.find('div', {'data-name': 'Geo'})
            address_text = ''
            time_text = ''
            if geo:
                address = geo.find('address')
                if address:
                    address_text = address.getText(strip=True).replace('На карте', '')

                all_time = geo.find_all('ul')
                if all_time:
                    for ul in all_time:
                        for li in ul:
                            time_text = time_text + li.getText(strip=True) + ' ; '

            price = soup.find('span', {'itemprop': 'price'})
            price_text = None
            if price:
                text_price = unicodedata.normalize("NFKD", price.getText(strip=True))
                price_text = ''.join(re.findall(r'\d+', text_price))

            price_for_m = soup.find(lambda x: x.name == 'div' and '--price_per_meter--' in ' '.join(x.get('class', [])))
            price_for_m_text = None
            if price_for_m:
                text_price_m = unicodedata.normalize("NFKD", price_for_m.text)
                price_for_m_text = ''.join(re.findall(r'\d+', text_price_m)[:-1])

            params = soup.select_one("div#description"). \
                find_all(lambda x: x.name == 'div' and '--info--' in ' '.join(x.get('class', [])))
            all_params = ''
            if params:
                for param in params:
                    param_value = param.find('div').text
                    param_text = param.find_all('div')[-1].text
                    all_params = all_params + unicodedata.normalize("NFKD", f"{param_text} : {param_value} ; ")

            description_t = soup.find('p', {'itemprop': 'description'})
            description_text = ''
            if description_t:
                description_text = description_t.text

            phone = ''
            phone_div = soup.find(lambda x: x.name == 'div' and '--print_phones--' in ' '.join(x.get('class', [])))
            if phone_div:
                phone = phone_div.getText(strip=True)

            all_images = self.driver.find_elements_by_css_selector('img.fotorama__img')
            rez_all_images = ''
            for image in all_images:
                rez_all_images = rez_all_images + f"{image.get_attribute('src')}; "

            data = {
                'Название': name,
                'Телефон': phone,
                'Статус': check_status,
                'ЖК': parent_text,
                'Адресс': address_text,
                'Время в пути': time_text,
                'Цена': price_text,
                'Цена за метр': price_for_m_text,
                'Параметры': all_params,
                'Описание': description_text,
                'Фотографии': rez_all_images,
                'URL': url,
            }
            db.object_insert(data)
            self.step += 1
        except:
            pass

    def get_page(self, url):
        # Загружаем страницу через selenium
        self.driver.get(url)
        time.sleep(random.uniform(0.5, 1.5))
        # Создаем суп из полученой страницы
        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        try:
            # Проверяем есть ли на старнице заголовок объявления
            main_div = soup.find('section', {'data-name': 'Main'})
            name = main_div.find('h1', {'data-name': 'OfferTitle'}).text
        except:
            # Заголовка нет, перезапускаем драйвер
            self.reload_bot()
            return False
        else:
            if 'error response' in soup.text.lower():
                self.reload_bot()
                return False
            elif name == '':
                self.reload_bot()
                return False
            else:
                # Заголовок объявления найден, возвращаем суп страницы
                return soup


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

    def add_data(results):
        for d in results['data']['points']:
            address = results['data']['points'][d]['content']['text']
            for obj in results['data']['points'][d]['offers']:
                url = str(re.findall(r'href="\S+"', obj['link_text'][4])[0]).replace(r'href="', '').replace(r'"', '')
                pk = url.split('/')[-1]
                values = {'title': obj['link_text'][0],
                          'price': obj['link_text'][2],
                          'p': obj['link_text'][1].replace('<sup>2</sup>', ''),
                          'floor': obj['link_text'][3],
                          'address': address,
                          'url': url,
                          'pk': pk}

                all_results.append(values)
                db.map_insert(values)

    min_price = price[0]
    max_price = price[1]
    all_results = []
    url = f'https://www.cian.ru/ajax/map/roundabout/?engine_version=2&deal_type=sale&offer_type=flat&region=1&' \
          f'in_polygon[0]=55.566274_37.137084,55.566274_37.954192,55.912587_37.954192,55.912587_37.137084&' \
          f'minprice={min_price}&maxprice={max_price}'
    # request = requests.get(
    #     url=url,
    #     headers=get_headers(),
    #     proxies=proxies.get_new_proxy()[0]
    # )
    #
    # data = request.json()
    data = json_request(url)
    if data is not False:
        if 300 < int(data['data']['offers_count']) <= 1500:
            # print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , mod 1")
            add_data(data)
            for p in [2, 3, 4, 5]:
                new_url_p = f'{url}&p={p}'
                # print(new_url_p)
                # request = requests.get(
                #     url=new_url_p,
                #     headers=get_headers(),
                #     proxies=proxies.get_new_proxy()[0]
                # )
                # new_data = request.json()
                new_data = json_request(new_url_p)
                if new_data is not False and int(len(new_data['data']['points'])) > 0:
                    add_data(data)
                else:
                    break
        elif 0 < int(data['data']['offers_count']) <= 300:
            # print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , mod 2")
            add_data(data)
        elif int(len(data['data']['points'])) == 0 or int(data['data']['offers_count']) == 0:
            # print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']}, PASS")
            pass
        elif int(data['data']['offers_count']) > 1500:
            # print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , mod 3")
            for rm in ['room1=1', 'room2=1', 'room3=1', 'room4=1', 'room5=1', 'room6=1', 'room9=1']:
                new_url = f'{url}&{rm}'
                # print(new_url)
                for p in [1, 2, 3, 4, 5]:
                    new_url_p = f'{new_url}&p={p}'
                    # print(new_url_p)
                    # request = requests.get(
                    #     url=new_url_p,
                    #     headers=get_headers(),RELO
                    #     proxies=proxies.get_new_proxy()[0]
                    # )
                    # new_data = request.json()
                    new_data = json_request(new_url_p)
                    if new_data is not False and int(len(new_data['data']['points'])) > 0:
                        add_data(data)
                    else:
                        break
        else:
            # print(f"Min price : {min_price} , Max price : {max_price} , result : {data['data']['offers_count']} , BROKEN")
            pass

        return all_results if len(all_results) > 0 else False


def json_request(url):
    k = 0
    while k < 10:
        try:
            request = requests.get(
                url=url,
                headers=get_headers(),
                proxies=proxies.get_new_proxy()[0]
            )
            if request.status_code == 200:
                data = request.json()
                return data
            else:
                k += 1
        except:
            k += 1
    return False


def get_target_value():
    url = "https://www.cian.ru/ajax/map/roundabout/?engine_version=2&deal_type=sale&offer_type=flat&region=1&" \
          "in_polygon[0]=55.566274_37.137084,55.566274_37.954192,55.912587_37.954192,55.912587_37.137084&"
    data = json_request(url)
    if data is not False:
        db.set_target_value(data['data']['offers_count'])


class AllPriseValues:
    def __init__(self):
        self.all_price = [0, 2000000]
        # self.all_price = [1999999, 2000000]
        # for _ in range(0, 1):
        #     self.all_price.append(self.all_price[-1] + 50000)
        for _ in range(0, 800):
            self.all_price.append(self.all_price[-1] + 50000)

        for _ in range(0, 120):
            self.all_price.append(self.all_price[-1] + 500000)

        self.price_list = ([self.all_price[i-1] + 1, self.all_price[i]] for i in range(1, len(self.all_price)))

    def get_new_value(self):
        try:
            return next(self.price_list)
        except StopIteration:
            return False


class DataBase:
    def __init__(self):
        self.all_urls = []
        self.all_map_urls = []

        self.conn = sqlite3.connect(f'{BASE_DIR}/db.sqlite3', check_same_thread=False)
        self.c = self.conn.cursor()

    def object_insert(self, data):
        values = list(data.values())
        try:
            lock.acquire(True)
            self.c.execute(
                """INSERT INTO cian_parser_objectinfodetails (
                title, phones, is_active, jk_name, address, time_to_the_subway, price, price_for_m, params,
                description, photos, url
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);""", values
            )
            self.conn.commit()
        except Exception as err:
            print(err)
        finally:
            lock.release()

    def map_insert(self, data):
        values = list(data.values())
        try:
            lock.acquire(True)
            self.c.execute(
                """INSERT INTO cian_parser_mapparserdetails (
                title, price, area, floor, address, url, object_id
                ) VALUES (?,?,?,?,?,?,?)""", values
            )
            self.conn.commit()
        except Exception as err:
            print(err)
        finally:
            lock.release()

    def clean_map_table(self):
        try:
            lock.acquire(True)
            self.c.execute(
                """DELETE FROM cian_parser_mapparserdetails"""
            )
            self.conn.commit()
        except Exception as err:
            print(err)
        finally:
            lock.release()

    def get_all_urls(self):
        try:
            for row in self.c.execute("""SELECT url FROM cian_parser_objectinfodetails"""):
                self.all_urls.append(row[0])
            return self.all_urls
        except Exception as err:
            print(err)

    def get_all_map_urls(self):
        try:
            for row in self.c.execute("""SELECT url FROM cian_parser_mapparserdetails"""):
                self.all_map_urls.append(row[0])
            return self.all_map_urls
        except Exception as err:
            print(err)

    def get_all_data(self):
        try:
            for row in self.c.execute("""SELECT * FROM test_table"""):
                # print(row)
                new_row = [row[1], '', '', row[2], row[3], row[4], row[5], row[6], row[7], row[8], '', row[9]]
                print(new_row)

                # DataBase.insert(new_row)
        except Exception as err:
            print(err)

    def get_object(self, url):
        try:
            lock.acquire(True)
            self.c.execute("""SELECT * FROM cian_parser_objectinfodetails WHERE url='%s'""" % (url, ))
            data = self.c.fetchone()
            return data
        except Exception as err:
            print(err)
            return None
        finally:
            lock.release()

    def del_old_objects(self):
        try:
            lock.acquire(True)
            all_urls = tuple(self.get_all_map_urls())

            self.c.execute("""DELETE FROM cian_parser_objectinfodetails WHERE url NOT IN {}""".format(all_urls))
            self.conn.commit()
        except Exception as err:
            print(err)
        finally:
            lock.release()

    def update_price(self, pk, new_price):
        try:
            lock.acquire(True)
            self.c.execute("""UPDATE cian_parser_objectinfodetails SET price='%s' WHERE id='%s'""" % (new_price, pk))
            self.conn.commit()
        except Exception as err:
            print(err)
        finally:
            lock.release()

    def set_target_value(self, target):
        try:
            lock.acquire(True)
            self.c.execute("""DELETE FROM cian_parser_targetvalue""")
            self.conn.commit()
            self.c.execute("""INSERT INTO cian_parser_targetvalue (target_value) VALUES (?)""", (int(target), ))
            self.conn.commit()
        except Exception as err:
            print(err)
        finally:
            lock.release()

    def change_status(self):
        try:
            lock.acquire(True)
            self.c.execute("""UPDATE cian_parser_status SET status='False' WHERE id=(
            SELECT (id) FROM cian_parser_status ORDER BY id ASC LIMIT 1)""")
            self.conn.commit()
        except Exception as err:
            print(err)
        finally:
            lock.release()

    def close_db(self):
        self.c.close()


class Proxy:
    def __init__(self):
        with open(f'{MEDIA_DIR}/{proxy_file_name}', 'r', encoding='utf-8') as proxy_file:
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


lock = threading.Lock()     # Блокировка потоков

price = AllPriseValues()    # Создаем класс для получаения диапазона цен

db = DataBase()             # Создаем класс для управления базой
db.clean_map_table()        # Отчищаем таблицу карт

all_done_urls = set(db.get_all_urls())

proxies = Proxy()
use_proxy = 1

threads = []

get_target_value()

for _ in range(4):
    thread = Bot()
    thread.start()
    threads.append(thread)

for t in threads:
    t.join()

db.del_old_objects()
db.change_status()

db.close_db()

sys.exit()
