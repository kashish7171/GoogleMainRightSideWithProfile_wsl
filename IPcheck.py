import re
import os
import time
import json
import psutil
import multiprocessing
import mysql.connector
from urllib.parse import urlparse
from datetime import datetime, date
from random import randint, uniform
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains, Keys
from modules.saveRanks import commence as evalRanking
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from modules.runTimeSecrets import HOST, DB, USER, PASS, HOST2, DB2, USER2, PASS2, HOST3, DB3, USER3, PASS3

# --------------------------------- GLOBAL ---------------------------------
LIMIT = 1
PROFILE_DIR = "/usr/bin/google-chrome"
PROFILE = "Default"
PROJECT_DIR = "/mnt/d/projects2025/march/31_march/GoogleMainRightSideWithProfile_wsl"
WINDOWS_CHROMEDRIVER_PATH = PROJECT_DIR + "/driver/chromedriver"
useProfile = False
scraped_by_system = "pc"
vendorID = 10021
# --------------------------------- GLOBAL ---------------------------------

# --------------------------------- LOGGER ---------------------------------
import logging
def loggerInit(logFileName):
    try: os.makedirs("logs/ss")
    except: pass
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
    file_handler = logging.FileHandler(f'logs/{logFileName}')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger
logger = loggerInit(logFileName="IPcheck.log")
# --------------------------------- LOGGER ---------------------------------

def init_selenium_driver(IpCheck=False, useVPN=False):
    """
    Initialize the Selenium driver with headless options
    """
    logger.debug(f"trigger selenium")
    from seleniumwire import webdriver
    
    with open("vpn.config.json") as json_data_file:
        configs = json.load(json_data_file)
    for atmpt in range(3):
        try:
            VPN_IP_PORT = configs['VPN_IP_PORT'][randint(0, len(configs['VPN_IP_PORT']) - 1)]
            seleniumwire_options = {
                'proxy': {
                    "http": f"http://{VPN_IP_PORT}",
                    "https": f"https://{VPN_IP_PORT}",
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }

            chrome_options = webdriver.ChromeOptions()
            # Set homepage preferences
            if useProfile:
                chrome_options.add_argument(f"--user-data-dir={PROFILE_DIR}")
                chrome_options.add_argument(f"--profile-directory={PROFILE}")

            # Critical stability arguments
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            # chrome_options.add_argument("--   headless")
            chrome_options.add_argument("--start-maximized")
            # Unique remote debugging port
            debugging_port = 9222 + (multiprocessing.current_process().pid % 1000)
            chrome_options.add_argument(f"--remote-debugging-port={debugging_port}")

            service = ChromeService(WINDOWS_CHROMEDRIVER_PATH, port=9515 + (multiprocessing.current_process().pid % 1000))
            driver = webdriver.Chrome(
                service=service,
                options=chrome_options,
                seleniumwire_options=seleniumwire_options if useVPN else {}
            )

            # Check IP address
            try:
                if IpCheck:
                    random_pause(1, 2)
                    driver.get("https://api.ipify.org?format=json")
                    random_pause(1, 2)
                    for request in driver.requests:
                        if request.response:
                            if 'ipify' in request.url:
                                ip_info = json.loads(request.response.body.decode('utf-8'))
                                ip_address = ip_info.get('ip', 'IP not found')
                                logger.debug(f"Current IP: {ip_address}")
                                break
                random_pause(1, 2)
                return driver
            except:
                driver.get_screenshot_as_file(f"logs/ss/IpException({VPN_IP_PORT}).png")
                driver.quit()
                raise Exception("BadSession")
        except Exception as e:
            logger.debug(f"Attempting ({atmpt + 1}/3) >> {e}")
            if atmpt == 2: raise e

def random_pause(min_time=2, max_time=5):
    """
    Add a random pause to simulate human thinking or waiting.
    """
    time.sleep(uniform(min_time, max_time))

def scroll_page(driver, min_scroll=100, max_scroll=1000):
    """
    Simulate smooth scrolling behavior
    """
    scroll_height = randint(min_scroll, max_scroll)
    driver.execute_script(f"""
        window.scrollBy({{
            top: {scroll_height},
            behavior: 'smooth'
        }});
    """)
    time.sleep(uniform(1, 3) + 0.5)

def human_typing(driver, element, text, min_delay=0.05, max_delay=0.2):
    """
    Mimic human typing for a given element in the Firefox browser using Selenium.

    Parameters:
    driver (WebDriver): The Selenium WebDriver instance.
    element (WebElement): The web element to type into.
    text (str): The text to type out.
    min_delay (float): Minimum delay between key presses.
    max_delay (float): Maximum delay between key presses.
    """
    actions = ActionChains(driver)
    # Clear any existing text in the element
    element.clear()
    for char in text:
        actions.send_keys(char)
        actions.perform()
        time.sleep(uniform(min_delay, max_delay))
    actions.send_keys(Keys.RETURN).perform()

def googleMainRightSideBox(searchKey):
    driver = init_selenium_driver(IpCheck=True, useVPN=True)
    try:
        # open google
        driver.get(f"https://www.google.com")
        random_pause(2, 4)
        # paste keyword and hit search
        try: search_box = driver.find_element(By.NAME, "q")
        except:
            logger(f"Google search box not found")
            return
        human_typing(driver, search_box, f"{searchKey}")
        random_pause(5, 10)
        # Check for captcha page
        while True:
            if "https://www.google.com/sorry/index" in driver.current_url:
                logger.debug(f"Captcha Detected, Waiting to be resolved manually")
                random_pause(10, 20)
            else: break
        # Check for consent page and handle it
        if "https://consent.google.com/" in driver.current_url:
            ActionChains(driver).send_keys(Keys.TAB).perform()
            ActionChains(driver).send_keys(Keys.ENTER).perform()
        # main div
        try: main = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'main')))
        except: main = None
        # google main search result -ss
        imgName = f"{searchKey}".lower()
        # driver.get_screenshot_as_file(f"logs/ss/{imgName}.png")
        if main is None:
            logger.debug(f"Main div not found.")
            driver.get_screenshot_as_file(f"logs/ss/{imgName}-mainDivNotFound.png")
        else:
            logger.debug(f"Main div found.")
        return True    
    except Exception as e:
        logger.debug(f"Error in googleMainRightSideBox :{e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    searchKey = "Toto SN989M01"
    try:
        respnse = googleMainRightSideBox(searchKey)
        if respnse:
            logger.info("IP is working")
        else:
            logger.info("IP is blocked")    
    except Exception as e:
        print(f"Error in main:{e}")    