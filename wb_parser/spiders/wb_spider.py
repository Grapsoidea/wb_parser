import scrapy
import datetime


class WBSpider(scrapy.Spider):
    name = "wb_parser"

    start_urls = [
        'https://www.wildberries.ru/catalog/obuv/zhenskaya/sabo-i-myuli/myuli'
    ]

    section = None

    def parse(self, response):
        # follow links to products' pages
        for href in response.css('a.ref_goods_n_p::attr(href)'):
            yield response.follow(href, self.parse_product)

        if not self.section:
            self.section = response.css(
                'div.breadcrumbs div a span::text').extract()

        # folow links to next page
        for href in response.css('a.next::attr(href)'):
            yield response.follow(href, self.parse)

    def parse_product(self, response):
        def extract_number(str_):
            if not isinstance(str_, str):
                return None
            number = ""
            for s in str_:
                if s.isdigit():
                    number += s
            if number.isdigit():
                return float(number)
            else:
                return None

        # current price
        current = response.css(
            'span.add-discount-text-price::text').extract_first()
        # if price whith discount exist
        if current:
            current = extract_number(current)
            original = extract_number(
                response.css('span.price-popup del::text').extract_first())
            discount = int((original - current) / original * 100)
            sale_tag = 'Скидка {}%'.format(discount)
        # don't exist
        else:
            original = extract_number(
                response.css('div.j-price div p ins::text').extract_first())
            current = original
            sale_tag = None

        yield {
            "timestamp": datetime.datetime.now().timestamp(),
            "RPC": response.css('span.j-article::text').extract_first(),
            "url": response.url,
            "title": response.css('title::text').extract_first(),
            "marketing_tags": response.css(
                'li.tags-group-item a::text').extract(),
            "brand": response.css(
                'div.good-header meta::attr(content)').extract_first(),
            "section": self.section,
            "price_data": {
                "current": current,
                "original": original,
                "sale_tag": sale_tag
            },
            "assets": {
                "main_image": response.xpath(
                    '//img[@id="preview-large"]/@src').extract_first(),
                "set_images": response.css(
                    'ul.carousel li a img::attr(src)').extract(),
                "view360": [],
                "video": []
            },
            "metadata": {
                "__description": response.xpath(
                    '//div[@id="description"]/div/p/text()').extract_first(),
                "АРТИКУЛ": response.css('span.j-article::text').extract_first()
            }
        }
