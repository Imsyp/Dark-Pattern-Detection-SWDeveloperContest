import requests
from bs4 import BeautifulSoup
import re

from category_info import *
from rabbitmq_producer import *

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")

# RabbitMQ Producer 설정
mq_producer = RabbitMQProducer(
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USERNAME,
    RABBITMQ_PASSWORD,
    RABBITMQ_QUEUE,
)


# product_id, 가격 정보 수집
def get_product_info(product_box):

    href = product_box.find("a")["href"]
    match = re.search(r"/product/detail/(\d+)", href)

    # 매칭 product_id가 없을 경우 None 반환
    if not match:
        print(f"No product ID found in {href}")
        return None  # 매칭되지 않으면 None 반환
    product_id = int(match.group(1))

    # 할인가 & 정가 정보 수집
    sale_price = product_box.find("span", {"class": "price_discount"}).find("b").text
    reg_price = product_box.find("span", {"class": "price_original"}).find("b").text

    sale_price = int(sale_price.replace(",", ""))
    reg_price = int(reg_price.replace(",", ""))

    # 할인 가격이 존재하면 할인 가격 사용, 그렇지 않을 시 정가 사용
    if sale_price:
        price = sale_price
    else:
        price = reg_price

    if not price:
        print(f"No price found in {href}")
        return None

    result = {"product_id": product_id, "price": price}
    return result


# 개별 url 요청
def crawl(url):
    response = requests.get(url)

    if response.status_code == 200: # 요청 성공 시
        print(f"Successfully fetch.")

        soup = BeautifulSoup(response.text, "html.parser")
        product_boxes = soup.find_all("div", class_="wrapBox")

        result = []
        for product_box in product_boxes:
            # 상품 ID와 가격 정보 추출
            product_info = get_product_info(product_box)
            if product_info:
                result.append(product_info)
        mq_producer.produce(result) # RabbitMQ에 상품 정보 전송

    else: # 요청 실패 시
        print(f"Failed to retrieve {url}. Status code: {response.status_code}")


if __name__ == "__main__":

    for category_id in category_info.keys():
        url = f"https://www.oasis.co.kr/product/list?categoryId={category_id}&page=1&sort=priority&direction=desc&couponType=&rows=100000"
        crawl(url)

    mq_producer.close() # RabbitMQ 연결 종료
