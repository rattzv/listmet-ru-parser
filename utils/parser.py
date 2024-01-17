import re

from bs4 import BeautifulSoup
from utils.utils import get_current_time, get_requests, print_template


def parsing_pagination(soup):
    pagination = soup.find('div', 'default-pagination__pages')
    if pagination:
        pagination_pages = pagination.find_all('a')
        second_page = int(pagination_pages[0].get_text(strip=True))
        last_page = int(pagination_pages[-1].get_text(strip=True))

        return True, range(second_page, last_page + 1)
    return False, []


def parsing_products_on_page(soup):
    products_links = []
    products_wrapper = soup.find_all('tbody', 'catalog-list2')
    for element in products_wrapper:
        onclick = element.find('h2').get('onclick')
        if 'window.location=' in onclick:
            products_links.append(onclick[17:-2])
    return products_links if len(products_links) > 0 else False


def parsing_page(url):
    response = get_requests(url)
    if not response:
        return False

    soup = BeautifulSoup(response.text, 'html.parser')
    return parsing_products_on_page(soup)


def parsing_product_page(url):
    try:
        response = get_requests(url)
        if not response:
            print_template(f'Error (HTTP) parsing product {url}')
            return False

        soup = BeautifulSoup(response.content, 'html.parser')

        product_item = soup.find('div', 'product_item')
        if not product_item:
            print_template(f'Key element "product_item" not found on page {url})')
            return False

        product = {}

        product['Наименование'] = soup.find('h1', 'product_item_title').get_text(strip=True)
        product['Время парсинга (мск)'] = get_current_time()
        product['URL товара'] = url

        breadcrumbs = soup.find('div', 'breadcrumbs-container')
        if breadcrumbs:
            breadcrumbs_items = breadcrumbs.find_all('div', 'breadcrumbs-container__item')
            if len(breadcrumbs_items) > 2 and breadcrumbs_items[2].find('a'):
                product['Раздел'] = breadcrumbs_items[2].find('a').get_text(strip=True)
            if len(breadcrumbs_items) > 3 and breadcrumbs_items[3].find('a'):
                product['Категория'] = breadcrumbs_items[3].find('a').get_text(strip=True)

        characteristics = soup.find_all(class_='catalog-detail__property')
        for element in characteristics:
            name = element.find('div', 'catalog-detail__property-name').get_text(strip=True)
            value = element.find('div', 'catalog-detail__property-value').get_text(strip=True)
            value = re.sub(r'\s+', ' ', value)
            if name and name is not None and value and value is not None:
                product[name] = value

        availability_in_cities = {}
        detail_existences = soup.find('div', 'catalog-detail__existences')
        existences = detail_existences.find_all('div', 'catalog-detail__existence')
        for existence in existences:
            city = existence.find('span', 'catalog-list-item__storage-city').get_text(strip=True)
            count = existence.find('div', 'catalog-list-item__existence-text').get_text(strip=True)
            if city and city is not None and count and count is not None:
                availability_in_cities[city] = count

        product['Наличие'] = availability_in_cities

        price_items = soup.find_all('div', 'catalog-detail__price-item')
        for item in price_items:
            price = item.find('div', 'catalog-detail__price').get_text(strip=True).lower()
            descriptor = 'Цена ' + item.find('span', 'catalog-detail__price-descriptor').get_text(strip=True).lower()
            if descriptor and descriptor is not None and price and price is not None:
                product[descriptor] = price
        return product
    except Exception as ex:
        print(print_template(f'Error: {ex} ({url})'))
        return False

