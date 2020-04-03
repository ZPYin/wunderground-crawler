import requests
import time
import openpyxl
import random
import datetime
from bs4 import BeautifulSoup
import json
import os


def get_headers():
    pc_headers = {
        "X-Forwarded-For": '%s.%s.%s.%s' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
    }
    return pc_headers


class NetWorkError(Exception):
    pass


def build_request(url, headers=None):
    if headers is None:
        headers = get_headers()
    for i in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            return response
        except Exception as e:
            continue
    raise NetWorkError


def write_to_excel(lines, filename, write_only=True):
    excel = openpyxl.Workbook(write_only=write_only)
    sheet = excel.create_sheet()
    for line in lines:
        sheet.append(line)
    excel.save(filename)


def get_next_date(current_date='2017-01-01'):
    current_date = datetime.datetime.strptime(current_date, '%Y-%m-%d')
    oneday = datetime.timedelta(days=1)
    next_date = current_date+oneday
    return str(next_date).split(' ')[0]


def create_url(latitude, longitude, start_date, end_date):
    url = 'https://api.weather.com/v1/geocode/{}/{}/observations/historical.json?apiKey=6532d6454b8aa370768e63d6ba5a832e&startDate={}&endDate={}&units=e'.format(
        latitude, longitude, start_date, end_date)
    return url


def get_json(url):
    req = build_request(url)
    html = BeautifulSoup(req.text, 'lxml')
    res_json = eval(html.find("p").get_text().replace('null', '"null"'))
    return res_json


def save_records(filename, res):
    with open(filename, 'a') as fh:
        for line in res:

            fh.write('{time:s} {temp} {dewPt} {rh} {pres} {wspd} {wdir} {uv_desc} {uv_index}\n'.format(
                time=datetime.datetime.utcfromtimestamp(line['valid_time_gmt']).strftime('%Y-%m-%d %H:%M'),
                temp=line['temp'],
                dewPt=line['dewPt'],
                rh=line['rh'],
                pres=line['pressure'],
                wspd=line['wspd'],
                wdir=line['wdir_cardinal'],
                uv_desc=line['uv_desc'],
                uv_index=line['uv_index']
            ))


def crawl(latitude, longitude, start_date, end_date, savepath, *, sleeptime=6):
    res = {}
    current_date = start_date
    while current_date != end_date:
        print('Crawling {}'.format(current_date))

        date = current_date.replace('-', '')
        url = create_url(latitude, longitude, date, date)
        res_json = get_json(url)

        filename = os.path.join(savepath, res_json['observations'][0]['obs_id'] + '.csv')
        if not os.path.exists(filename):
            with open(filename, 'w') as fh:
                fh.write('datetime(UTC) Temperature(°F) DewPoint(°F) Humidity(%) Pressure(in) WindSpeed(mph) WindDir UV_desc UV_index\n')

        save_records(filename, res_json['observations'])
        res[current_date] = res_json

        time.sleep(sleeptime)
        current_date = get_next_date(current_date)
    return res


def main():
    res = crawl(30.88, 114.37, '2011-01-01', '2019-12-31', '/Users/yinzhenping/data/wunderground/')


if __name__ == "__main__":
    main()
