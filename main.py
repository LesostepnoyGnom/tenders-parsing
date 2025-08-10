import requests
from bs4 import BeautifulSoup
import re

from fastapi.responses import JSONResponse
from tqdm import tqdm
from tabulate import tabulate
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import math
import csv
import argparse
import json


app = FastAPI()

@app.get("/api/v1/tenders", summary='возвращает json с данными')
def tenders():
    link = "https://rostender.info/extsearch?page=1"

    rows = rows_from_table(link)

    lst = get_content_from_site(rows_on_page=len(rows), total=100)

    return JSONResponse(content=lst)


def save_to_csv(data, filename="output.csv"):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def rows_from_table(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    response = requests.get(link, headers=headers).text
    soup = BeautifulSoup(response, 'lxml')
    table = soup.find('div', id="table-constructor-body")
    rows = table.find_all("article")

    return rows

def get_content_from_site(rows_on_page, total=100):
    c = 1
    lst = []

    for page in tqdm(range(1, math.ceil(total / rows_on_page) + 1)):

        link = f"https://rostender.info/extsearch?page={page}"
        rows = rows_from_table(link)

        for row in rows:
            content = row.find("div")

            tender_id = content.find("span", class_="tender__number").find(string=True, recursive=False).strip().split()
            start = content.find("span", class_="tender__date-start").find(string=True, recursive=False).strip().split()[1]
            tender_class = content.find("div", class_="tender__class-wrap").find("div").get("aria-label")
            tender_class = re.sub(r'&nbsp;', ' ', tender_class)
            tender_class = re.sub(r'&laquo;', '"', tender_class)
            tender_class = re.sub(r'&raquo;', '"', tender_class)

            tender_pwh = content.find("div", class_="tender__pwh-wrap").find("div").get("aria-label")
            tender_pwh = re.sub(r'&nbsp;', ' ', tender_pwh)
            tender_pwh = re.sub(r'&mdash;', '-', tender_pwh)
            tender_pwh = re.sub(r'<p>', '', tender_pwh)
            tender_pwh = re.sub(r'</p>', '', tender_pwh)

            tender_info = content.find("div", class_="tender-info").find("a").find(string=True, recursive=False).strip()

            start_price = content.find("div", class_="starting-price__price starting-price--price").find(string=True, recursive=False).strip()
            start_price = "".join(start_price.split()[:-1])

            address = content.find("div", class_="tender-address").find("div").find(string=True, recursive=False).strip()

            region = content.find("a", class_="tender__region-link")
            if region:
                region = region.find(string=True, recursive=False).strip()

            end = content.find("span", class_="tender__countdown-text").find("span").find(string=True, recursive=False).strip()

            lst.append({"tender_id": tender_id[1],
                        "type": tender_id[0],
                        "start": start,
                        "tender_class": tender_class,
                        "tender_pwh": tender_pwh,
                        "tender_info": tender_info,
                        "start_price": start_price,
                        "address": address,
                        "region": region,
                        "end": end}
                       )

            if c >= total:
                break
            c += 1

    return lst


def main():
    parser = argparse.ArgumentParser(description='get tenders')
    parser.add_argument('--max', type=int, default=10, help='get n tenders')
    parser.add_argument('--output', type=str, default='output.csv', help='file name')
    args = parser.parse_args()

    link = "https://rostender.info/extsearch?page=1"

    rows = rows_from_table(link)

    lst = get_content_from_site(rows_on_page=len(rows), total=100)

    save_to_csv(lst, filename=args.output)

    print(tabulate(lst[:int(args.max)], headers='keys', tablefmt="grid", showindex="always", maxcolwidths=[None, None, None, None, 15, 20, 15, None, 15, 15, None]))

if __name__ == '__main__':
    main()