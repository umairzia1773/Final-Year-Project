import scrapy


class EbayItemsSpider(scrapy.Spider):
    name = "ebay_items"
    allowed_domains = ["www.ebay.com"]
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(EbayItemsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://www.ebay.com/b/Samsung/bn_21834655']

        
    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',  # For output files
        'DEFAULT_RESPONSE_ENCODING': 'utf-8',  # For responses
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 3,  # Increased from 1
        'CONCURRENT_REQUESTS': 1,  # Reduced from 4
        'COOKIES_ENABLED': True,
        'AUTOTHROTTLE_ENABLED': True,
        'HTTPCACHE_ENABLED': True,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429, 307]
    }

    def parse(self, response):
        response = response.replace(encoding='utf-8')
        # First, collect all product URLs from the listing page
        product_urls = response.css('div.brwrvr__item-card__image-wrapper a::attr(href)').getall()
        
        for url in product_urls:
            yield response.follow(
                url,
                callback=self.parse_product,
                meta={'original_url': url}
            )

        # Pagination handling
        next_page = response.css("a.pagination__next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_product(self, response):
        # Extract basic product info
        product = {
            'url': response.meta['original_url'],
            'title': response.css('h1.x-item-title__mainTitle span::text').get(default='N/A').strip(),
            'price': response.css('div.x-price-primary span.ux-textspans::text').get(default='N/A').strip(),
            'condition': response.css('div.x-item-condition-text div.ux-textspans::text').get(default='N/A').strip(),
            'seller_info': {
                'name': response.css('div.ux-seller-section__item--seller a.ux-seller-section__link span::text').get(default='N/A').strip(),
                'feedback_score': response.css('div.ux-seller-section__item--seller div.ux-seller-section__feedback span::text').get(default='N/A').strip(),
            },
            'shipping_info': response.css('div.ux-labels-values__values div.ux-labels-values__value::text').get(default='N/A').strip(),
            'description': ' '.join(response.css('div.item-description div.ux-layout-section-evo__item--content *::text').getall()).strip(),
            'specifications': {}
        }

        # Extract product specifications
        for section in response.css('div.x-prp-product-details_section'):
            section_title = section.css('h3 span::text').get(default='').strip()
            if not section_title:
                continue
                
            product['specifications'][section_title] = {}
            
            for row in section.css('div.x-prp-product-details_row'):
                cols = row.css('div.x-prp-product-details_col')
                for col in cols:
                    name = col.css('span.x-prp-product-details_name span::text').get(default='').strip()
                    value = col.css('span.x-prp-product-details_value span::text').get(default='').strip()
                    if name and value:
                        product['specifications'][section_title][name] = value

        # Extract additional features if available
        features = response.css('div.ux-layout-section--features div.ux-layout-section__item--features div.ux-layout-section-evo__col')
        if features:
            product['key_features'] = []
            for feature in features:
                feature_text = feature.css('span::text').get(default='').strip()
                if feature_text:
                    product['key_features'].append(feature_text)

        # Extract ratings if available
        ratings = response.css('div.ebay-review-section')
        if ratings:
            product['ratings'] = {
                'average': ratings.css('span.review-item-stars span::attr(aria-label)').get(default='N/A'),
                'count': ratings.css('a.review-item-count span::text').get(default='N/A').strip(),
            }

        yield product
