from email.mime.application import MIMEApplication
import json
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

class WebsiteScraper:
    def __init__(self,home_url):
        self.url = home_url
        self.list_url = ""
        self.email = ""
        self.password = ""

        self.sender_email = ""
        self.sender_password = ""
        self.recipient_email = ""

        with open("config.json","r") as file:
            config = json.load(file)
            self.email = config["email"]
            self.password = config["password"]
            self.list_url = config["list_url"]

            self.sender_email = config["email_from"]
            self.sender_password = config["app_password"]
            self.recipient_email = config["email_to"]

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        options.add_argument("--disable-gpu") 
        options.add_argument("--disable-extensions") 
        options.add_argument("--disable-infobars") 
        options.add_argument("--start-maximized") 
        options.add_argument("--disable-notifications")  

        options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

    def login_to_apollo(self):
        self.driver.get(self.url)
        WebDriverWait(self.driver,30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,"input[name='email']")))
        email_box = self.driver.find_element(By.CSS_SELECTOR,"input[name='email']")
        email_box.send_keys(self.email)

        time.sleep(random.randint(2,4))
        password_box = self.driver.find_element(By.CSS_SELECTOR,"input[name='password']")
        password_box.send_keys(self.password)

        time.sleep(random.randint(2,4))
        login_btn = WebDriverWait(self.driver,10).until(
            EC.element_to_be_clickable((By.XPATH,"//div[text()='Log In']/ancestor::button")))
        login_btn.click()
        time.sleep(random.randint(5,8))
        self.driver.find_element(By.TAG_NAME,"body").send_keys(Keys.ESCAPE)


    def open_custom_url(self):
        self.driver.refresh()
        self.driver.get(self.list_url)
        names = []
        titles = []
        companies = []
        contact_locations = []
        employees = []
        industries = []
        keywords = []

        profile_urls = []
        company_urls = []

        full_emails_data = []
        full_phone_numbers = []
        counter = 0

        while True:
            emails_data = []
            phone_numbers = []
            WebDriverWait(self.driver,20).until(EC.visibility_of_all_elements_located((By.XPATH,'//table//tr//td')))

            rows = self.driver.find_elements(By.XPATH,'//table//tr')
            for index,row in enumerate(rows):
                if index == 0:
                    continue
                else:

                    company_urls.append([item.get_attribute('href') for item in row.find_elements(By.TAG_NAME,'td')[2].find_elements(By.TAG_NAME,'a')])

                    profile_urls.append([item.get_attribute('href') for item in row.find_elements(By.TAG_NAME,'td')[0].find_elements(By.TAG_NAME,'a')])

                    names.append([val.get_attribute('textContent') for val in row.find_elements(By.TAG_NAME,'td')][0])

                    titles.append([val.get_attribute('textContent') for val in row.find_elements(By.TAG_NAME,'td')][1])

                    companies.append([val.get_attribute('textContent') for val in row.find_elements(By.TAG_NAME,'td')][2])

                    contact_locations.append([val.get_attribute('textContent') for val in row.find_elements(By.TAG_NAME,'td')][4])

                    employees.append([val.get_attribute('textContent') for val in row.find_elements(By.TAG_NAME,'td')][5])

                    industries.append([val.get_attribute('textContent') for val in row.find_elements(By.TAG_NAME,'td')][7])

                    keywords.append([val.get_attribute('textContent') for val in row.find_elements(By.TAG_NAME,'td')][8])

    
            for i in range(1,len(rows)):
                try:
                    WebDriverWait(self.driver,10).until(EC.element_to_be_clickable((By.XPATH,"//div[contains(text(),'Access email')]/ancestor::button")))
                    rows[i].find_element(By.XPATH,"//div[contains(text(),'Access email')]/ancestor::button").click()
                    WebDriverWait(self.driver,15).until(EC.presence_of_all_elements_located((By.XPATH,"//div[contains(@id,'id-')]//span[contains(text(),'@')]")))
                    email_tags = rows[i].find_elements(By.XPATH,"//div[contains(@id,'id-')]//span[contains(text(),'@')]")
                    emails = [tag.text for tag in email_tags]
                
                except:
                    emails = ['NA']
                emails_data.append("|".join(emails))
                self.driver.find_element(By.TAG_NAME,'body').send_keys(Keys.ESCAPE)

                time.sleep(random.randint(2,5))

            phones_text = [item.text for item in self.driver.find_elements(By.XPATH,'//table//tr')][1:]
        
            for item in phones_text:
                try:
                    phone_numbers.append(re.search(r"\+?\(?\d{3}?\)?\d{5,10}",item).group())
                except:
                    phone_numbers.append('NA')

            full_emails_data.extend(emails_data)
            full_phone_numbers.extend(phone_numbers)

            counter += 1
            if counter == 2:
                break
            self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='right-arrow']").click()
            #WebDriverWait(driver,20).until(EC.presence_of_all_elements_located((By.XPATH,'//table//tr')))
    
        full_profile_url = ['|'.join(val) for val in profile_urls]
        full_company_urls = ['|'.join(item) for item in company_urls]


        lead_data = pd.DataFrame({'Names':names,'Titles':titles,'Profile_urls':full_profile_url,
             'Comapny_urls':full_company_urls,'Company_names':companies,
              'Contact_locations':contact_locations,'Employee_counts':employees,
             'Industries':industries,'Keywords':keywords,'Email_address':full_emails_data,'Phone_Contact':full_phone_numbers})
        
        
        lead_data.to_csv("apollo_lead.csv",index=False)

        # Add your scraping logic here using Selenium commands

    def send_email(self,subject,body):

        message = MIMEMultipart('alternative')
        message["From"] = self.sender_email
        message["To"] = self.recipient_email
        message["Subject"] = subject

        message.attach(MIMEText(body,'plain'))
        attachment_path = "apollo_lead.csv"
        filename = os.path.basename(attachment_path)

        with open(attachment_path,'rb') as attachment_file:
            part = MIMEBase('application','octet-stream')
            part.set_payload(attachment_file.read())
        encoders.encode_base64(part)

        part.add_header("Content-Disposition","attachment; filename="+filename)
        message.attach(part)

        with smtplib.SMTP('smtp.gmail.com',587) as server:
            server.starttls()
            server.login(self.sender_email,self.sender_password)
            server.send_message(message)
        print("email sent successfully")

        
        
       
    def close_browser(self):
        self.driver.quit()

# Example usage
if __name__ == "__main__":

    scraper = WebsiteScraper("https://app.apollo.io/#/login")
    scraper.login_to_apollo()
    scraper.open_custom_url()
    time.sleep(10)
    subject = "apollo lead data"
    body  = "please find the csv lead data attached below"
    #attachment_path = "apollo_lead.csv"
    scraper.send_email(subject=subject,body=body)
    

    scraper.close_browser()

