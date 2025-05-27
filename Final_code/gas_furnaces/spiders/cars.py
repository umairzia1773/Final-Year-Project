import scrapy
import json
import re
from urllib.parse import urljoin
from itertools import zip_longest

class CarsSpider(scrapy.Spider):
    name = "cars"
    allowed_domains = ["pakwheels.com"]
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(CarsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://www.pakwheels.com/used-cars/search/-/']

    
    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
    }

            
    def parse(self, response):
       
        # Remove any query parameters first
        base_url = response.url.split('?')[0]
        print(base_url)
        if base_url != response.url:
            yield scrapy.Request(url=base_url, callback=self.parse, dont_filter=True)
            return

        # Handle specific vehicle detail pages (containing numeric IDs)
        if re.search(r'/(used-cars|used-bikes)/[^/]+/\d+/', base_url):
            yield from self.parse_used_vehicle_detail(response)
            return

        # Handle used vehicles search/category URLs
        if any(x in base_url for x in ['/used-cars/', '/used-bikes/']):
            # Don't modify URLs that already have search parameters
            if '/search/' in base_url:
                pass
            # Don't modify city/region pages
            elif re.search(r'/(used-cars|used-bikes)/[a-z-]+/$', base_url):
                pass
            # Only add /search/-/ to root category pages
            elif base_url.endswith(('used-cars/', 'used-bikes/')):
                clean_url = base_url.rstrip('/') + '/search/-/'
                yield scrapy.Request(url=clean_url, callback=self.parse, dont_filter=True)
                return

        # Handle new vehicles URLs
        elif '/new-bikes/' in base_url:
            if not base_url.endswith('bikes/search/make_any/model_any/price_any_any/'):
                clean_url = base_url.replace('/new-bikes/', '/search/make_any/model_any/price_any_any/')
                yield scrapy.Request(url=clean_url, callback=self.parse, dont_filter=True)
                return
                
        elif '/new-cars/' in base_url:
            if not base_url.endswith('search/make_any/model_any/price_any_any/'):
                clean_url = base_url.rstrip('/') + '/search/make_any/model_any/price_any_any/'
                yield scrapy.Request(url=clean_url, callback=self.parse, dont_filter=True)
                return

        # Now process the page based on its type
        if any(x in base_url for x in ['/used-cars/', '/used-bikes/']):
            yield from self.parse_used_listing(response)
        elif any(x in base_url for x in ['/new-cars/', '/bikes/']):
            yield from self.parse_new_listing(response)
        else:
            self.logger.warning(f"Unknown page type: {base_url}")

    def parse_used_listing(self, response):
        """Parse used vehicle listings"""
        for listing in response.css('li.classified-listing'):
            vehicle_url = listing.css('a.car-name::attr(href)').get()
            if vehicle_url:
                full_url = urljoin('https://www.pakwheels.com', vehicle_url)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_used_vehicle_detail,
                    meta={
                        'basic_info': self.extract_basic_info(listing)
                    }
                )
        
        next_page = response.css('a.next_page::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=urljoin(response.url, next_page), callback=self.parse)

    def parse_new_listing(self, response):
        """Parse new vehicle listings"""
        for listing in response.css('li > div.new-car-box'):
            vehicle_url = listing.css('a.car-name::attr(href)').get()
            if vehicle_url:
                full_url = urljoin('https://www.pakwheels.com', vehicle_url)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_new_vehicle_detail,
                    meta={
                        'basic_info': self.extract_new_basic_info(listing)
                    }
                )
        
        next_page = response.css('a.next_page::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=urljoin(response.url, next_page), callback=self.parse)

    def extract_basic_info(self, listing):
        """Extract basic info from used vehicle listing card"""
        item = {
            'listing_url': urljoin('https://www.pakwheels.com', listing.css('a.car-name::attr(href)').get()),
            'title': listing.css('a.car-name h3::text').get('').strip(),
            'price': self.parse_price(listing.css('.price-details::text').getall()),
            'city': listing.css('.search-vehicle-info li:first-child::text').get('').strip(),
            'is_featured': 'featured' in listing.css('::attr(class)').get(''),
            'updated_time': listing.css('.dated::text').get('').replace('Updated', '').strip(),
            'listing_type': 'used'
        }

        # Extract from JSON-LD if available
        script_data = listing.css('script[type="application/ld+json"]::text').get()
        if script_data:
            try:
                json_data = json.loads(script_data)
                item.update({
                    'brand': json_data.get('brand', {}).get('name', ''),
                    'condition': json_data.get('itemCondition', ''),
                    'year': json_data.get('modelDate', ''),
                    'manufacturer': json_data.get('manufacturer', ''),
                    'fuel_type': json_data.get('fuelType', ''),
                    'transmission': json_data.get('vehicleTransmission', ''),
                    'engine_cc': json_data.get('vehicleEngine', {}).get('engineDisplacement', '').replace('cc', '').strip(),
                    'mileage': json_data.get('mileageFromOdometer', '').replace(',', '').replace(' km', ''),
                })
            except json.JSONDecodeError:
                pass

        # Extract from visible specs
        specs = listing.css('.search-vehicle-info-2 li::text').getall()
        if len(specs) >= 1 and not item.get('year'):
            item['year'] = specs[0].strip()
        if len(specs) >= 2 and not item.get('mileage'):
            item['mileage'] = specs[1].strip().replace(',', '').replace(' km', '')
        if len(specs) >= 3 and not item.get('fuel_type'):
            item['fuel_type'] = specs[2].strip()
        if len(specs) >= 4 and not item.get('engine_cc'):
            item['engine_cc'] = specs[3].strip().replace('cc', '')
        if len(specs) >= 5 and not item.get('transmission'):
            item['transmission'] = specs[4].strip()

        return {k: v for k, v in item.items() if v}

    def extract_new_basic_info(self, listing):
        """Extract basic info from new vehicle listing card"""
        item = {
            'listing_url': urljoin('https://www.pakwheels.com', listing.css('a.car-name::attr(href)').get()),
            'title': listing.css('a.car-name h3::text').get('').strip(),
            'price': self.parse_price(listing.css('.price-details::text').getall()),
            'listing_type': 'new'
        }

        # Extract from JSON-LD if available
        script_data = listing.css('script[type="application/ld+json"]::text').get()
        if script_data:
            try:
                json_data = json.loads(script_data)
                item.update({
                    'brand': json_data.get('brand', {}).get('name', ''),
                    'model': json_data.get('model', ''),
                    'year': json_data.get('modelDate', ''),
                    'manufacturer': json_data.get('manufacturer', ''),
                    'fuel_type': json_data.get('vehicleEngine', {}).get('fuelType', ''),
                    'engine_cc': json_data.get('vehicleEngine', {}).get('engineDisplacement', {}).get('value', ''),
                    'category': json_data.get('category', ''),
                })
            except json.JSONDecodeError:
                pass

        # Extract from visible specs
        specs = listing.css('.ad-specs li::text').getall()
        if specs:
            item['specs'] = [s.strip() for s in specs if s.strip()]

        return {k: v for k, v in item.items() if v}

    def parse_used_vehicle_detail(self, response):
        """Parse used vehicle detail page"""
        item = response.meta['basic_info']
        
        # Extract specifications
        specs = {}
        for group in response.css('#scroll_car_detail'):
            labels = group.css('li.ad-data::text').getall()
            values = group.css('li:not(.ad-data)').xpath('normalize-space()').getall()
            
            for label, value in zip_longest(labels, values, fillvalue=''):
                clean_label = label.strip().replace(':', '').replace(' ', '_').lower()
                if clean_label and value.strip():
                    specs[clean_label] = value.strip()
        item.update(specs)

        # Extract detailed specifications and features from tabs
        detailed_specs = self.extract_detailed_specs(response)
        if detailed_specs:
            item['detailed_specifications'] = detailed_specs

        # Extract features
        features = self.extract_features(response)
        if features:
            item['features'] = features

        # Extract images
        images = self.extract_images(response)
        if images:
            item['images'] = images

        # Extract seller comments
        seller_comments = []
        for comment_div in response.css('div.description-details'):
            comment_lines = comment_div.xpath('.//text()[not(ancestor::label)]').getall()
            for line in comment_lines:
                cleaned_line = line.strip()
                if cleaned_line and not cleaned_line.startswith('Mention PakWheels.com'):
                    seller_comments.append(cleaned_line)
        
        if seller_comments:
            item['seller_comments'] = '\n'.join(seller_comments)

        yield item

    def parse_new_vehicle_detail(self, response):
        """Parse new vehicle detail page"""
        item = response.meta['basic_info']
        
        # Extract specifications from table
        specs = {}
        for row in response.css('.table.table-striped tr'):
            label = row.css('td:first-child::text').get('').strip()
            value = row.css('td:last-child::text').get('').strip()
            if label and value:
                clean_label = label.strip().replace(':', '').replace(' ', '_').lower()
                specs[clean_label] = value
        item.update(specs)

        # Extract detailed specifications and features from tabs
        detailed_specs = self.extract_detailed_specs(response)
        if detailed_specs:
            item['detailed_specifications'] = detailed_specs

        # Extract features
        features = self.extract_features(response)
        if features:
            item['features'] = features

        # Extract images
        images = self.extract_images(response)
        if images:
            item['images'] = images

        # Extract additional details from JSON-LD
        script_data = response.css('script[type="application/ld+json"]::text').get()
        if script_data:
            try:
                json_data = json.loads(script_data)
                item.update({
                    'description': json_data.get('description', ''),
                    'colors': json_data.get('color', []),
                    'fuel_capacity': json_data.get('fuelCapacity', {}).get('value', ''),
                    'fuel_efficiency': json_data.get('fuelEfficiency', {}).get('value', ''),
                    'top_speed': json_data.get('speed', {}).get('maxValue', ''),
                    'dimensions': {
                        'width': json_data.get('width', {}).get('value', ''),
                        'height': json_data.get('height', {}).get('value', ''),
                        'wheelbase': json_data.get('wheelbase', {}).get('value', ''),
                    },
                    'weight': json_data.get('weight', {}).get('value', '')
                })
            except json.JSONDecodeError:
                pass

        yield item

    def extract_detailed_specs(self, response):
        """Extract detailed specifications from specification tabs"""
        specs = {}
        
        # Process each specification section
        for section in response.css('.specs-wrapper'):
            section_name = section.css('.specs-heading::text').get('').strip()
            if not section_name:
                continue
                
            section_specs = {}
            for row in section.css('table tr'):
                label = row.css('td:first-child::text').get('').strip()
                value = row.css('td:last-child').xpath('normalize-space()').get('').strip()
                
                # Handle checkmark icons
                if not value:
                    if row.css('td:last-child .fa-check'):
                        value = 'Yes'
                    elif row.css('td:last-child .fa-times'):
                        value = 'No'
                
                if label and value:
                    clean_label = label.strip().replace(':', '').replace(' ', '_').lower()
                    section_specs[clean_label] = value
            
            if section_specs:
                specs[section_name.lower().replace(' ', '_')] = section_specs
        
        return specs if specs else None

    def extract_features(self, response):
        """Extract features from features tabs"""
        features = {}
        
        # Process each feature section
        for section in response.css('#carfeatures .specs-wrapper'):
            section_name = section.css('.specs-heading::text').get('').strip()
            if not section_name:
                continue
                
            section_features = {}
            for row in section.css('table tr'):
                label = row.css('td:first-child::text').get('').strip()
                value = row.css('td:last-child').xpath('normalize-space()').get('').strip()
                
                # Handle checkmark icons
                if not value:
                    if row.css('td:last-child .fa-check'):
                        value = 'Yes'
                    elif row.css('td:last-child .fa-times'):
                        value = 'No'
                
                if label and value:
                    clean_label = label.strip().replace(':', '').replace(' ', '_').lower()
                    section_features[clean_label] = value
            
            if section_features:
                features[section_name.lower().replace(' ', '_')] = section_features
        
        return features if features else None

    def extract_images(self, response):
        """Extract all images from vehicle detail page"""
        images = []
        
        # Method 1: From lightSlider main images
        for img in response.css('.lightSlider li img'):
            img_url = img.css('::attr(data-original)').get() or img.css('::attr(src)').get()
            if img_url and not img_url.startswith('data:image') and img_url not in images:
                images.append(img_url)
        
        # Method 2: From thumbnail gallery
        for thumb in response.css('.lSGallery img.slider-thumb'):
            thumb_url = thumb.css('::attr(src)').get() or thumb.css('::attr(data-original)').get()
            if thumb_url and not thumb_url.startswith('data:image') and thumb_url not in images:
                images.append(thumb_url)
        
        # Method 3: Fallback to any image with data-original attribute
        if not images:
            for img in response.css('img[data-original]'):
                img_url = img.css('::attr(data-original)').get()
                if img_url and img_url not in images:
                    images.append(img_url)
        
        # Clean image URLs
        clean_images = []
        for img in images:
            if img.startswith('//'):
                img = 'https:' + img
            elif img.startswith('/'):
                img = 'https://www.pakwheels.com' + img
            clean_images.append(img)
        
        return clean_images

    def parse_price(self, price_elements):
        """Robust price parsing"""
        price_text = ''.join(price_elements).strip()
        if not price_text:
            return None
        
        if 'lac' in price_text.lower():
            try:
                num = float(re.search(r'[\d.]+', price_text).group())
                return int(num * 100000)
            except (AttributeError, ValueError):
                pass
        
        try:
            return int(re.sub(r'[^\d]', '', price_text))
        except ValueError:
            return None