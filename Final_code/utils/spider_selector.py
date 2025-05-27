import re
from urllib.parse import urlparse

def identify_spider(url):
    """
    Determine which spider to use based on the URL domain
    Returns spider name or None if no match found
    """
    domain_rules = {
        'cars': [
            r'pakwheels\.com',
            r'pakwheels\.com\.pk'
        ],
        'ebay_items': [
            r'ebay\.com',
            r'ebay\.co\.uk',
            r'ebay\.de'
        ],
        'gas': [
            r'lennoxpros\.com'
        ],
        'cnn': [
            r'edition.cnn.com',
            r'cnn.com'
        ]
        # Add more sites as needed
    }

    try:
        domain = urlparse(url).netloc.lower()
        for spider_name, patterns in domain_rules.items():
            for pattern in patterns:
                if re.search(pattern, domain):
                    return spider_name
        return None
    except Exception as e:
        print(f"Error identifying spider: {e}")
        return None