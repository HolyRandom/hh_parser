import requests
from bs4 import BeautifulSoup
from time import sleep
import sqlite3
from datetime import datetime
from fake_useragent import UserAgent
import re

URL = 'https://hh.ru/search/vacancy'
HEADERS = {'user-agent': UserAgent().random
           , 'accept': '*/*'}
pag_max = None
params = {'text': None,
          'page': '0'}

def get_html(url, params = None):
    """request url and get raw html"""
    req = requests.get(url, headers=HEADERS,  params=params)
    sleep(1)
    if req.status_code == 200:
        pass
    return parse(req.content)


def parse(html):
    """parse html in bs"""
    soup = BeautifulSoup(html, 'lxml')
    return soup


def clear_vacancy_url(url):
    return re.search(r'(hh.*\?)', url).group(0)[:-1]


def parse_main(soup):
    """parse  page with vacancies"""
    global c, params, now
    vacancies = soup.find_all(class_='vacancy-serp-item')
    for vacancy in vacancies:
        vacancy_url = vacancy.find('a').get('href')
        clear_url = clear_vacancy_url(vacancy_url)
        c.execute('''SELECT * FROM vacansies WHERE URL=?''', (clear_url,))
        exists = c.fetchall()
        if not exists:
            parsed = parse_vacancy(get_html(url=vacancy_url))
            vacancy = parsed[0]
            salary = parsed[1]
            company = parsed[2]
            location = parsed[3]
            c.execute('''INSERT INTO vacansies VALUES (?,?,?,?,?,?)''', (vacancy, salary, company, location, clear_url, now,))
            conn.commit()
        else:
            c.execute('''UPDATE vacansies SET last_update = ? WHERE URL = ?''', (now, clear_url,))
            conn.commit()
            vacancy_title = vacancy.find(class_='resume-search-item__name').find('a').text
            print(f'[Дубляж] {vacancy_title}')

def get_pag(soup):
    """Get maximum pagination page"""
    pag = soup.find_all('a', class_='HH-Pager-Control')[-2].text
    return pag

def parse_vacancy(soup):
    """parse vacancy page"""
    try:
        name = soup.find('h1').text
    except:
        name = 'None'
    try:
        company = soup.find(class_='vacancy-company-name-wrapper').find_all('span')[0].text
    except:
        company = 'None'
    try:
        location = soup.find_all(attrs={'data-qa': 'vacancy-view-raw-address'})[0].text
    except:
        location = 'None'
    try:
        salary = soup.find(class_='vacancy-salary').text
    except:
        salary = 'None'
    print(f'{name}, {salary}')
    return name, salary, company, location

def delete_old(now):
    c.execute('''SELECT * from vacansies''')
    data = c.fetchall()
    for row in data:
        if now > row[-1]:
            c.execute('''DELETE FROM vacansies WHERE URL = ?''', (row[-2],))
            conn.commit()
            print(f'Вакансия {row[0]} - удалена')

if params['text'] == None:
    vacancy_name = input('Какую вакансию искать?\n')
    params['text'] = vacancy_name

conn = sqlite3.connect('example.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS vacansies (vacancy text, Salary text, Company text, Location text, URL text  PRIMARY KEY, last_update timestamp)''')

now = datetime.now()
html = get_html(URL, params=params)
pag_max = int(get_pag(html))
for page in range(pag_max):
    print("-"*10, page + 1, "-"*10)
    params['page'] = str(page)
    parse_main(get_html(URL, params=params))

delete_old(now)