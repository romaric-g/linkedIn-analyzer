import os.path
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep

def save_cookies():
    print("Saving cookies in " + selenium_cookie_file)
    pickle.dump(driver.get_cookies() , open(selenium_cookie_file,"wb"))

def load_cookies():
    if os.path.exists(selenium_cookie_file) and os.path.isfile(selenium_cookie_file):
        print("Loading cookies from " + selenium_cookie_file)
        cookies = pickle.load(open(selenium_cookie_file, "rb"))

        # Enables network tracking so we may use Network.setCookie method
        driver.execute_cdp_cmd('Network.enable', {})

        # Iterate through pickle dict and add all the cookies
        for cookie in cookies:
            # Fix issue Chrome exports 'expiry' key but expects 'expire' on import
            if 'expiry' in cookie:
                cookie['expires'] = cookie['expiry']
                del cookie['expiry']

            # Replace domain 'apple.com' with 'microsoft.com' cookies
            cookie['domain'] = cookie['domain'].replace('apple.com', 'microsoft.com')

            # Set the actual cookie
            driver.execute_cdp_cmd('Network.setCookie', cookie)

        # Disable network tracking
        driver.execute_cdp_cmd('Network.disable', {})
        return 1

    print("Cookie file " + selenium_cookie_file + " does not exist.")
    return 0

def pretty_print(pdict):
    for p in pdict:
        print(str(p))
    print('',end = "\n\n")


# Minimal settings
selenium_cookie_file = 'test.txt'

# Open a driver, get a page, save cookies
driver = webdriver.Chrome('C://Users//romar//Downloads//chromedriver')
driver.get('https://www.linkedin.com/')
sleep(40)
save_cookies()
pretty_print(driver.get_cookies())
print("SAVE")

# Rewrite driver with a new one, load and set cookies before any requests
# driver = webdriver.Chrome('C://Users//romar//Downloads//chromedriver')
# load_cookies()
# driver.get('https://www.linkedin.com/')
# pretty_print(driver.get_cookies())