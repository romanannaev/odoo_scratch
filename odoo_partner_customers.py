import copy
import csv
import requests
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

ODOO_HOST = "https://www.odoo.com"

gold_url = "https://www.odoo.com/partners/grade/gold-1/page/{}?country_all=True"
silver_url = "https://www.odoo.com/partners/grade/silver-2/page/{}?country_all=True"
ready_url = "https://www.odoo.com/partners/grade/ready-3/page/{}?country_all=True"

base_urls = {gold_url: ["Gold Partner", 6], silver_url: ["Silver Partner", 6], ready_url: ["Ready Partner", 26]}

csv_attrs = {
    "partner_name": None,
    "partner_web_site": None,
    "partner_status": None,
    "customer_name": None,
    "customer_address": None,
    "customer_description": None,
}

start_time = time.time()

chromedriver = '/usr/bin/chromedriver'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("enable-automation")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--dns-prefetch-disable")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--lang=en')
chrome_options.page_load_strategy = 'normal'
driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)

with open('partner_and_customers.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=csv_attrs.keys())
    writer.writeheader()

    partner_counter = 0
    for base_url, data in base_urls.items():
        for page in range(1, data[1] + 1):
            partner_list_html = requests.get(base_url.format(page)).text
            partner_list_soup = BeautifulSoup(partner_list_html, 'html.parser')

            partner_list_divs = partner_list_soup.find_all("div", attrs={"class": "media mt-3"})
            partner_urls = [partner.find("a").get("href") for partner in partner_list_divs]

            for pu in partner_urls:
                print(f"Partner with url is processed: {pu}")
                partner_counter += 1

                partner_profile_html = requests.get(f"{ODOO_HOST}{pu}").text
                partner_profile_soup = BeautifulSoup(partner_profile_html, 'html.parser')

                customers_list_divs = partner_profile_soup.find_all("div", attrs={"class": "media mt-3"})

                rows = []
                for customer in customers_list_divs:
                    copy_csv_attrs = copy.deepcopy(csv_attrs)

                    copy_csv_attrs["partner_name"] = partner_profile_soup.find("h1", attrs={"id": "partner_name"}).text.strip()
                    copy_csv_attrs["partner_status"] = data[0]
                    try:
                        partner_web_site = partner_profile_soup.find("span", attrs={"itemprop": "website"}).text.strip()
                    except AttributeError:
                        partner_web_site = None

                    copy_csv_attrs["partner_web_site"] = partner_web_site
                    copy_csv_attrs["customer_name"] = customer.find("div", attrs={"class": "media-body"}).find("span").text.strip()
                    try:
                        description = customer.find("div", attrs={"class": "media-body"}).find("div").text.strip()
                    except AttributeError:
                        description = None

                    copy_csv_attrs["customer_description"] = description

                    try:
                        driver.get(f"https://www.google.com/search?q={copy_csv_attrs['customer_name']}")
                        google_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        address = google_soup.find("span", attrs={"class": "LrzXr"}).text.strip()
                    except TimeoutException as err:
                        print(err.Message)
                        driver.navigate().refresh()
                        address = None
                    except AttributeError:
                        address = None

                    copy_csv_attrs["customer_address"] = address
                    rows.append(copy_csv_attrs)
                
                writer.writerows(rows)

            print(f"There were amount of partners processed: {partner_counter}")

print("--- {} seconds ---".format((time.time() - start_time)))