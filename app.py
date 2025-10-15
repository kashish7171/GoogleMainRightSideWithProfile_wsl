import re
import os
import glob
import time
import json
import psutil
import random
import multiprocessing
import mysql.connector
from urllib.parse import urlparse
from datetime import datetime, date, timedelta
from decimal import Decimal
from random import randint, uniform
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains, Keys
from modules.saveRanks import commence as evalRanking
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from modules.runTimeSecrets import HOST, DB, USER, PASS, HOST2, DB2, USER2, PASS2, HOST3, DB3, USER3, PASS3

# --------------------------------- GLOBAL ---------------------------------
LIMIT = 7
# PROFILE_DIR = "/mnt/c/users/matrid/AppData/Local/Google/Chrome/User Data"
# PROFILE = "Profile 17"
PROFILE_DIR = "/usr/bin/google-chrome"
PROFILE = "Default"
PROJECT_DIR = "/home/matrid/Project/GoogleMainRightSideWithProfile_wslAF"
WINDOWS_CHROMEDRIVER_PATH = PROJECT_DIR + "/driver/chromedriver"
useProfile = False
scraped_by_system = "Kashish Neighbour PC"
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
logger = loggerInit(logFileName="pricing.from.google.main.right.side.log")
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
            # VPN_IP_PORT = configs['VPN_IP_PORT'][randint(0, len(configs['VPN_IP_PORT']) - 1)]
            # print(VPN_IP_PORT)
            # seleniumwire_options = {
            #     'proxy': {
            #         "http": f"http://{VPN_IP_PORT}",
            #         "https": f"https://{VPN_IP_PORT}",
            #         'no_proxy': 'localhost,127.0.0.1'
            #     }
            # }
            vpn_user = configs['VPN_User']
            vpn_pass = configs['VPN_Pass']
            vpn_ip_port = configs['VPN_IP_PORT'][random.randint(0, len(configs['VPN_IP_PORT']) - 1)]
            print(vpn_ip_port)
            seleniumwire_options = {
                'proxy': {
                    "http": f"http://{vpn_user}:{vpn_pass}@{vpn_ip_port}",
                    "https":f"https://{vpn_user}:{vpn_pass}@{vpn_ip_port}",
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }
            chrome_options = webdriver.ChromeOptions()
            # Set homep= preferences
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
                driver.get_screenshot_as_file(f"logs/ss/IpException({vpn_ip_port}).png")
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

# to scrape compeittors from right side box on google main
def googleMainRightSideBox(searchKey, productID, data, atmpt=1):
    driver = init_selenium_driver(IpCheck=False, useVPN=True)
    try:
        # open google
        driver.get(f"https://www.google.com/")
        random_pause(4, 10)

        # # Try the first XPath, if not found, try the second
        # wait = WebDriverWait(driver, 1=        # try:
        #     # First attempt
        #     stay_signed_out_btn = wait.until(EC.element_to_be_clickable(
        #         (By.XPATH, '//*[@id="stUuGf"]/div/div[2]/div/div/div/div[2]/div/promo-button-text[1]/div/div/div')
        #     ))
        #     stay_signed_out_btn.click()
        #     print("Clicked 'Stay signed out' (First XPath)")
        # except Exception:
        #     try:
        #         # Second attempt
        #         alternative_btn = wait.until(EC.element_to_be_clickable(
        #             (By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/c-wiz/div/div/div/div[2]/div[2]/button')
        #         ))
        #         alternative_btn.click()
        #         print("Clicked alternative button (Second XPath)")
        #     except Exception as e:
        #         print(f"Could not find or click either button: {e}")


        # # paste keyword and hit search
        # try: search_box = driver.find_element(By.NAME, "q")
        # except:
        #     logger.debug(f"Google search box not found")
        #     return
        # human_typing(driver, search_box, f"{searchKey}")
        # random_pause(5, 10)

        # === Try to find 'q' or fallback to 'textarea' ===
        try:
            search_box = driver.find_element(By.NAME, "q")
            print("Found input with name='q'")
        except Exception:
            print("Input with name='q' not found. Trying to find a <textarea> instead...")
            try:
                search_box = driver.find_element(By.TAG_NAME, "textarea")
                print("Found <textarea> element")
            except Exception:
                print("Neither <input name='q'> nor <textarea> found.")
                logger.info("Google search box not found")
                return

        # If element found, click and type
        try:
            search_box.click()
            human_typing(driver, search_box, f"{searchKey}")
            random_pause(5, 10)
        except Exception as e:
            logger(f"Typing failed due to error: {e}")

        # # If element found, click and type
        # try:
        #     search_box.click()
        #     human_typing(driver, search_box, f"{searchKey}")
        #     random_pause(5, 10)
        #     # Check if the full keyword was actually typed
        #     typed_value = search_box.get_attribute("value").strip()
        #     print(typed_value)
        #     if typed_value.lower() != searchKey.lower():
        #         logger.info(f"Incomplete keyword detected: '{typed_value}'. Retyping...")
        #         # Clear the box and re-type
        #         # search_box.clear()
        #         human_typing(driver, search_box, f"{searchKey}")
        #         random_pause(3, 6)
        #         # # Double-check again
        #         # typed_value = search_box.get_attribute("value").strip()
        #         # if typed_value.lower() != searchKey.lower():
        #         #     logger.warning(f"Still incomplete after retry for keyword: {searchKey}")
        #         # else:
        #         logger.info(f"Keyword successfully retyped: {searchKey}")
        # except Exception as e:
        #     logger.info(f"Typing failed due to error: {e}")

        if "https://www.google.com/sorry/index" in driver.current_url:
            logger.debug(f"Captcha Detected")
            return
        # # Check for captcha page
        # while True:
        #     if "https://www.google.com/sorry/index" in driver.current_url:
        #         logger.debug(f"Captcha Detected, Waiting to be resolved manually")
        #         random_pause(10, 20)
        #     else: break
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
            random_pause(2, 4)
            scroll_page(driver)
            random_pause(2, 4)
            try:
                # google main right side box
                try: googleMainRightSide = main.find_element(By.XPATH, '//*[@id="rhs"]/div/div/div[2]/div/div/div/div[2]')
                except:
                    try: googleMainRightSide = main.find_element(By.CSS_SELECTOR, 'div#rhs div.osrp-blk')
                    except: googleMainRightSide = None
                if googleMainRightSide is None:
                    logger.debug(f"Right side box not found ({searchKey}).")
                    setProductRightSideStatus(productID, status="1")
                else:
                    try:
                        try: findingButton = googleMainRightSide.find_element(By.CSS_SELECTOR, 'div[data-oopc="DESKTOP_RHS"]')
                        except Exception as e:
                            findingButton = None
                        
                        if findingButton is None:
                            try: rightSideBox = googleMainRightSide.find_element(By.XPATH, '//*[@id="jobWhd"]/div/div/div/div/div/div/div/div/div[3]')
                            except: rightSideBox = None
                            # Find the `compare prices` button
                            try: comparePricesButton = rightSideBox.find_element(By.CSS_SELECTOR, 'div.J8Ur2b > div > div > div > div:nth-child(2) > div.M8PXde > button.UHCRod')
                            except:
                                comparePricesButton = None
                        else:
                            try: comparePricesButton = WebDriverWait(findingButton, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button")))
                            except Exception as e:
                                comparePricesButton = None
                               
                        # check `compare prices` button found or not
                        if comparePricesButton is None:
                            logger.debug(f"`compare prices` button not found ({searchKey}).")
                        else:
                            random_pause(2, 4)
                            comparePricesButton.click()
                            random_pause(4, 6)
                            scroll_page(driver)
                            random_pause(4, 6)
                            # table in competitors popup
                            try:
                                mainTable = driver.find_element(By.CSS_SELECTOR, 'div.ejwGBd > div > table[aria-label="Grid of sellers for this product."]')
                            except:
                                try: mainTable = driver.find_element(By.CSS_SELECTOR, 'div.ejwGBd > div > table')
                                except: mainTable = None
                            
                            if mainTable == None:
                                logger.error("Table in popup not found.")
                            else:
                                try: tableInPopUp = mainTable.find_elements(By.CSS_SELECTOR, 'tbody.L66lOd > tr')
                                except: tableInPopUp = None
                            
                            if tableInPopUp is None:
                                logger.error("<tbody> in popup not found.")
                            else:
                                # more offers button
                                try: moreOffersButtton = mainTable.find_element(By.XPATH, '..').find_element(By.CSS_SELECTOR, 'button')
                                except Exception as e: moreOffersButtton = None
                                # click the button to view more vendors in the list
                                if moreOffersButtton is not None: moreOffersButtton.click()
                                random_pause(4, 6)
                                # check if `more offers` button still there
                                try: greatGrandDiv = mainTable.find_element(By.XPATH, '../../..')
                                except Exception as e: greatGrandDiv = None
                                if greatGrandDiv is not None:
                                    while True:
                                        try: moreMoreOffersButtton = greatGrandDiv.find_element(By.CSS_SELECTOR, 'div.ejwGBd button')
                                        except: moreMoreOffersButtton = None
                                        if moreMoreOffersButtton is None: break
                                        else: moreMoreOffersButtton.click()
                                        random_pause(4, 6)
                                random_pause(4, 6)
                                # re-scraping the table rows 
                                try: tableInPopUp = mainTable.find_elements(By.CSS_SELECTOR, 'tbody.L66lOd > tr')
                                except: pass

                                row, total_competitors, competitors_lst, vendor_wise_suspicious = 1, {}, [], {}
                                for tr in tableInPopUp:
                                    temp = {}
                                    # finding td's
                                    try: td = tr.find_element(By.CSS_SELECTOR, 'td:nth-child(5)')
                                    except: td = None
                                    if td is None:
                                        logger.debug("table <td> not found.")
                                    else:
                                        # vendor product url
                                        try: competitor_url = tr.find_elements(By.CSS_SELECTOR, 'td')[-1].find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                                        except Exception as e:
                                            try: competitor_url = td.find_element(By.CSS_SELECTOR, 'a.P9159d.hMk97e.BbI1ub').get_attribute('href')
                                            except Exception as e: competitor_url = None
                                        # refining product url
                                        if competitor_url is not None:
                                            temp['competitor_url'] = competitor_url
                                            # vendor_website
                                            parsed_url = urlparse(temp['competitor_url'])
                                            temp['competitor_website'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"
                                        else:
                                            logger.debug(f"Skipping this vendor, unable to scrape url of the product (ID: {productID}).")
                                            continue
                                        # vendor name
                                        try: temp['competitor_name'] = tr.find_element(By.CSS_SELECTOR, 'td').text.strip()
                                        except Exception as e:
                                            try: temp['competitor_name'] = tr.find_elements(By.CSS_SELECTOR, 'td')[0].text.strip()
                                            except Exception as e:
                                                logger.debug(f"Unable to scrape vendor name, setting vendor domian name as vendor name when searched for product (ID: {productID}).")
                                                parsed_url = urlparse(temp['competitor_url'])
                                                temp['competitor_name']  = f"{parsed_url.netloc}"
                                        # vendorprice_offers
                                        try:
                                            price_offers = tr.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > div.PV5tLb > div').text.strip()
                                            temp['vendorprice_offers'] = price_offers
                                        except:
                                            temp['vendorprice_offers'] = None
                                        # offers section
                                        try:
                                            offers_cell = mainTable.find_elements(By.CSS_SELECTOR, f'tbody.L66lOd > tr:nth-child({row}) > td')[2].find_element(By.CSS_SELECTOR, 'div > div')
                                            # delivery_text, vendorprice_return, vendorprice_offers
                                            delivery_return = offers_cell.find_elements(By.CSS_SELECTOR, 'div.Z8dN6c')
                                            if len(delivery_return) > 0:
                                                if len(delivery_return) > 1:
                                                    temp['delivery_text'] = delivery_return[0].text
                                                    temp['vendorprice_return'] = delivery_return[1].text.replace("·", "")
                                                    temp['vendorprice_offers'] = delivery_return[0].text +'\n'+ delivery_return[1].text.replace("·", "")
                                                else:
                                                    temp['vendorprice_offers'] = delivery_return[0].text.replace("·", "")
                                                    if 'return' in delivery_return[0].text:
                                                        temp['vendorprice_return'] = delivery_return[0].text.replace("·", "")
                                                        temp['delivery_text'] = None
                                                    else:
                                                        temp['vendorprice_return'] = None
                                                        temp['delivery_text'] = delivery_return[0].text
                                            else:
                                                temp['delivery_text'] = None
                                                temp['vendorprice_return'] = None
                                                temp['vendorprice_offers'] = None
                                            # vendorprice_delivery_date
                                            temp['vendorprice_delivery_date'], daysToDeliver = None, 0
                                            if  temp['delivery_text'] != None:
                                                try:
                                                    if 'by' in temp['delivery_text']: deliveryDateTemp = temp['delivery_text'].rsplit('by')[1].strip()
                                                    elif 'delivery' in temp['delivery_text']: deliveryDateTemp = temp['delivery_text'].rsplit('delivery')[1].strip()
                                                    else: deliveryDateTemp = None
                                                except Exception as e: deliveryDateTemp = None
                                                # date text extracted
                                                if deliveryDateTemp != None:
                                                    # adding current year
                                                    today = date.today()
                                                    datetime_str = f'{deliveryDateTemp}, {today.year}'
                                                    try: vendorprice_delivery_date = datetime.strptime(datetime_str, "%B %d, %Y").date().strftime("%Y-%m-%d")
                                                    except:
                                                        try: vendorprice_delivery_date = datetime.strptime(datetime_str, "%b %d, %Y").date().strftime("%Y-%m-%d")
                                                        except Exception as e: vendorprice_delivery_date = None
                                                    # if date is formatted
                                                    if vendorprice_delivery_date != None:
                                                        today_date = datetime.now().strftime("%Y-%m-%d")
                                                        # Next year date
                                                        if today_date > vendorprice_delivery_date:
                                                            vendorprice_delivery_date_date = datetime.strptime(vendorprice_delivery_date, "%Y-%m-%d").date()
                                                            year_later = vendorprice_delivery_date_date.replace(year=vendorprice_delivery_date_date.year+1)
                                                            vendorprice_delivery_date = year_later.strftime("%Y-%m-%d")
                                                            # days to deliver
                                                            daysToDeliver = (datetime.strptime(vendorprice_delivery_date, "%Y-%m-%d").date() - datetime.strptime(today_date, "%Y-%m-%d").date()).days
                                                    temp['vendorprice_delivery_date'] = vendorprice_delivery_date
                                            # vendorprice_isbackorder
                                            if daysToDeliver > 28:
                                                temp['vendorprice_isbackorder'] = 'yes'
                                            else:
                                                temp['vendorprice_isbackorder'] = 'no'
                                            # vendorprice_stock_text
                                            stock_product_condition = offers_cell.find_elements(By.CSS_SELECTOR, 'div.OaQPmf.rArxUc')
                                            if len(stock_product_condition) > 0:
                                                if len(stock_product_condition) > 1:
                                                    temp['vendorprice_stock_text'] = stock_product_condition[0].text
                                                    temp['vendorprice_extra_discount'] = (match.group(1)) if (match := re.search(r"([\d.]+)%\s*off", stock_product_condition[1].text, re.I)) else None
                                                else:
                                                    if 'stock' in stock_product_condition[0].text or 'online' in stock_product_condition[0].text:
                                                        temp['vendorprice_stock_text'] = stock_product_condition[0].text
                                                        temp['vendorprice_extra_discount'] = "0.00"
                                                    else:
                                                        temp['vendorprice_stock_text'] = None
                                                        temp['vendorprice_extra_discount'] = "0.00"
                                            else:
                                                temp['vendorprice_stock_text'] = None
                                                temp['vendorprice_extra_discount'] = "0.00"
                                        except Exception as e:
                                            temp['vendorprice_stock_text'], temp['vendorprice_extra_discount'] = None, "0.00"
                                            temp['delivery_text'], temp['vendorprice_return'] = None, None
                                            temp['vendorprice_offers'], temp['vendorprice_delivery_date'] = None, None
                                            temp['vendorprice_isbackorder'] = 'no'
                                        # source
                                        temp['source'] = 'google_main_searched'
                                        # product_condition
                                        temp['product_condition'] = 'New'
                                        # scrap prices
                                        try:
                                            pricing_td = mainTable.find_elements(By.CSS_SELECTOR, f'tbody.L66lOd > tr:nth-child({row}) > td')[-2]
                                            pricing_td_trs = pricing_td.find_elements(By.CSS_SELECTOR, 'tr')
                                            for tr_inner in pricing_td_trs:
                                                tr_inner_tds = tr_inner.find_elements(By.CSS_SELECTOR, 'td')
                                                if len(tr_inner_tds) == 2:
                                                    label = str(tr_inner_tds[0].get_attribute('innerHTML')).strip()
                                                    try: value = str(tr_inner_tds[1].find_element(By.CSS_SELECTOR, 'span').get_attribute('innerHTML')).strip()
                                                    except: value = str(tr_inner_tds[1].get_attribute('innerHTML')).strip()
                                                    if 'item price' in label.lower():
                                                        tempPrice = value.split('$')[-1]
                                                        temp['vendorprice_price'] = removeComma(tempPrice)
                                                    elif 'delivery' in label.lower():
                                                        if 'free' in value.lower():
                                                            temp['vendorprice_shipping'] = 0.00
                                                        else:
                                                            tempPrice = value.split('$')[-1]
                                                            temp['vendorprice_shipping'] = removeComma(tempPrice)
                                            # if shipping not found
                                            if 'vendorprice_shipping' not in temp:
                                                temp['vendorprice_shipping'] = None
                                                
                                            # Apply extra discount
                                            discount = temp.get('vendorprice_extra_discount')
                                            try:
                                                price = temp.get('vendorprice_price')
                                                discount_value = float(discount)
                                                if discount_value != 0.00:
                                                    discounted_price = price - (price * discount_value / 100)
                                                    temp['vendorprice_finalprice'] = round(discounted_price, 2)
                                                else:
                                                    temp['vendorprice_finalprice'] = price
                                            except Exception:
                                                temp['vendorprice_finalprice'] = temp.get('vendorprice_price', 0.00)

                                            # # add shipping to the discounted price
                                            # try:
                                            #     shipping = temp.get('vendorprice_shipping', 0.00)
                                            #     if shipping is not None:
                                            #         temp['vendorprice_finalprice'] = round(temp['vendorprice_finalprice'] + shipping, 2)
                                            # except Exception:
                                            #     pass
                                            
                                            # to save total competitors
                                            if temp['product_condition'] == 'New':
                                                competitor_website = temp['competitor_website']
                                                if competitor_website in total_competitors.keys():
                                                    total_competitors[competitor_website] = int(total_competitors[competitor_website]) + 1
                                                else:
                                                    total_competitors[competitor_website] = 1
                                            # checking if existing vendor
                                            for val in data:
                                                if temp['competitor_website'] in val['vendor_website']:
                                                    temp['existing'] = {
                                                        'vendor_id': val['vendor_id'],
                                                        'vendor_name': val['vendor_name'],
                                                        'vendor_website': val['vendor_website'],
                                                        'vendor_product_id': val['vendor_product_id'],
                                                        'vendor_url': val['vendor_url']
                                                    }
                                            # collecting competitors
                                            competitors_lst.append(temp)
                                            
                                            # === Once all vendors are appended to finalData, assign rank ===
                                            # Sort vendors based on final price
                                            sorted_vendors = sorted(competitors_lst, key=lambda x: x['vendorprice_finalprice'])
                                            # Assign rank: even if price is the same, assign increasing rank (1, 2, 3...)
                                            for index, item in enumerate(sorted_vendors):
                                                item['rank'] = index + 1
                                            # Optional: reassign sorted list back to finalData (if needed)
                                            competitors_lst = sorted_vendors
                                            # print(competitors_lst)
                                            
                                            # vendor wise suspicious
                                            competitor_website = temp['competitor_website']
                                            if competitor_website in vendor_wise_suspicious.keys():
                                                vendor_wise_suspicious[competitor_website] = int(vendor_wise_suspicious[competitor_website]) + 1
                                            else:
                                                vendor_wise_suspicious[competitor_website] = 1
                                        except Exception as e:
                                            logger.debug(f"Unable to scrap prices, Exception is coming. {e}")
                                    row += 1
                                # save total competitors
                                total_competitors = len(list(filter(lambda v: v == 1, total_competitors.values())))
                                savePricingData(productID, competitors_lst, total_competitors, vendor_wise_suspicious)
                                # generate ranking
                                # for vendor in data:
                                evalRanking(vendorID, productID)
                    except Exception as e:
                        if 'element click intercepted' in str(e) or 'is not clickable at point' in str(e):
                            logger.debug("Unable to click, re-trying")
                            atmpt += 1
                            if atmpt < 4: googleMainRightSideBox(searchKey, productID, atmpt)
                            else: logger.debug(f"Failed in all attempts (3/3)")
                        else:
                            logger.debug(f"Google main right side inner box not found, Exception >> {e}")
            except Exception as e:
                if 'element click intercepted' in str(e) or 'is not clickable at point' in str(e):
                    driver.quit()
                    driver.service.stop()
                    logger.debug("Unable to click, re-trying")
                    atmpt += 1
                    if atmpt < 4: googleMainRightSideBox(searchKey, productID, atmpt)
                    else: logger.debug(f"Failed in all attempts (3/3)")
                else:
                    logger.debug(f"Google main right side box not found, Exception >> {e}")
    except Exception as e:
        if 'element click intercepted' in str(e) or 'is not clickable at point' in str(e):
            driver.quit()
            driver.service.stop()
            logger.debug("Unable to click, re-trying")
            atmpt += 1
            if atmpt < 4: googleMainRightSideBox(searchKey, productID, atmpt)
            else: logger.debug(f"Failed in all attempts (3/3)")
        else:
            logger.debug(f"googleMainRightSideBox >> {e}")
    finally:
        driver.quit()
        driver.service.stop()

def setProductRightSideStatus(productID, status):
    print("================================")
    print(productID, status)
    try:
        print("in try")
        conn = mysql.connector.connect(host=HOST, database=DB, user=USER, password=PASS)
        cursor = conn.cursor()
        # Check if product_id exists
        cursor.execute("SELECT is_found_google_right_side FROM ProductRightSideStatus WHERE product_id = %s", (productID,))
        result = cursor.fetchone()
        if result:
            print(f"result found {result}")
            current_status = result[0]
            if status == 0:
                print(f"status in if {status}")
                # Update to 0 only if different
                if current_status != 0:
                    cursor.execute("""
                        UPDATE ProductRightSideStatus
                        SET is_found_google_right_side = 0
                        WHERE product_id = %s
                    """, (productID,))
                    conn.commit()
                    logger.debug(f"Updated Product ID {productID} → is_found_google_right_side=0")
                    # return "updated_to_0"
                else:
                    logger.debug(f"Product ID {productID} already has status 0 → no update needed")
                    # return "already_0"

            elif status == 1:
                print(f"status in else {status}")
                # Determine new status
                if current_status == 0:
                    print(current_status)
                    new_status = 1
                elif current_status == 1:
                    new_status = 2
                else:
                    new_status = current_status
                print(new_status)
                cursor.execute("""UPDATE ProductRightSideStatus SET is_found_google_right_side = %s WHERE product_id = %s
                """, (new_status, productID))
                conn.commit()
                logger.debug(f"Updated Product ID {productID} → is_found_google_right_side={new_status}")
                # return f"updated_to_{new_status}"
        else:
            # No record found — insert new one
            cursor.execute("""INSERT INTO ProductRightSideStatus (product_id, is_found_google_right_side) VALUES (%s, %s)
            """, (productID, status))
            conn.commit()
            logger.debug(f"Inserted new ProductRightSideStatus(product_id={productID}, is_found_google_right_side={status})")
            # return f"inserted_with_{status}"

    except Exception as e:
        logger.error(f"Error in setProductRightSideStatus >> {e}")
        # return "error"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Removing comma from price
def removeComma(value):

    strValue = str(value).strip()
    if "," in strValue:
        newStrValue = strValue.replace(',', '')
        newStrValue = newStrValue.replace(' ', '')
        finalValue =  float(newStrValue)
        finalValue = format(finalValue, '.2f')
    else:
        finalValue =  float(strValue)
        finalValue = format(finalValue, '.2f')
    return float(finalValue)

# save pricing data
def savePricingData(product_id, competitors_lst, competitor_count, vendor_wise_suspicious, atmpt=1):
    try:
        conn = mysql.connector.connect(host=HOST, database=DB, user=USER, password=PASS)
        if conn.is_connected():
            this = conn.cursor()
            scrapedProductCounted = False
            for temp in competitors_lst:
                is_suspicious = '1' if vendor_wise_suspicious[temp['competitor_website']] > 1 else '0'
                # product url
                productRawURL = temp['competitor_url']
                if '?' in productRawURL: productURL = productRawURL.split("?")[0]
                elif '&' in productRawURL: productURL = productRawURL.split("&")[0]
                else: productURL = productRawURL
                # vendor website
                vendor_website = temp['competitor_website']
                # check if competitor is existing or not
                if 'existing' in temp:
                    print("\n>>>>> EXISTING <<<<<")

                    vendor_id = temp['existing']['vendor_id']
                    vendor_name = temp['existing']['vendor_name']
                    vendor_product_id = temp['existing']['vendor_product_id']
                else:
                    print("\n>>>>> NEW <<<<<")

                    # check if vendor already exist
                    this.execute("SELECT vendor_id, vendor_name FROM Vendor WHERE vendor_website = %s LIMIT 1;", (vendor_website,))
                    record = this.fetchone()
                    if record:
                        vendor_id, vendor_name = record
                        logger.debug(f"Found existing vendor: {vendor_name} (ID: {vendor_id})")
                    else:
                        this.execute("INSERT INTO Vendor (vendor_name, vendor_website) VALUES (%s, %s);", (temp['competitor_name'], vendor_website))
                        conn.commit()
                        vendor_id = this.lastrowid
                        logger.debug(f"Added new vendor: {temp['competitor_name']} (ID: {vendor_id})")
                    # check vendor and product mapping
                    this.execute("SELECT vendor_product_id FROM ProductVendor WHERE vendor_id = %s AND product_id = %s LIMIT 1;", (vendor_id, product_id))
                    record2 = this.fetchone()
                    if record2:
                        vendor_product_id = record2[0]
                        logger.debug(f"Mapping already exist: Vendor (ID: {vendor_id}) x Product (ID: {product_id})")
                    else:
                        this.execute("INSERT INTO ProductVendor (vendor_id, product_id) VALUES (%s, %s);", (vendor_id, product_id))
                        conn.commit()
                        vendor_product_id = this.lastrowid
                        logger.debug(f"Mapped Vendor (ID: {vendor_id}) x Product (ID: {product_id})")
                    # check,insert/update product url of competitors
                    this.execute('SELECT vendor_url_id FROM VendorURL WHERE vendor_product_id = %s;', (vendor_product_id,))
                    product_url_result = this.fetchall()
                    if not product_url_result:
                        this.execute(
                            "INSERT INTO VendorURL (vendor_product_id, vendor_raw_url, vendor_url) VALUES (%s, %s, %s)",
                            (vendor_product_id, productRawURL, productURL)
                        )
                        conn.commit()
                        logger.info(f"Inserted vendor_url for vendor_product_id={vendor_product_id}, inserted_id={this.lastrowid}")
                    else:
                        logger.info(f"Vendor URL already exists for vendor_product_id={vendor_product_id}, existing_ids={product_url_result}")
                        # this.execute("UPDATE VendorURL SET vendor_raw_url = %s, vendor_url = %s WHERE vendor_product_id = %s", (productRawURL, productURL, vendor_product_id))
                        # conn.commit()
                if vendor_id == 10021:
                    # Try to find shipping cost from ShippingType
                    this.execute("""
                        SELECT shipping_value
                        FROM ShippingType
                        INNER JOIN ErpData ON ErpData.shipping_type = ShippingType.shipping_code
                        WHERE vendor_product_id = %s
                        LIMIT 1;
                    """, (vendor_product_id,))
                    result = this.fetchone()
                    if result and result[0] is not None:
                        shipping_value = result[0]
                        shipping_cost = float(removeComma(shipping_value))
                        vendorprice_finalprice = round(temp['vendorprice_finalprice'] + shipping_cost, 2)
                    else:
                        raw_shipping = temp.get('vendorprice_shipping')
                        if raw_shipping is not None:
                            shipping_cost = float(removeComma(raw_shipping))
                            vendorprice_finalprice = round(temp['vendorprice_finalprice'] + shipping_cost, 2)
                else:
                    # For other vendors, add shipping to final price
                    try:
                        shipping_value = temp.get('vendorprice_shipping')
                        if shipping_value is not None:
                            shipping_cost = float(removeComma(shipping_value))
                            vendorprice_finalprice = round(temp['vendorprice_finalprice'] + shipping_cost, 2)
                    except Exception as e:
                        logger.warning(f"Could not apply shipping to final price: {e}")
                
                # Checking manual price update
                this.execute(
                    "SELECT manual_price_update_date, manual_price_time_period,is_price_manually_verified,vendorprice_finalprice as db_vendorprice_finalprice,vendor_pricing_id FROM TempVendorPricing WHERE vendor_product_id = %s AND source = %s LIMIT 1",
                    (vendor_product_id, temp['source'])
                )
                record = this.fetchone()
                vendorprice_date = datetime.now().strftime("%Y-%m-%d")
                
                if record:
                    manual_price_update_date, manual_price_time_period, is_price_manually_verified, db_vendorprice_finalprice, vendor_pricing_id = record
                    current_date = datetime.now().date()
                    
                    if str(is_price_manually_verified) == '1':
                        is_suspicious = '0'

                    if manual_price_update_date is not None:
                        if isinstance(manual_price_update_date, str):
                            manual_price_update_date = datetime.strptime(manual_price_update_date, "%Y-%m-%d").date()
                        
                        day_difference = (current_date - manual_price_update_date).days
                        print(f"================ day_difference >> {day_difference} =================")
                        
                        if manual_price_time_period is not None and isinstance(manual_price_time_period, int):
                            if day_difference <= manual_price_time_period:
                                logger.info(f"Skipping update for vendor_product_id ({vendor_product_id}) as it's within the allowed time period.")
                                continue
                    else:
                        print("manual_price_update_date is None")

                    if db_vendorprice_finalprice is not None:
                        db_price = Decimal(str(db_vendorprice_finalprice)).quantize(Decimal("0.01"))
                        scraped_price = Decimal(str(vendorprice_finalprice)).quantize(Decimal("0.01"))

                        if str(is_price_manually_verified) == '1' and db_price == scraped_price:
                            try:
                                this.execute("""
                                    UPDATE TempVendorPricing
                                    SET vendorprice_date = %s
                                    WHERE vendor_pricing_id = %s;
                                """, (vendorprice_date, vendor_pricing_id))
                                conn.commit()
                                logger.info(f"Only vendorprice_date updated for vendor_pricing_id ({vendor_pricing_id}) - vendor_product_id ({vendor_product_id}) x source ({temp['source']})")
                            except Exception as e:
                                logger.error(f"Date-only update failed >> {e}")
                            continue
                        else:
                            is_price_manually_verified = '0'
                    else:
                        is_price_manually_verified = '0'
                else:
                    print("Not found manual_price_update_date and manual_price_time_period.") 
                    is_price_manually_verified = '0'
                
                if temp.get('vendorprice_extra_discount') is None:
                    temp['vendorprice_extra_discount'] = 0.00
                
                # insert pricing info
                vendorprice_date = datetime.now().strftime("%Y-%m-%d")
                this.execute("""
                    SELECT
                        vendor_pricing_id,
                        marked_as_unmatched,
                        raw_product_url,
                        product_url,
                        approved_as_correct_product
                    FROM TempVendorPricing
                    WHERE
                        vendor_product_id = %s
                        AND source = %s;
                """, (vendor_product_id, temp['source']))
                record3 = this.fetchall()
                if len(record3) > 0:
                    update_suspicous, skip, vendor_pricing_id_to_update, approved_as_correct_product = False, False, 0, False
                    for row in record3:
                        vendor_pricing_id, marked_as_unmatched, raw_product_url, product_url_from_db, approved_as_correct_product_db = row
                        # check if product url is not saved
                        if product_url_from_db != None and product_url_from_db != '':
                            product_url_from_db_2 = replace_special_chars(product_url_from_db.strip())
                            url_in_current = replace_special_chars(productURL.strip())
                            # check if current iteration vendor's product url matched with product URL in DB
                            if url_in_current in product_url_from_db_2:
                                update_suspicous, vendor_pricing_id_to_update = True, vendor_pricing_id
                                if marked_as_unmatched == '1':
                                    skip = True
                                if approved_as_correct_product_db == '1':
                                    approved_as_correct_product = True
                                break
                        else:
                            update_suspicous, vendor_pricing_id_to_update = True, vendor_pricing_id
                            if approved_as_correct_product_db == '1':
                                approved_as_correct_product = True
                            break
                    # skip products that are marked as unmatched
                    if not skip:
                        if update_suspicous:
                            try:
                                if approved_as_correct_product:
                                    is_suspicious = '0'
                                    this.execute("""
                                        UPDATE TempVendorPricing
                                        SET
                                            vendorprice_price = %s, vendorprice_finalprice = %s, vendorprice_date = %s, vendorprice_shipping = %s,
                                            vendorprice_return = %s, vendorprice_stock_text = %s, vendorprice_isbackorder = %s, vendorprice_offers = %s,
                                            vendorprice_delivery_date = %s, delivery_text = %s, vendorprice_extra_discount = %s, rank = %s, product_condition = %s,
                                            is_suspicious = %s, competitor_count = %s, scraped_by_system = %s
                                        WHERE
                                            vendor_pricing_id = %s;
                                    """, (
                                        temp['vendorprice_price'], vendorprice_finalprice, vendorprice_date, shipping_cost,
                                        temp['vendorprice_return'], temp['vendorprice_stock_text'], temp['vendorprice_isbackorder'], temp['vendorprice_offers'],
                                        temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['product_condition'], 
                                        is_suspicious, competitor_count, scraped_by_system, vendor_pricing_id_to_update
                                    ))
                                else:
                                    this.execute("""
                                        UPDATE TempVendorPricing
                                        SET
                                            vendorprice_price = %s, vendorprice_finalprice = %s, vendorprice_date = %s, vendorprice_shipping = %s,
                                            vendorprice_return = %s, vendorprice_stock_text = %s, vendorprice_isbackorder = %s, vendorprice_offers = %s,
                                            vendorprice_delivery_date = %s, delivery_text = %s, vendorprice_extra_discount = %s, rank = %s, product_condition = %s, 
                                            is_suspicious = %s, competitor_count = %s, raw_product_url = %s, product_url = %s, scraped_by_system = %s
                                        WHERE
                                            vendor_pricing_id = %s;
                                    """, (
                                        temp['vendorprice_price'], vendorprice_finalprice, vendorprice_date, shipping_cost,
                                        temp['vendorprice_return'], temp['vendorprice_stock_text'], temp['vendorprice_isbackorder'], temp['vendorprice_offers'],
                                        temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['product_condition'], is_suspicious, competitor_count,
                                        productRawURL, productURL, scraped_by_system, vendor_pricing_id_to_update
                                    ))
                                conn.commit()
                                # Saving today's scraped products
                                if not scrapedProductCounted:
                                    if this.rowcount > 0:
                                        currentDayScraped(product_id)
                                        scrapedProductCounted = True
                                if is_suspicious == '1':
                                    logger.debug(f"Pricing info updated, vendor_pricing_id ({vendor_pricing_id_to_update}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']}) x SUSPICIOUS")
                                else:
                                    logger.debug(f"Pricing info updated, vendor_pricing_id ({vendor_pricing_id_to_update}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']})")
                            except Exception as e:
                                logger.debug(f"Suspicious Vendors - Update >> {e}")
                        else:
                            try:
                                # inserting, if url not matched
                                this.execute("""
                                    INSERT INTO TempVendorPricing (
                                        vendor_product_id, vendorprice_price, vendorprice_finalprice, vendorprice_date, vendorprice_shipping, vendorprice_return,
                                        vendorprice_stock_text, vendorprice_isbackorder, vendorprice_offers, vendorprice_delivery_date, delivery_text, vendorprice_extra_discount, 
                                        rank, source, product_condition, is_suspicious, competitor_count, raw_product_url, product_url, scraped_by_system
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                                """, (
                                    vendor_product_id, temp['vendorprice_price'],  vendorprice_finalprice, vendorprice_date,  shipping_cost, 
                                    temp['vendorprice_return'],  temp['vendorprice_stock_text'],  temp['vendorprice_isbackorder'],  temp['vendorprice_offers'],
                                    temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['source'], temp['product_condition'], is_suspicious,
                                    competitor_count, productRawURL, productURL, scraped_by_system
                                ))
                                conn.commit()
                                vendor_pricing_id = this.lastrowid
                                # Saving today's scraped products
                                if not scrapedProductCounted:
                                    if this.rowcount > 0:
                                        currentDayScraped(product_id)
                                        scrapedProductCounted = True
                                if is_suspicious == '1':
                                    logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']}) x SUSPICIOUS")
                                else:
                                    logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']})")
                            except Exception as e:
                                print(f"Suspicious Vendors - Insert(1) >> {e}")
                else:
                    # try:
                    #     # inserting, as there is no record of current vendor in DB
                    #     this.execute("""
                    #         INSERT INTO TempVendorPricing (
                    #             vendor_product_id, vendorprice_price, vendorprice_finalprice, vendorprice_date, vendorprice_shipping, vendorprice_return,
                    #             vendorprice_stock_text, vendorprice_isbackorder, vendorprice_offers, vendorprice_delivery_date, delivery_text, vendorprice_extra_discount, 
                    #             rank, source, product_condition, is_suspicious, competitor_count, raw_product_url, product_url, scraped_by_system
                    #         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    #     """, (
                    #         vendor_product_id, temp['vendorprice_price'],  vendorprice_finalprice,  vendorprice_date,  shipping_cost, 
                    #         temp['vendorprice_return'],  temp['vendorprice_stock_text'],  temp['vendorprice_isbackorder'],  temp['vendorprice_offers'],
                    #         temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['source'], temp['product_condition'], is_suspicious,
                    #         competitor_count, productRawURL, productURL, scraped_by_system
                    #     ))
                    #     conn.commit()
                    #     vendor_pricing_id = this.lastrowid
                    #     # Saving today's scraped products
                    #     if not scrapedProductCounted:
                    #         if this.rowcount > 0:
                    #             currentDayScraped(product_id)
                    #             scrapedProductCounted = True
                    #     if is_suspicious == '1':
                    #         logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']}) x SUSPICIOUS")
                    #     else:
                    #         logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']})")
                    # except Exception as e:
                    #     print(f"Suspicious Vendors - Insert(2) >> {e}")
                    

                    ############ Remove later ############
                    this.execute("""
                        SELECT
                            vendor_pricing_id,
                            marked_as_unmatched,
                            raw_product_url,
                            product_url,
                            approved_as_correct_product
                        FROM TempVendorPricing
                        WHERE
                            vendor_product_id = %s
                            AND source = %s;
                    """, (vendor_product_id, 'searched'))
                    record4 = this.fetchall()
                    if len(record4) > 0:
                        update_suspicous, skip, vendor_pricing_id_to_update, approved_as_correct_product = False, False, 0, False
                        for row in record4:
                            vendor_pricing_id, marked_as_unmatched, raw_product_url, product_url_from_db, approved_as_correct_product_db = row
                            # check if product url is not saved
                            if product_url_from_db != None and product_url_from_db != '':
                                product_url_from_db_2 = replace_special_chars(product_url_from_db.strip())
                                url_in_current = replace_special_chars(productURL.strip())
                                # check if current iteration vendor's product url matched with product URL in DB
                                if url_in_current in product_url_from_db_2:
                                    update_suspicous, vendor_pricing_id_to_update = True, vendor_pricing_id
                                    if marked_as_unmatched == '1':
                                        skip = True
                                    if approved_as_correct_product_db == '1':
                                        approved_as_correct_product = True
                                    break
                            else:
                                update_suspicous, vendor_pricing_id_to_update = True, vendor_pricing_id
                                if approved_as_correct_product_db == '1':
                                    approved_as_correct_product = True
                                break
                        # skip products that are marked as unmatched
                        if not skip:
                            if update_suspicous:
                                try:
                                    if approved_as_correct_product:
                                        is_suspicious = '0'
                                        this.execute("""
                                            UPDATE TempVendorPricing
                                            SET
                                                vendorprice_price = %s, vendorprice_finalprice = %s, vendorprice_date = %s, vendorprice_shipping = %s,
                                                vendorprice_return = %s, vendorprice_stock_text = %s, vendorprice_isbackorder = %s, vendorprice_offers = %s,
                                                vendorprice_delivery_date = %s, delivery_text = %s, vendorprice_extra_discount = %s, rank = %s, product_condition = %s, source = %s, is_suspicious = %s,
                                                competitor_count = %s, scraped_by_system = %s
                                            WHERE
                                                vendor_pricing_id = %s;
                                        """, (
                                            temp['vendorprice_price'], vendorprice_finalprice, vendorprice_date, shipping_cost,
                                            temp['vendorprice_return'], temp['vendorprice_stock_text'], temp['vendorprice_isbackorder'], temp['vendorprice_offers'],
                                            temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['product_condition'], 'google_main_searched', is_suspicious,
                                            competitor_count, scraped_by_system, vendor_pricing_id_to_update
                                        ))
                                    else:
                                        this.execute("""
                                            UPDATE TempVendorPricing
                                            SET
                                                vendorprice_price = %s, vendorprice_finalprice = %s, vendorprice_date = %s, vendorprice_shipping = %s,
                                                vendorprice_return = %s, vendorprice_stock_text = %s, vendorprice_isbackorder = %s, vendorprice_offers = %s,
                                                vendorprice_delivery_date = %s, delivery_text = %s, vendorprice_extra_discount = %s, rank = %s, product_condition = %s, source = %s, is_suspicious = %s,
                                                competitor_count = %s, raw_product_url = %s, product_url = %s, scraped_by_system = %s
                                            WHERE
                                                vendor_pricing_id = %s;
                                        """, (
                                            temp['vendorprice_price'], vendorprice_finalprice, vendorprice_date, shipping_cost,
                                            temp['vendorprice_return'], temp['vendorprice_stock_text'], temp['vendorprice_isbackorder'], temp['vendorprice_offers'],
                                            temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['product_condition'], 'google_main_searched', is_suspicious, competitor_count,
                                            productRawURL, productURL, scraped_by_system, vendor_pricing_id_to_update
                                        ))
                                    conn.commit()
                                    # Saving today's scraped products
                                    if not scrapedProductCounted:
                                        if this.rowcount > 0:
                                            currentDayScraped(product_id)
                                            scrapedProductCounted = True
                                    if is_suspicious == '1':
                                        logger.debug(f"Pricing info updated, vendor_pricing_id ({vendor_pricing_id_to_update}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']}) x SUSPICIOUS")
                                    else:
                                        logger.debug(f"Pricing info updated, vendor_pricing_id ({vendor_pricing_id_to_update}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']})")
                                except Exception as e:
                                    print("Suspicious Vendors - Temp - Update >>", e)
                            else:
                                try:
                                    # inserting, if url not matched
                                    this.execute("""
                                        INSERT INTO TempVendorPricing (
                                            vendor_product_id, vendorprice_price, vendorprice_finalprice, vendorprice_date, vendorprice_shipping, vendorprice_return,
                                            vendorprice_stock_text, vendorprice_isbackorder, vendorprice_offers, vendorprice_delivery_date, delivery_text, vendorprice_extra_discount, 
                                            rank, source, product_condition, is_suspicious, competitor_count, raw_product_url, product_url, scraped_by_system
                                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                                    """, (
                                        vendor_product_id, temp['vendorprice_price'], vendorprice_finalprice,  vendorprice_date,  shipping_cost, 
                                        temp['vendorprice_return'],  temp['vendorprice_stock_text'],  temp['vendorprice_isbackorder'],  temp['vendorprice_offers'],
                                        temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['source'], temp['product_condition'], is_suspicious,
                                        competitor_count, productRawURL, productURL, scraped_by_system
                                    ))
                                    conn.commit()
                                    vendor_pricing_id = this.lastrowid
                                    # Saving today's scraped products
                                    if not scrapedProductCounted:
                                        if this.rowcount > 0:
                                            currentDayScraped(product_id)
                                            scrapedProductCounted = True
                                    if is_suspicious == '1':
                                        logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']}) x SUSPICIOUS")
                                    else:
                                        logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']})")
                                except Exception as e:
                                    print("Suspicious Vendors - Temp - Insert(1) >>", e)
                    else:
                        try:
                            # inserting, as there is no record of current vendor in DB
                            this.execute("""
                                INSERT INTO TempVendorPricing (
                                    vendor_product_id, vendorprice_price, vendorprice_finalprice, vendorprice_date, vendorprice_shipping, vendorprice_return,
                                    vendorprice_stock_text, vendorprice_isbackorder, vendorprice_offers, vendorprice_delivery_date, delivery_text, vendorprice_extra_discount, 
                                    rank, source, product_condition, is_suspicious, competitor_count, raw_product_url, product_url, scraped_by_system
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """, (
                                vendor_product_id, temp['vendorprice_price'], vendorprice_finalprice,  vendorprice_date,  shipping_cost, 
                                temp['vendorprice_return'],  temp['vendorprice_stock_text'],  temp['vendorprice_isbackorder'],  temp['vendorprice_offers'],
                                temp['vendorprice_delivery_date'], temp['delivery_text'], temp['vendorprice_extra_discount'], temp['rank'], temp['source'], temp['product_condition'], is_suspicious,
                                competitor_count, productRawURL, productURL, scraped_by_system
                            ))
                            conn.commit()
                            vendor_pricing_id = this.lastrowid
                            # Saving today's scraped products
                            if not scrapedProductCounted:
                                if this.rowcount > 0:
                                    currentDayScraped(product_id)
                                    scrapedProductCounted = True
                            if is_suspicious == '1':
                                logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']}) x SUSPICIOUS")
                            else:
                                logger.debug(f"Pricing info added, vendor_pricing_id ({vendor_pricing_id}): vendor_product_id (ID: {vendor_product_id}) x source ({temp['source']})")
                        except Exception as e:
                            print("Suspicious Vendors - Temp - Insert(2) >>", e)
                # saving history
                savePricingHistory(vendor_id, vendor_product_id, temp, vendorprice_finalprice, shipping_cost, is_suspicious, competitor_count, productRawURL, productURL)
                # # for vendor in data:
                # evalRanking(vendor_id, product_id)
    except mysql.connector.Error as e:
        if 'timeout' in str(e):
            if atmpt == 2:
                logger.error(f"MySQL ERROR savePricingData(2/2) >> {e}")
            else:
                logger.error(f"Retrying to save pricing data ({atmpt+1}/2)")
                savePricingData(product_id, competitors_lst, competitor_count, vendor_wise_suspicious, atmpt=atmpt+1)
        else:
            logger.error(f"MySQL ERROR savePricingData() >> {e}")
    finally:
        if conn.is_connected():
            this.close()
            conn.close()

def replace_special_chars(text):
    """Replace all non-alphanumeric characters with 'special' """
    return re.sub(r'[^a-zA-Z0-9]', 'special', text)

def get_table_structure(host, db, user, password, table_name):
    """Retrieve column details from a TempVendorPricing, preserving the column order."""
    try:
        conn = mysql.connector.connect(host=host, database=db, user=user, password=password)
        cursor = conn.cursor()            
        cursor.execute(f"DESCRIBE {table_name}")
        structure = [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in cursor.fetchall()]  
        # (Column Name, Column Type, NULL, Key, Default, Extra)
    except Exception as e:
        logger.error(f"Error fetching TempVendorPricing structure for {table_name}: {e}")
        structure = []
    finally:
        cursor.close()
        conn.close()
    return structure

def match_table_structure(source_structure, target_structure):
    """Find missing columns with full definitions and their correct positions."""
    target_columns = {col[0]: col for col in target_structure}  # {Column Name: Column Details}
    missing_columns = []

    for index, column in enumerate(source_structure):
        col_name, col_type, is_null, key, default, extra = column
        if col_name not in target_columns:
            after_column = source_structure[index - 1][0] if index > 0 else None
            missing_columns.append((col_name, col_type, is_null, key, default, extra, after_column))
    if missing_columns and len(missing_columns) > 0:
        logger.info(f"Missing columns: {missing_columns}")
    else:
        logger.info(f"History Table is up-to-date.")
    return missing_columns

def savePricingHistory(vendor_id, vendor_product_id, data, vendorprice_finalprice, shipping_cost, is_suspicious, competitor_count, product_raw_url, product_url):
    """
    Insert pricing data into vendor specific vendorPricing DB
    """
    try:
        # save to AF/HP if vendor_id is one of them
        if vendor_id == 10021 or vendor_id == 10024: conn = mysql.connector.connect(host=HOST2, database=DB2, user=USER2, password=PASS2)
        else: conn = mysql.connector.connect(host=HOST3, database=DB3, user=USER3, password=PASS3)
        if conn.is_connected():
            this = conn.cursor()
            # check if vendor specific vendorPricing table exists or not
            vendor_pricing_table = f"z_{vendor_id}_VendorPricing"
            this.execute(f"""SELECT *
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = '{vendor_pricing_table}'
            LIMIT 1""")
            result = this.fetchone()
            source_structure = get_table_structure(HOST, DB, USER, PASS, 'TempVendorPricing')
            if not result:
                logger.info(f"Table {vendor_pricing_table} does not exist. Creating table...")
                column_definitions = []
                primary_key = None  # Store primary key column if exists
                for col_name, col_type, is_null, key, default, extra in source_structure:
                    null_option = "NULL" if is_null == "YES" else "NOT NULL"
                    # Handle default values properly
                    if default is not None:
                        if "timestamp" in col_type.lower() or "datetime" in col_type.lower():
                            default_option = "DEFAULT CURRENT_TIMESTAMP" if default.lower() == "current_timestamp()" else ""
                        else:
                            default_option = f"DEFAULT {repr(default)}"
                    else:
                        default_option = ""
                    extra_option = extra if extra else ""
                    # Ensure AUTO_INCREMENT is properly handled
                    if "auto_increment" in extra.lower():
                        extra_option = "AUTO_INCREMENT"
                        primary_key = col_name  # Store primary key
                    column_definitions.append(f"`{col_name}` {col_type} {null_option} {default_option} {extra_option}")
                create_table_query = f"""
                    CREATE TABLE `{vendor_pricing_table}` (
                        {', '.join(column_definitions)}
                        {f", PRIMARY KEY (`{primary_key}`)" if primary_key else ""}
                    );
                """.strip()
                this.execute(create_table_query)
                conn.commit()
                logger.info(f"Table {vendor_pricing_table} created successfully.")
                logger.info(f"====================================================")
            else:
                if vendor_id == 10021 or vendor_id == 10024:
                    target_structure = get_table_structure(HOST2, DB2, USER2, PASS2, vendor_pricing_table)
                else:
                    target_structure = get_table_structure(HOST3, DB3, USER3, PASS3, vendor_pricing_table)
                missing_columns = match_table_structure(source_structure, target_structure)
                if missing_columns and len(missing_columns) > 0:
                    # Add missing columns if table exists
                    for col_name, col_type, is_null, key, default, extra, after_column in missing_columns:
                        null_option = "NULL" if is_null == "YES" else "NOT NULL"
                        # Handle default values properly
                        if default is not None:
                            if "timestamp" in col_type.lower() or "datetime" in col_type.lower():
                                default_option = "DEFAULT CURRENT_TIMESTAMP" if default.lower() == "current_timestamp()" else ""
                            else:
                                default_option = f"DEFAULT {repr(default)}"
                        else:
                            default_option = ""
                        extra_option = extra if extra else ""
                        after_option = f"AFTER `{after_column}`" if after_column else "FIRST"
                        # Prevent adding AUTO_INCREMENT column incorrectly
                        if "auto_increment" in extra.lower():
                            logger.warning(f"Skipping column `{col_name}` because it has AUTO_INCREMENT.")
                            continue  # Do not add AUTO_INCREMENT column
                        alter_query = f"""
                            ALTER TABLE `{vendor_pricing_table}`
                            ADD COLUMN `{col_name}` {col_type} {null_option} {default_option} {extra_option} {after_option};
                        """.strip()
                        this.execute(alter_query)
                    conn.commit()
                    logger.info(f"Table {vendor_pricing_table} altered successfully.")
                    logger.info(f"==========================================")
                    
            vendorprice_date = datetime.now().strftime("%Y-%m-%d")
            # insert pricing data into vendor specific vendorPricing table
            if is_suspicious == '1':
                this.execute("""
                    INSERT INTO """+ vendor_pricing_table +""" (
                        vendor_product_id, vendorprice_price, vendorprice_finalprice, vendorprice_date, vendorprice_shipping, vendorprice_return,
                        vendorprice_stock_text, vendorprice_isbackorder, vendorprice_offers, vendorprice_delivery_date, delivery_text, vendorprice_extra_discount, 
                        rank, source, product_condition, is_suspicious, competitor_count, raw_product_url, product_url, scraped_by_system
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    vendor_product_id, data['vendorprice_price'], vendorprice_finalprice,  vendorprice_date,  shipping_cost, 
                    data['vendorprice_return'],  data['vendorprice_stock_text'],  data['vendorprice_isbackorder'],  data['vendorprice_offers'],
                    data['vendorprice_delivery_date'], data['delivery_text'], data['vendorprice_extra_discount'], data['rank'], data['source'], data['product_condition'], is_suspicious,
                    competitor_count, product_raw_url, product_url, scraped_by_system
                ))
            else:
                this.execute("""
                    INSERT INTO """+ vendor_pricing_table +""" (
                        vendor_product_id, vendorprice_price, vendorprice_finalprice, vendorprice_date, vendorprice_shipping, vendorprice_return,
                        vendorprice_stock_text, vendorprice_isbackorder, vendorprice_offers, vendorprice_delivery_date, delivery_text, vendorprice_extra_discount, 
                        rank, source, product_condition, is_suspicious, competitor_count, scraped_by_system
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    vendor_product_id, data['vendorprice_price'], vendorprice_finalprice,  vendorprice_date,  shipping_cost, 
                    data['vendorprice_return'],  data['vendorprice_stock_text'],  data['vendorprice_isbackorder'],  data['vendorprice_offers'],
                    data['vendorprice_delivery_date'], data['delivery_text'], data['vendorprice_extra_discount'], data['rank'], data['source'], data['product_condition'], is_suspicious,
                    competitor_count, scraped_by_system
                ))
            conn.commit()
            logger.debug(f"Pricing info added to history ({vendor_pricing_table})")
    except mysql.connector.Error as e:
        logger.debug(f"MySQL ERROR savePricingHistory() >> {e}")
    finally:
        if conn.is_connected():
            this.close()
            conn.close()

def setAsPicked(product_id, atmpt=1):
    """
    Marking product as picked
    """
    try:
        conn = mysql.connector.connect(host=HOST, database=DB, user=USER, password=PASS)
        if conn.is_connected():
            this = conn.cursor()
            this.execute("UPDATE Product SET is_picked_for_google_main_right = %s WHERE product_id = %s;", ('1', product_id))
            conn.commit()
            logger.debug(f"Product (ID: {product_id}) is marked as picked")

            # # Check if the product_id already exists in ProductRightSideStatus
            # this.execute(f"SELECT product_status_id FROM ProductRightSideStatus WHERE product_id = {product_id}")
            # result = this.fetchone()

            # if result:
            #     pass  # Already exists, do nothing
            # else:
            #     # Insert if not found
            #     this.execute("INSERT INTO ProductRightSideStatus (product_id) VALUES (%s)", (product_id,))
            #     conn.commit()
            #     logger.info(f"Product ID {product_id} inserted in ProductRightSideStatus table.")
            # # Saving today's processed products
            # currentDayProcessed()
    except mysql.connector.Error as e:
        if 'timeout' in str(e):
            if atmpt == 3:
                logger.error(f"MySQL ERROR setAsPicked(3/3) >> {e}")
            else:
                logger.error(f"Retrying to set product as picked ({atmpt+1}/3)")
                setAsPicked(product_id, atmpt=atmpt+1)
        else:
            logger.error(f"MySQL ERROR setAsPicked() >> {e}")
    finally:
        if conn.is_connected():
            this.close()
            conn.close()

def setAsProcessed(product_id, atmpt=1):
    """
    Marking product as processed
    """
    try:
        conn = mysql.connector.connect(host=HOST, database=DB, user=USER, password=PASS)
        if conn.is_connected():
            this = conn.cursor()
            this.execute("UPDATE Product SET is_processed_for_google_main_right = %s WHERE product_id = %s;", ('1', product_id))
            conn.commit()
            logger.debug(f"Product (ID: {product_id}) is marked as processed")
            # Saving today's processed products
            currentDayProcessed()
    except mysql.connector.Error as e:
        if 'timeout' in str(e):
            if atmpt == 3:
                logger.error(f"MySQL ERROR setAsProcessed(3/3) >> {e}")
            else:
                logger.error(f"Retrying to set product as processed ({atmpt+1}/3)")
                setAsProcessed(product_id, atmpt=atmpt+1)
        else:
            logger.error(f"MySQL ERROR setAsProcessed() >> {e}")
    finally:
        if conn.is_connected():
            this.close()
            conn.close()

def setAsScraped(product_id, atmpt=1):
    """
    Marking product as scraped
    """
    try:
        conn = mysql.connector.connect(host=HOST, database=DB, user=USER, password=PASS)
        if conn.is_connected():
            this = conn.cursor()
            this.execute("UPDATE Product SET is_scraped_for_google_main_right = %s WHERE product_id = %s;", ('1', product_id))
            conn.commit()
            logger.debug(f"Product (ID: {product_id}) is marked as scrapped")
    except mysql.connector.Error as e:
        if 'timeout' in str(e):
            if atmpt == 3:
                logger.error(f"MySQL ERROR setAsScraped(3/3) >> {e}")
            else:
                logger.error(f"Retrying to set product as scraped ({atmpt+1}/3)")
                setAsScraped(product_id, atmpt=atmpt+1)
        else:
            logger.error(f"MySQL ERROR setAsScraped() >> {e}")
    finally:
        if conn.is_connected():
            this.close()
            conn.close()

def currentDayProcessed():
    """
    Saving today's processed products
    """
    processedCountFile = f"({date.today()})processed"
    if os.path.exists(processedCountFile):
        with open(processedCountFile) as f:
            count = f.read()
        with open(processedCountFile, "w") as f:
            try: count = int(count) + 1
            except: count = 1
            f.write(str(count))
    else:
        with open(processedCountFile, "w") as f:
            f.write(str(1))

def currentDayScraped(product_id):
    """
    Saving today's scraped products
    """
    scrapedCountFile = f"({date.today()})scraped"
    if os.path.exists(scrapedCountFile):
        with open(scrapedCountFile) as f:
            count = f.read()
        with open(scrapedCountFile, "w") as f:
            try: count = int(count) + 1
            except: count = 1
            f.write(str(count))
    else:
        with open(scrapedCountFile, "w") as f:
            f.write(str(1))
    setAsScraped(product_id)
    setProductRightSideStatus(product_id, status="0")


def getKeywordFromDB():
    """
    Get Brand + MPN of products to search
    """
    try:
        conn = mysql.connector.connect(host=HOST, database=DB, user=USER, password=PASS)
        if conn.is_connected():
            this = conn.cursor()
            this.execute(f"""
            SELECT 
                DISTINCT ProductVendor.product_id
            FROM ProductVendor
            INNER JOIN Product ON Product.product_id = ProductVendor.product_id
            INNER JOIN TempVendorPricing on TempVendorPricing.vendor_product_id = ProductVendor.vendor_product_id
            INNER JOIN ErpData ON ErpData.vendor_product_id = ProductVendor.vendor_product_id
            INNER JOIN UniversalGroupMapping ON ErpData.mapping_id = UniversalGroupMapping.universal_group_mapping_id
            WHERE
                ProductVendor.vendor_id = 10021
                AND gprule_group_name_parent_id NOT IN (97)
                AND Product.is_picked_for_google_main_right = '0'
            GROUP BY ProductVendor.vendor_product_id
            HAVING SUM(source = 'google_main_searched') = 0;
            """)
            result0 = this.fetchall()
            # product_ids = result0[0] if result0 else 0
            product_ids = ','.join(str(row[0]) for row in result0)
            # get products from DB to scrap
            this.execute(f"""
                WITH Products AS (
                    SELECT
                        Brand.brand_name,
                        Product.product_mpn,
                        Product.product_id
                    FROM Product
                    INNER JOIN Brand ON Brand.brand_id = Product.brand_id
                    INNER JOIN ProductVendor ON ProductVendor.product_id = Product.product_id
                    WHERE
                        ProductVendor.vendor_id = {vendorID}
                        AND ProductVendor.product_id IN ({product_ids})
                        AND Product.is_picked_for_google_main_right = '0'
                    GROUP BY Product.product_id
                    ORDER BY Product.product_id
                    LIMIT {LIMIT}
                )

                SELECT
                    Products.brand_name,
                    Products.product_mpn,
                    Products.product_id,
                    Vendors.vendor_id,
                    Vendors.vendor_name,
                    Vendors.vendor_website,
                    ProductVendor.vendor_product_id,
                    CASE
                        WHEN VendorURL.vendor_url IS NULL OR VendorURL.vendor_url = ''
                        THEN VendorURL.vendor_raw_url
                        ELSE VendorURL.vendor_url
                    END AS vendor_url
                FROM Products
                INNER JOIN ProductVendor ON ProductVendor.product_id = Products.product_id
                LEFT JOIN VendorURL ON VendorURL.vendor_product_id = ProductVendor.vendor_product_id
                INNER JOIN (
                    SELECT
                        vendor_id,
                        vendor_name,
                        vendor_website
                    FROM Vendor
                    GROUP BY vendor_website
                ) AS Vendors ON Vendors.vendor_id = ProductVendor.vendor_id
                ORDER BY Products.product_id, Vendors.vendor_id;
            """)
            result = this.fetchall()
            structured_data = []
            if len(result) > 0:
                current_product = None
                for row in result:
                    brand_name, product_mpn, product_id, vendor_id, vendor_name, vendor_website, vendor_product_id, vendor_url = row
                    keyword = f'{brand_name} {product_mpn}'
                    # If this is a new product or first row
                    if current_product is None or current_product['product_id'] != product_id:
                        # If we have previous data, add it to structured_data
                        if current_product is not None:
                            structured_data.append(current_product)
                        # Start new product entry
                        current_product = {
                            'keyword': keyword,
                            'product_id': product_id,
                            'data': []
                        }
                    # Add vendor data
                    current_product['data'].append({
                        'vendor_id': vendor_id,
                        'vendor_name': vendor_name,
                        'vendor_website': vendor_website,
                        'vendor_product_id': vendor_product_id,
                        'vendor_url': vendor_url
                    })
                # Add the last product
                if current_product is not None:
                    structured_data.append(current_product)
                # ✅ After finishing processing, trigger the daily email
                # send_once_per_day()
                return structured_data
            else:
                logger.error(f"Re-setting products to be scraped again")
                # resetting the products to be scraped again
                this.execute(f"""
                    UPDATE Product
                    SET is_picked_for_google_main_right = '0'
                    WHERE product_id IN ({product_ids})
                        AND Product.is_picked_for_google_main_right = '1'
                    ORDER BY Product.product_id Desc;
                """)
                conn.commit()
                getKeywordFromDB()
            return structured_data
    except mysql.connector.Error as e:
        logger.error(f"MySQL ERROR getKeywordFromDB() >> {e}")
    finally:
        if conn.is_connected():
            this.close()
            conn.close()


                    #                 SELECT
                    #         DISTINCT Product.product_id
                    #     FROM Product
                    #     INNER JOIN Brand ON Brand.brand_id = Product.brand_id
                    #     INNER JOIN ProductVendor ON ProductVendor.product_id = Product.product_id
                    #     WHERE
                    #         ProductVendor.vendor_id = {vendorID}
                    #         AND ProductVendor.product_id IN ({product_ids})
                    #         AND Product.is_picked_for_google_main_right = '1'
                    #     ORDER BY Product.product_id Desc 
                    # );

def googleMainSearch(searchKey, productID, data):
    logger.debug(f"Processing ({searchKey})")
    try:
        googleMainRightSideBox(searchKey, productID, data)
    except Exception as e:
        logger.debug(f"Failed search for (PID: {productID}): {e}")
    finally:
        setAsProcessed(productID)
        logger.debug(f"Processed ({searchKey})")

def monitor_resources(processes, pause_events):
    """
    Monitor system resources and pause/resume processes based on CPU and memory usage
    """
    paused_process = None
    while any(p.is_alive() for p in processes):
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)

        print(f"paused_process  ({paused_process}).")
        print(f"Memory usage ({memory_usage}%) x CPU usage ({cpu_usage}%).")
        if memory_usage > 80 or cpu_usage > 90:
            logging.warning(f"Memory usage ({memory_usage}%) or CPU usage ({cpu_usage}%) too high.")
            
            # Pause one process to free up memory (pause the first process)
            if paused_process is None:
                for i, p in enumerate(processes):
                    if p.is_alive():
                        paused_process = p
                        pause_events[i].clear()  # Clear event to pause the process
                        logging.info(f"Pausing process {p.name}")
                        break
            time.sleep(10)
        else:
            if paused_process is not None:
                paused_process_index = processes.index(paused_process)
                pause_events[paused_process_index].set()  # Set event to resume the paused process
                logging.info(f"Resuming process {paused_process.name}")
                paused_process = None
            time.sleep(10)

# get start date from start file
def getStartDate():
    allNewStartFiles = glob.glob("*start")
    if len(allNewStartFiles) == 1:
        return allNewStartFiles[0].split(")")[0].replace("(", "").strip()
    else:
        return

# Today's total processed products
def totalProcessed(date, count=0):
    processedCountFile = f"({date})processed"
    if os.path.exists(processedCountFile):
        with open(processedCountFile) as f:
            count = f.read()
    try: os.remove(processedCountFile)
    except: pass
    return int(count)

# Total scraped counts
def totalScraped(limited_products, productIDs=''):
    limited_products = len(limited_products)
    # print(limited_products)
    try:
        conn = mysql.connector.connect(host=HOST, database=DB, user=USER, password=PASS)
        if conn.is_connected():
            cursor = conn.cursor()
            html = '<div style="padding: 25px 5px;">'
            if productIDs == '':
                cursor.execute(f"""
                    SELECT
                        GROUP_CONCAT(DISTINCT product_id) AS product_ids
                    FROM (
                        SELECT
                            DISTINCT Product.product_id
                        FROM Product
                        INNER JOIN ProductVendor ON ProductVendor.product_id = Product.product_id
                        INNER JOIN ErpData ON ErpData.vendor_product_id = ProductVendor.vendor_product_id
                        WHERE
                            Product.is_active = "1"
                            AND Product.gcode IS NOT NULL
                            AND ErpData.atp IS NOT NULL
                            AND ErpData.atp > 0
                            AND ProductVendor.vendor_id IN {vendorID}
                        GROUP BY Product.product_id
                        ORDER BY Product.product_id
                        LIMIT {limited_products}
                    ) AS limited_product_ids;
                """)
                result = cursor.fetchone()
                product_ids = result[0]
                print(product_ids)
                # Today's total products processed
                yesterday = datetime.now() - timedelta(1)
                total_processed = totalProcessed(yesterday.strftime("%Y-%m-%d"))
                if total_processed > 0:
                    html += '<div style="padding: 0 0 10px 0;">'
                    html += f'<p style="margin: 0;display: inline;">Today\'s Total Processed Products</p><b>:</b> <p style="margin: 0;display: inline;">{total_processed}</p>'
                    html += "</div>"
                else:
                    # Total products processed
                    cursor.execute(f"""
                        SELECT
                            COUNT(DISTINCT Product.product_id) AS total_processed
                        FROM Product
                        INNER JOIN ProductVendor ON ProductVendor.product_id = Product.product_id
                        WHERE
                            Product.product_id IN ({product_ids})
                            AND Product.is_processed = '1'
                            AND ProductVendor.vendor_id IN {vendorID};
                    """)
                    result1 = cursor.fetchone()
                    total_processed = result1[0]
                    html += '<div style="padding: 0 0 10px 0;">'
                    html += f'<p style="margin: 0;display: inline;">Total Processed Products</p><b>:</b> <p style="margin: 0;display: inline;">{total_processed}</p>'
                    html += "</div>"
                # Today's total products and vendors scraped
                cursor.execute(f"""
                    SELECT
                        DISTINCT ProductVendor.product_id, (
                            SELECT
                                COUNT(DISTINCT PV.vendor_id)
                            FROM ProductVendor AS PV
                            INNER JOIN TempVendorPricing AS TVP ON TVP.vendor_product_id = PV.vendor_product_id
                            WHERE
                                TVP.vendorprice_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY)
                                AND TVP.source = 'gmc'
                                AND PV.product_id = ProductVendor.product_id
                        ) AS total_scraped_vendors
                    FROM ProductVendor
                    INNER JOIN TempVendorPricing ON TempVendorPricing.vendor_product_id = ProductVendor.vendor_product_id
                    WHERE
                        TempVendorPricing.vendorprice_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY)
                        AND TempVendorPricing.source = 'gmc'
                        AND ProductVendor.product_id IN ({product_ids});
                """)
                result2 = cursor.fetchall()
                total_vendors_scraped = 0
                for row in result2:
                    total_vendors_scraped = total_vendors_scraped + int(row[1])
                # Today's total products scraped
                html += '<div style="padding: 0 0 10px 0;">'
                html += f'<p style="margin: 0;display: inline;">Today\'s Total Scraped Products</p><b>:</b> <p style="margin: 0;display: inline;">{len(result2)}</p>'
                html += "</div>"
                # Today's total vendors scraped
                html += '<div style="padding: 0 0 10px 0;">'
                html += f'<p style="margin: 0;display: inline;">Today\'s Total Scraped Vendors</p><b>:</b> <p style="margin: 0;display: inline;">{total_vendors_scraped}</p>'
                html += "</div>"
            else:
                product_ids = productIDs
                # Total products processed
                cursor.execute(f"""
                    SELECT
                        COUNT(DISTINCT Product.product_id) AS total_processed
                    FROM Product
                    INNER JOIN ProductVendor ON ProductVendor.product_id = Product.product_id
                    WHERE
                        Product.product_id IN ({product_ids})
                        AND Product.is_processed = '1'
                        AND ProductVendor.vendor_id IN {vendorID};
                """)
                result1 = cursor.fetchone()
                total_processed = result1[0]
                html += '<div style="padding: 0 0 10px 0;">'
                html += f'<p style="margin: 0;display: inline;">Total Processed Products</p><b>:</b> <p style="margin: 0;display: inline;">{total_processed}</p>'
                html += "</div>"
                # Total products and vendors scraped
                startDate = getStartDate()
                fromWhen = f"AND TempVendorPricing.vendorprice_date >= {startDate}" if startDate != None else ""
                cursor.execute(f"""
                    SELECT
                        DISTINCT ProductVendor.product_id, (
                            SELECT
                                COUNT(DISTINCT PV.vendor_id)
                            FROM ProductVendor AS PV
                            INNER JOIN TempVendorPricing AS TVP ON TVP.vendor_product_id = PV.vendor_product_id
                            WHERE
                                TVP.source = 'gmc'
                                AND PV.product_id = ProductVendor.product_id
                        ) AS total_scraped_vendors
                    FROM ProductVendor
                    INNER JOIN TempVendorPricing ON TempVendorPricing.vendor_product_id = ProductVendor.vendor_product_id
                    WHERE
                        TempVendorPricing.source = 'gmc'
                        {fromWhen}
                        AND ProductVendor.product_id IN ({product_ids});
                """)
                result2 = cursor.fetchall()
                total_vendors_scraped = 0
                for row in result2:
                    total_vendors_scraped = total_vendors_scraped + int(row[1])
                # Total products scraped
                html += '<div style="padding: 0 0 10px 0;">'
                html += f'<p style="margin: 0;display: inline;">Total Scraped Products</p><b>:</b> <p style="margin: 0;display: inline;">{len(result2)}</p>'
                html += "</div>"
                # Total vendors scraped
                html += '<div style="padding: 0 0 10px 0;">'
                html += f'<p style="margin: 0;display: inline;">Total Scraped Vendors</p><b>:</b> <p style="margin: 0;display: inline;">{total_vendors_scraped}</p>'
                html += "</div>"
            html += "</div>"
            return html   
    except mysql.connector.Error as e:
        print(f"MySQL ERROR totalScraped() >> {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Sending mail
def sendMail(content, receivers, html=False, port=465):
    import smtplib
    from email.message import EmailMessage

    smtp_server, port = "smtp.gmail.com", port
    sender_email, password = "neha.matrid4567@gmail.com", "zeyfihscmfjpzzca"
    # is html content
    message = EmailMessage()
    if html:
        message.add_alternative(content, subtype='html')
    else:
        message.set_content(content)

    message['Subject'] = 'GMC Scrapper Count of all GP Rules'
    message['From'] = sender_email
    receivers_email = ", ".join(receivers) if isinstance(receivers, list) else receivers
    message['To'] = receivers_email

    try:
        server = smtplib.SMTP_SSL(smtp_server, port)
        server.login(sender_email, password)
        server.send_message(message)
        server.quit()
        print(f'Mail was sent to: {receivers_email}')
    except Exception as e:
        logger.debug(f'Mail was not sent {e}, Retrying once with different port.')
        if port == 465: 
            sendMail(content, receivers, html=html, port=587)

# Main function to manage the scraping
def primary():
    # Get products from DB
    searchKeys = getKeywordFromDB()
    logger.debug(f"""-------------- Process started for {len(searchKeys)} product(s) --------------""")

    # Begin scraping products
    processes, pause_events = [], []
    for row in searchKeys:
        setAsPicked(row['product_id'])
        p = multiprocessing.Process(target=googleMainSearch, args=(row['keyword'], row['product_id'], row['data']))
        event = multiprocessing.Event()
        pause_events.append(event)
        event.set()
        processes.append(p)
        p.start()
        time.sleep(3)
    
    # Monitor resources
    monitor_resources(processes, pause_events)
    # Wait for all processes to complete
    for p in processes:
        p.join()

if __name__ == "__main__":
    os.chdir(PROJECT_DIR)
    start = time.perf_counter()
    primary()
    finish = time.perf_counter()
    logger.debug(f'Finished ThreadMain in {round(finish - start, 2)} second(s)')
