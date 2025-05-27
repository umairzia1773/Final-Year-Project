import scrapy
from bs4 import BeautifulSoup, Comment
import re

class GasSpider(scrapy.Spider):
    name = "gas"
    allowed_domains = ["lennoxpros.com"]
    #start_urls = ["https://www.lennoxpros.com/hvac/furnaces/gas-furnaces/c/r109"]

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if start_url:
            self.start_urls = [start_url]  # Set the start URL from the command line
        else:
            self.start_urls = ["https://www.lennoxpros.com/hvac/furnaces/gas-furnaces/c/r109"]  # Default URL
            
    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
    }


    def clean_and_prettify_html(self, html_content):
        # Create a BeautifulSoup object for parsing
        soup = BeautifulSoup(html_content, 'html.parser')   
        
            
        # Remove comments and unnecessary tags like divs containing PDFs
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # # Remove divs containing .pdf links
        
        # Remove divs containing links to PDF files
        for link in soup.find_all('a', href=True):
            if '.pdf' in link['href']:
                parent_div = link.find_parent('div')
                if parent_div:
                    parent_div.decompose()  # Remove the entire div containing the PDF link

        # Clean up weird characters
        text = str(soup)
        clean_text = re.sub(r'[Ââ€¢€™®]', '', text)
        
        # Remove tab characters and extra whitespace
        clean_text = clean_text.replace('\t', '').strip()
        
        # Parse the cleaned text back into BeautifulSoup for pretty output (optional)
        clean_soup = BeautifulSoup(clean_text, 'html.parser')
        # Return prettified HTML content
        prettified_html = clean_soup.prettify()

        return prettified_html
    
    def simplify_html(self, html_code):
	
        # Replace the soup content with the cleaned HTML
        soup = BeautifulSoup(html_code, 'html.parser')

        # Remove h2 tags containing the text 'Product Overview'
        for h2_tag in soup.find_all('h2'):
            if 'Product Overview' in h2_tag.get_text():
                h2_tag.decompose()  # Remove the entire h2 tag
    
    # Remove specified tags: div, span, style
        for tag in soup.find_all(['div', 'span', 'style']):
                tag.unwrap()

    
    # Find all <p> tags and remove the empty ones
        for p in soup.find_all('p'):
            if not p.get_text(strip=True):  # Check if <p> tag is empty or contains only whitespace
                p.decompose()

        cleaned_html = soup.prettify()
    
        # Clean up unnecessary spaces and newlines
        cleaned_html = ' '.join(line.strip() for line in cleaned_html.splitlines() if line.strip())
        cleaned_html = soup.prettify()
        return cleaned_html
    
    def parse(self, response):
        # Extract product page links and images from the main product list page
        product_links = response.css('.inner a::attr(href)').getall()
        images = response.css('.thumb img::attr(src)').getall()
        
        for link, image in zip(product_links, images):
            absolute_link = response.urljoin(link)
            absolute_image = response.urljoin(image)
            yield response.follow(absolute_link, callback=self.parse_product, meta={'image_url': absolute_image})
        
        # Pagination - follow the next page link
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            next_page = 'https://www.lennoxpros.com' + next_page
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        # Extract product name and image URL
        product_title = response.css('h1::text').get()
        product_description = response.css('div.col-12.col-xl-8.Product-overview').get()
        product_description = self.clean_and_prettify_html(product_description)
        product_description_new = self.simplify_html(product_description)
        
        
        # Extract specification table
        specifications = {}
        spec_rows = response.css('.specification-container')
        for row in spec_rows:
            spec_key = row.css('span.title.col div::text').get().strip()
            spec_value = row.css('span.description.col div::text').get().strip()
            specifications[spec_key] = spec_value
        try:
            product_name = specifications['Brand'] + ' ' + specifications['Model/Part Number'] + ' ' + 'Furnace'
        except KeyError:
            product_name = specifications.get('Brand', '') + ' ' + 'Furnace'

        product_listing_title = specifications.get('Brand','') + ' ' + specifications.get('Model/Part Number', '') + ' ' + specifications.get('Gas Stages', '') + ' ' + 'Furance'
        
        
        # Get the image URL from meta
        image_url = response.meta.get('image_url', '')
        
        # Store product data
        yield {
            'Product Page_url': response.url,
            'Product Image_url': image_url,
            'Image_Large': image_url.replace("?$product_related$", ""),
            'Product Name': product_name,
            'Product Title': product_title,
            #'Product Description': product_description,
            #'Product Description New': product_description_new,
            'Product Listing Title': product_listing_title,
            **specifications
        }