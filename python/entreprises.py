import csv
from parsel import Selector
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os.path
import pickle
import mysql.connector
import requests
import re

# Minimal settings
selenium_cookie_file = 'test.txt'

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

# AUTH 

authData = {
    "identifier": "identifier", # utilisateur strapi
    "password": "password" # mot de passe du compte strapi
}
r = requests.post('http://localhost:1337/auth/local', data = authData )
json = r.json()
authorization = 'Bearer ' + json['jwt']


writer = csv.writer(open('output.csv', 'w+', encoding='utf-8-sig', newline=''))
writer.writerow(['Name', 'Position', 'Company', 'Education', 'Location', 'URL'])

driver = webdriver.Chrome('C://Users//romar//Downloads//chromedriver')

driver = webdriver.Chrome('C://Users//romar//Downloads//chromedriver')
load_cookies()
driver.get('https://www.linkedin.com/')

# username = driver.find_element_by_name("session_key")
# username.send_keys('loggin')
# sleep(0.5)

# password = driver.find_element_by_name('session_password')
# password.send_keys('password')
# sleep(0.5)

# sign_in_button = driver.find_element_by_class_name('sign-in-form__submit-button')
# sign_in_button.click()
# sleep(2)


def saveEntreprise(entrepriseID):

    headers = {'Authorization': authorization }

    r = requests.get('http://localhost:1337/entreprises?entrepriseID=' + entrepriseID, headers=headers)
    if len(r.json()) > 0:
        print("Already exist: " + entrepriseID)
        return r.json()[0]

    driver.get('https://www.linkedin.com/company/' + entrepriseID + '/about/')
    sleep(1)

    sel = Selector(text = driver.page_source)

    name = sel.xpath('//*[@class = "org-top-card-summary__title t-24 t-black t-bold truncate"]/*/text()').extract_first()
    name = ' '.join(name.split())

    image = sel.xpath('//*[@class = "org-top-card-primary-content__logo-container"]/img[@src]').attrib['src']

    address = sel.xpath('//*[@class = "org-location-card pv2"]/*[@class = "t-14 t-black--light t-normal break-words"]/text()').extract_first()
    if address: address = ' '.join(address.split())

    def formatLabel(entry):
        return ' '.join(entry.split())

    infosLabel = list(map(formatLabel, sel.xpath('//*[@class = "artdeco-card p4 mb3"]/*[3]/*[@class = "org-page-details__definition-term t-14 t-black t-bold"]/text()').getall()))
    infos = sel.xpath('//*[@class = "artdeco-card p4 mb3"]/*[3]/*//text()').getall()

    sector = ""
    sizeLabel = ""
    employeesCountLabel = ""

    currentIndex = 0
    innerIndex = 0
    for info in infos:
        currentLabel = ' '.join(info.split())
        currentLabel = currentLabel.replace(" ", "")

        if currentIndex+1 < len(infosLabel) and currentLabel == infosLabel[currentIndex + 1]:
            currentIndex += 1
            innerIndex = 0

        if currentLabel == "Secteur" and innerIndex == 1: sector = currentLabel # GET SECTOR
        if currentLabel == "Taille de l’entreprise" and innerIndex == 1: sizeLabel = currentLabel # GET SIZE
        if currentLabel == "Taille de l’entreprise" and innerIndex == 2: employeesCountLabel = currentLabel # GET EMPLOYEES COUNT

        innerIndex += 1

    data = {
        "name": name,
        "sizeLabel": sizeLabel,
        "employeesCount": 0, #  int(re.sub("[^0-9]", "", employeesCountLabel.replace(' ', '')))
        "sector": sector,
        "address": address,
        "image": image,
        "entrepriseID": entrepriseID
    }

    headers = {'Authorization': authorization }
    r = requests.post('http://localhost:1337/entreprises', data=data, headers=headers)

    return r.json()


def saveSchool(url):
    driver.get("https://www.linkedin.com" + url)
    reelUrl = driver.current_url
    
    schoolID  = re.sub(".*/school/(.*)/.*", r'\1', reelUrl.replace(' ', ''))

    if "/" in schoolID: return None

    headers = {'Authorization': authorization }
    r = requests.get('http://localhost:1337/schools?schoolID=' + schoolID, headers=headers)
    if len(r.json()) > 0:
        print("Already exist: " + schoolID)
        return r.json()[0]

    driver.get(reelUrl + "/about")
    sleep(1)

    sel = Selector(text = driver.page_source)

    name = sel.xpath('//*[@class = "org-top-card-summary__title t-24 t-black t-bold truncate"]/*/text()').extract_first()
    name = ' '.join(name.split())

    address = sel.xpath('//*[@class = "org-location-card pv2"]/*[@class = "t-14 t-black--light t-normal break-words"]/text()').extract_first()
    if address: address = ' '.join(address.split())

    schoolData = {
        "name": name,
        "address": address,
        "lat": 0.0,
        "lng": 0.0,
        "schoolID": schoolID
    }

    r = requests.post('http://localhost:1337/schools', data=schoolData, headers=headers)

    return r.json() 

def saveExperience(data):
    entreprise = saveEntreprise(data["entrepriseID"])

    if entreprise and 'id' in entreprise.keys():
        data["entreprise"] = entreprise["id"]

        headers = {'Authorization': authorization }
        r = requests.post('http://localhost:1337/experiences', data=data, headers=headers)


def savePerson(personID):

    print("-----")
    print("GET PERSON: " + personID)

    headers = {'Authorization': authorization }

    r = requests.get('http://localhost:1337/people?personID=' + personID, headers=headers)
    if len(r.json()) > 0:
        print("Already exist: " + personID)
        return r.json()[0]

    driver.get('https://www.linkedin.com/in/' + personID + '/')
    sleep(1)

    driver.find_element_by_tag_name('body').send_keys(Keys.END)

    sleep(3)

    sel = Selector(text = driver.page_source)

    name = sel.xpath('//*[@class = "inline t-24 t-black t-normal break-words"]/text()').extract_first().split()
    name = ' '.join(name)
    location = ' '.join(sel.xpath('//*[@class = "t-16 t-black t-normal inline-block"]/text()').extract_first().split())
    image = sel.xpath('//*[@class = "presence-entity presence-entity--size-9 pv-top-card__image"]//*[@src]').attrib['src']
    url = driver.current_url

    data = {
        "personID": personID,
        "name": name,
        "zone": location,
        "lat": 0.0,
        "lng": 0.0,
        "image": image,
        "url": url
    }
    r = requests.post('http://localhost:1337/people', data=data, headers=headers)
    person = r.json()["id"]

    # EXPERIENCES

    print("GET EXPERIENCES") 
    experiences = sel.xpath('//*[@id = "experience-section"]/*[contains(@class, "pv-profile-section__section-info")]/*') # //*[@id = "experience-section"]/*[contains(@class, "pv-profile-section__section-info")]/*

    for experience in experiences:
        
        try: 
            title = experience.xpath('.//h3[@class="t-16 t-black t-bold"]/text()').extract_first().split()
            title = ' '.join(title)

            entrepriseID = experience.xpath('.//a[@data-control-name = "background_details_company"]').xpath('@href').get().split('/')[2]

            entreprise = experience.xpath('.//*[@class = "pv-entity__secondary-title t-14 t-black t-normal"]/text()').extract_first()
            if entreprise: entreprise = ' '.join(entreprise.split())

            role = experience.xpath('.//*[@class = "pv-entity__secondary-title t-14 t-black t-normal"]/span/text()').extract_first()
            if role: role = ' '.join(role.split())

            date = experience.xpath('.//*[@class = "pv-entity__date-range t-14 t-black--light t-normal"]/span[2]/text()').extract_first()
            if date: date = ' '.join(date.split())

            location = experience.xpath('.//*[@class = "pv-entity__location t-14 t-black--light t-normal block"]/span[2]/text()').extract_first()
            if location: location = ' '.join(location.split())
        
            dates = date.split(" – ")

            start = 0
            end = 0

            if len(dates) > 0: start = dates[0]
            if len(dates) > 1: start = dates[1]
            
            print("-> " + title + " - " + role)

            dataExperience = {
                "entrepriseID": entrepriseID,
                "title": title,
                "role": role,
                "start": start,
                "end": end,
                "location": location,
                "person": person
            }
            saveExperience(dataExperience)

        except:
            print("Skip experience")
    
    # EDUCATIONS

    print("GET EDUCATIONS")
    educations = sel.xpath('//*[@id = "education-section"]/*[@class = "pv-profile-section__section-info section-info pv-profile-section__section-info--has-no-more"]/li/*')
    
    for education in educations:

        url = education.xpath('.//@href').get()
        
        school = saveSchool(url)

        if school and 'id' in school.keys():
            infos = education.xpath('.//*[contains(@class, "pv-entity__secondary-title")]/span[2]/text()')

            diplome = ""
            domaine = ""

            if len(infos) > 0: diplome = " ".join(infos[0].get().split())
            if len(infos) > 1: domaine = " ".join(infos[1].get().split())

            startYear = " ".join(education.xpath('.//*[contains(@class, "pv-entity__dates")]/span[2]/*[1]/text()').extract_first().split())
            endYear = " ".join(education.xpath('.//*[contains(@class, "pv-entity__dates")]/span[2]/*[2]/text()').extract_first().split())

            educationData = {
                "startYear": startYear,
                "endYear": endYear,
                "school": school["id"],
                "person": person,
                "diplome": diplome,
                "domaine": domaine
            }

            print("-> " + diplome + " at " + url)

            r = requests.post('http://localhost:1337/studies', data=educationData, headers=headers)

# try: savePerson("elsa-seguin-49b03b155")
# except ValueError: print("Oops!")

# try: savePerson("souha-lakriche-22302610a")
# except ValueError: print("Oops!")

# try: savePerson("florian-dandrey-8000011a2")
# except ValueError: print("Oops!")

# try: savePerson("virginie-lenoir")
# except ValueError: print("Oops!")

# try: savePerson("arnaudsalome")
# except ValueError: print("Oops!")

# saveEntreprise("orange")


for page in range(1, 50):

    driver.get("https://www.linkedin.com/search/results/people/?currentCompany=%5B%224249%22%5D&origin=FACETED_SEARCH&page=" + str(page))
    sleep(1)

    sel = Selector(text = driver.page_source)

    results = sel.xpath('//*[contains(@class, "reusable-search__result-container")]//*[@class = "entity-result__image-1"]')

    for result in results:
        url = result.xpath('.//@href').get()

        personID  = re.sub(".*/in/(.*)", r'\1', url)
        print(personID)

        if not "/" in personID:
            try: 
                savePerson(personID)
            except:
                print("Oops!")


    sleep(5)

# driver.quit()
