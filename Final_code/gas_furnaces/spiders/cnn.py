import scrapy
from urllib.parse import urljoin

class CnnSpider(scrapy.Spider):
    name = "cnn"
    allowed_domains = ["edition.cnn.com", "cnn.com"]
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(CnnSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://www.cnn.com/world/middle-east']
    
    def parse(self, response):
        # Extract all news article URLs from the page
        article_urls = response.css('a.container__link::attr(href)').getall()
        
        # Filter and clean URLs
        article_urls = [url for url in article_urls if url.startswith('/202')]
        article_urls = list(set(article_urls))  # Remove duplicates
        
        # Follow each article URL
        for url in article_urls:
            absolute_url = urljoin('https://www.cnn.com', url)
            yield scrapy.Request(
                absolute_url,
                callback=self.parse_article,
                meta={'original_url': absolute_url}
            )
    
    def parse_article(self, response):
        # Extract article data
        yield {
            'url': response.meta['original_url'],
            'title': response.css('h1.headline__text::text').get().strip(),
            'description': self.extract_description(response),
            'images': self.extract_images(response),
            'videos': self.extract_videos(response),
            'text': self.extract_article_text(response)
        }
    
    def extract_description(self, response):
        # Try to find a description in the article
        description = response.css('meta[name="description"]::attr(content)').get()
        if not description:
            # Fallback to first paragraph if no meta description
            description = response.css('p.paragraph::text').get()
        return description.strip() if description else None
    
    def extract_images(self, response):
        # Extract all image URLs from the article
        images = []
        image_elements = response.css('div.image__container picture source::attr(srcset)').getall()
        
        for img in image_elements:
            # Get the highest resolution version if multiple sizes are available
            img_url = img.split('?')[0]  # Remove query parameters
            if img_url.startswith('http'):
                images.append(img_url)
        
        return list(set(images))  # Remove duplicates
    
    def extract_videos(self, response):
        # Extract video URLs if present
        videos = []
        video_elements = response.css('div.media__video source::attr(src)').getall()
        
        for vid in video_elements:
            if vid.startswith('http'):
                videos.append(vid)
        
        return videos
    
    def extract_article_text(self, response):
        # Extract all paragraphs of text
        paragraphs = response.css('p.paragraph::text').getall()
        return ' '.join([p.strip() for p in paragraphs if p.strip()])
