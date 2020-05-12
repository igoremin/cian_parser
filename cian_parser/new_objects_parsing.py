from .models import MapParserDetails, ObjectInfoDetails, Status, TargetValue, ProxyFile
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from seleniumwire import webdriver
from bs4 import BeautifulSoup
from threading import Thread
import unicodedata
import random
import time
import requests
import re


class Bot(Thread):
    MEDIA_DIR = settings.MEDIA_DIR

    def __init__(self, proxy_class, price_class):
        """Создаем экземпляр бота"""
        Thread.__init__(self)

        if settings.DEBUG:
            print('CREATE BOT')

        self.proxies = proxy_class
        self.price = price_class

        self.no_proxy = False

        self.use_proxy = 1

        if self.use_proxy == 2:
            self.proxy = ''
        else:
            self.proxy, clean_proxy = self.proxies.get_new_proxy()

        """Подключаем настройки прокси к экземпляру бота"""
        options = {
            'proxy': self.proxy
        }

        wind_width = random.randint(1000, 1920)
        wind_height = random.randint(750, 1080)

        with open(f'{settings.MEDIA_DIR}/user-agents/user_agents_for_chrome_pk.txt', 'r', encoding='utf-8') as f:
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
        if self.use_proxy == 1:
            self.driver = webdriver.Chrome(
                options=self.options,
                executable_path=f'{settings.MEDIA_DIR}/drivers/chromedriver',
                seleniumwire_options=options,
            )
        else:
            self.driver = webdriver.Chrome(
                options=self.options,
                executable_path=f'{settings.MEDIA_DIR}/drivers/chromedriver',
            )

        """Создаем необходимые переменные для работы"""
        self.reboot = False
        self.search_status = False
        self.step = 0
        self.target = []

    def run(self):
        if settings.DEBUG:
            print('START BOT')
        self.get_new_price()

    def reload_bot(self):
        """Clear the cookies and cache for the ChromeDriver instance."""
        self.driver.quit()

        wind_width = random.randint(1000, 1920)
        wind_height = random.randint(750, 1080)

        self.options.add_argument(f'window-size={wind_width},{wind_height}')

        self.proxy, clean_proxy = self.proxies.get_new_proxy()
        options = {
            'proxy': self.proxy
        }

        self.driver = webdriver.Chrome(
            options=self.options,
            executable_path=f'{settings.MEDIA_DIR}/drivers/chromedriver',
            seleniumwire_options=options,
        )

        self.step = 0

    def get_new_price(self):
        # Получаем новый диапазон цен для поиска объектов по картам
        while True:
            new_price = self.price.get_new_value()
            if new_price is False:
                # Цен больше нет, останавливаем цикл
                break
            else:
                # Если диапазон существует тогда находим объекты на картах которые соответсвуют запросу
                self.target = get_json(new_price, self.proxies)
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

            try:
                page_data = ObjectInfoDetails.objects.get(cain_id=int(data['pk']))
            except ObjectDoesNotExist:
                if settings.DEBUG:
                    print(f"PARSING URL : {data['url']}")
                # Если этот урл еще не парсили, начинаем парсинг
                url = data['url']
                # Меняем прокси если количество запросов больше цели
                if self.use_proxy == 1 and self.step == 20:
                    self.reload_bot()

                k = 0
                while k < 10:
                    # Получаем суп страницы через selenium
                    soup = self.get_page(url)
                    if soup:
                        # Суп взят, берем из него нужные данные
                        self.get_data_from_page(soup, url)
                        break
                    else:
                        k += 1
            except Exception as err:
                print(f"ERROR FIND OBJECT WITH ID {data['pk']} , ERROR : {err}")
            else:
                new_price = ''.join(re.findall(r'\d+', data['price']))
                if int(new_price) != int(page_data.price):
                    new_price_for_m = int(int(new_price) / int(''.join(re.findall(r'\d+', data['p']))))
                    if settings.DEBUG:
                        print(f'CHANGE PRICE. OLD PRICE : {page_data.price}, NEW PRICE : {new_price}, '
                              f'OLD M PRICE : {page_data.price_for_m}, NEW M PRICE : {new_price_for_m}, '
                              f'URL : {page_data.url}')

                    page_data.price = int(new_price)
                    page_data.price_for_m = new_price_for_m
                    page_data.save()

    def get_data_from_page(self, soup, url):
        try:
            # Проверка не снято ли объявление
            check = soup.find('div', {'data-name': 'OfferUnpublished'})
            check_status = True
            if check:
                check_status = False

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

            try:
                new_object = ObjectInfoDetails(
                    title=name, phones=phone, is_active=check_status, jk_name=parent_text, address=address_text,
                    time_to_the_subway=time_text, price=price_text, price_for_m=price_for_m_text,
                    params=all_params, description=description_text, photos=rez_all_images, url=url,
                    cain_id=int(str(url).split('/')[-1])
                )
                new_object.save()
            except Exception as err:
                print(f"ERROR WITH CREATE NEW OBJECT. URL : {url}, ERROR : {err}")
            self.step += 1
        except Exception as err:
            print(f'ERROR WITH GET DATA FROM PAGE : {err}')
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
    with open(f'{settings.MEDIA_DIR}/user-agents/user_agents_for_chrome_pk.txt') as u_a:
        user_agent = random.choice([row.strip() for row in u_a.readlines()])
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                  'q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'ru,ru-RU;q=0.9,kk-RU;q=0.8,kk;q=0.7,uz-RU;q=0.6,uz;q=0.5,en-RU;q=0.4,en-US;q=0.3,en;q=0.2',
        'connection': '0',
        'origin': 'https://www.cian.ru',
        'cache-control': 'max-age=0',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-Agent': user_agent
    }
    return headers


def get_json(price, proxy_class):

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
                try:
                    new_map_object = MapParserDetails(
                        title=values['title'],
                        price=values['price'],
                        area=values['p'],
                        floor=values['floor'],
                        address=values['address'],
                        url=values['url'],
                        object_id=values['pk']
                    )
                    new_map_object.save()
                except Exception as err:
                    print(f'ERROR WITH WRITE NEW MAP OBJECT : {err}')
                    pass

    min_price = price[0]
    max_price = price[1]
    all_results = []
    url = f'https://www.cian.ru/ajax/map/roundabout/?engine_version=2&deal_type=sale&offer_type=flat&region=1&' \
          f'in_polygon[0]=55.566274_37.137084,55.566274_37.954192,55.912587_37.954192,55.912587_37.137084&' \
          f'minprice={min_price}&maxprice={max_price}'
    data = json_request(url, proxy_class)
    if data is not False:
        if 300 < int(data['data']['offers_count']) <= 1500:
            add_data(data)
            for p in [2, 3, 4, 5]:
                new_url_p = f'{url}&p={p}'
                new_data = json_request(new_url_p, proxy_class)
                if new_data is not False and int(len(new_data['data']['points'])) > 0:
                    add_data(data)
                else:
                    break
        elif 0 < int(data['data']['offers_count']) <= 300:
            add_data(data)
        elif int(len(data['data']['points'])) == 0 or int(data['data']['offers_count']) == 0:
            pass
        elif int(data['data']['offers_count']) > 1500:
            for rm in ['room1=1', 'room2=1', 'room3=1', 'room4=1', 'room5=1', 'room6=1', 'room9=1']:
                new_url = f'{url}&{rm}'
                # print(new_url)
                for p in [1, 2, 3, 4, 5]:
                    new_url_p = f'{new_url}&p={p}'
                    new_data = json_request(new_url_p, proxy_class)
                    if new_data is not False and int(len(new_data['data']['points'])) > 0:
                        add_data(data)
                    else:
                        break
        else:
            pass

        return all_results if len(all_results) > 0 else False


def json_request(url, proxies):
    k = 0
    while k < 10:
        try:
            request = requests.get(
                url=url,
                headers=get_headers(),
                proxies=proxies.get_new_proxy()[0]
            )
            if request.status_code == 200:
                if settings.DEBUG:
                    print('STATUS COD 200')
                data = request.json()
                return data
            else:
                if settings.DEBUG:
                    print('STATUS COD FALSE')
                k += 1
        except:
            k += 1
    return False


def get_target_value(proxies):
    if settings.DEBUG:
        print('GET TARGET VALUE')
    url = "https://www.cian.ru/ajax/map/roundabout/?engine_version=2&deal_type=sale&offer_type=flat&region=1&" \
          "in_polygon[0]=55.566274_37.137084,55.566274_37.954192,55.912587_37.954192,55.912587_37.137084&"
    data = json_request(url, proxies)
    if data is not False:
        if settings.DEBUG:
            print(f"TARGET VALUE {data['data']['offers_count']}")
        set_target_value(data['data']['offers_count'])


class AllPriseValues:
    def __init__(self):
        if settings.DEBUG:
            print('CREATE PRICE CLASS')
        self.all_price = [0, 2000000]
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


def clean_map_table():
    if settings.DEBUG:
        print('CLEAN MAP TABLE')
    MapParserDetails.objects.all().delete()


def get_all_id():
    all_cian_id = ObjectInfoDetails.objects.all().values_list('cain_id', flat=True)
    return all_cian_id


def set_target_value(new_value):
    TargetValue.objects.all().delete()
    new_target = TargetValue(
        target_value=int(new_value)
    )
    new_target.save()


def del_old_objects():
    all_map_id = MapParserDetails.objects.values_list('object_id', flat=True)

    for row in ObjectInfoDetails.objects.all():
        if row.cain_id not in all_map_id:
            row.delete()


class Proxy:
    def __init__(self):
        if settings.DEBUG:
            print('CREATE PROXY CLASS')
        self.proxy_file_path = ProxyFile.objects.all()[0].proxy_file.path
        with open(self.proxy_file_path, 'r', encoding='utf-8') as proxy_file:
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
                with open(self.proxy_file_path, 'r', encoding='utf-8') as proxy_file:
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


def start():
    clean_map_table()

    all_proxies = Proxy()
    all_price = AllPriseValues()

    get_target_value(all_proxies)

    threads = []

    for _ in range(4):
        thread = Bot(proxy_class=all_proxies, price_class=all_price)
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()

    status = Status.objects.all()[0]
    status.status = False
    status.save()

    del_old_objects()

