import tldextract
import langdetect
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'



"""
UTILITY FUNCTIONS USED BY OTHER CLASSES - DOCUMENTATION STILL NEEDED
"""

def split_list(links, n):
    interval = int(len(links)/n)
    result = []
    for cutoff in range(0, len(links), interval):
        if (cutoff + interval) > len(links):
            result.append(links[cutoff:])
        else:
            result.append(links[cutoff: (cutoff + interval)])
    
    return result

def is_link(href_str):
    if (href_str != None and "http" in href_str):
        return True
    return False

def extract_link_domain(url):
    url_extracted = tldextract.extract(url)
    url_base = url_extracted.registered_domain.lower()
    return url_base

def create_driver():
    # Create driver for operation on linux aws server
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service = service, options = options)

    return driver

def create_start_driver(url):
    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(service = service, options = options)

    #if user_agent_required(driver):
    #    options.add_argument(f"--user-agent={USER_AGENT}")

    return driver
    
"""
def user_agent_required(driver):
    # Check if user agent is required
    # Some sites will block the crawler if it does not have a user agent
    # This function checks if the site is blocking the crawler
    driver.get("https://www.whatismybrowser.com/detect/what-is-my-user-agent")
    user_agent = driver.find_element_by_id("detected_value")
    # autogenerated don't use this
    if user_agent.text == USER_AGENT:
        return False
    return True
"""

def is_number(str):
    try:
        float(str)
        return True
    except ValueError:
        return False
    
def link_in_queue(link_to_check, queue):
    queued_links = list(queue.indices.keys())
    for link in queued_links:
        if link_to_check == link:
            return True
    return False
        
def remove_anchor(link):
    """
    Removes anchor tags from links
    An anchor tag is link to a specifc part of a page, so only one needs to 
    be visited
    """    
    if "#" in link:
        link = link.split("#")[0]
    return link

def is_not_download(link):
    parse = urlparse(link)
    if '.' in parse.path:
        return False
    return True

def is_not_login(link):
    if "login" in link:
        return False
    return True

def passes_link_conditions(link):
    return is_link(link) and is_not_download(link) and is_not_login(link)

def remove_trailing_slash(path):
    if len(path) > 1:
        if path[-1] == "/":
        # print(path)
            path = path[:-1]
    return path

def clean_link(link):
    link = remove_anchor(link)
    link = remove_trailing_slash(link)
    return link

def num_slashes(url):
    parse = urlparse(url)
    path = parse.path
    cleaned_path = remove_trailing_slash(path)
    return cleaned_path.count("/")

def is_english(text_sample):
    return langdetect.detect(text_sample) == "en"    
"""
def subdirectory_depth(url):
    # Determine the depth that a link lies within a subdirectory
    # For example, www.google.com/1/2/3/4/5 would have a depth of 5
    
    url = url.split("/")
    depth = len(url) - 1
"""