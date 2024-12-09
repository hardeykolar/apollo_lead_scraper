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
        prefs = {
            "credentials_enable_service": False,  # Disable password saving service
            "profile.password_manager_enabled": False  # Disable password manager
        }
        options.add_experimental_option("prefs", prefs)

        #options.add_argument("--disable-gpu") 
        options.add_argument("--disable-extensions") 
        options.add_argument("--disable-infobars") 
        options.add_argument("--start-maximized") 
        options.add_argument("--disable-notifications")  

        #options.add_argument("--headless")
        #options.add_argument('--no-sandbox')
        #options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=options)
        #self.driver.maximize_window()

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
        
        full_emails_data = []
        full_phone_numbers = []
        full_profile_url = []
        full_company_urls = []
        counter = 0

        while True:
            
            WebDriverWait(self.driver,60).until(EC.visibility_of_all_elements_located((By.XPATH,"//div[contains(@id,'table-row')]")))

            rows = self.driver.find_elements(By.XPATH,"//div[contains(@id,'table-row')]")
            
            
            for row in rows:
                
                #//div[contains(@id,'table-row')][4]/div[1]//a
                profile_name = row.find_element(By.XPATH,"./div[1]//a").get_attribute('textContent')
                names.append(profile_name)
                profile_url = row.find_element(By.XPATH,"./div[1]//a").get_attribute('href')
                full_profile_url.append(profile_url)
                job_title = row.find_element(By.XPATH,"./div[2]/span/span").get_attribute('textContent')
                titles.append(job_title)


                company_url = row.find_elements(By.XPATH,"./div[3]//a")[1].get_attribute('href')
                full_company_urls.append(company_url)
                company_name = row.find_elements(By.XPATH,"./div[3]//a")[1].get_attribute('textContent')
                companies.append(company_name)

                
            
            for i in range(len(rows)):
                try:
                    WebDriverWait(self.driver,10).until(EC.element_to_be_clickable((By.XPATH,"//span[contains(text(),'Access email')]/ancestor::button")))
                    rows[i].find_element(By.XPATH,"//span[contains(text(),'Access email')]/ancestor::button").click()
                    WebDriverWait(self.driver,60).until(EC.presence_of_element_located((By.XPATH,"//span[contains(text(),'@citadel.com')]")))
                    
                except:
                    pass
                self.driver.find_element(By.TAG_NAME,'body').send_keys(Keys.ESCAPE)
                time.sleep(random.randint(2,5))
            email_tags = self.driver.find_elements(By.XPATH,"//div[contains(@id,'table-row')]/div[4]//span[contains(text(),'@')]")
            for email_tag in email_tags:
                full_emails_data.append(email_tag.get_attribute("textContent"))

            
            for row in rows:

                try:
                    full_phone_numbers.append(row.find_element(By.XPATH,"./div[5]").get_attribute('textContent'))

                except:
                    full_phone_numbers.append('NA')

            
            counter += 1
            if counter == 2:
                break
            self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Next']").click()
            WebDriverWait(self.driver,20).until(EC.presence_of_all_elements_located((By.XPATH,"//div[contains(@id,'table-row')]")))
    
        

        lead_data = pd.DataFrame({'Names':names,'Titles':titles,'Profile_urls':full_profile_url,
             'Comapny_urls':full_company_urls,'Company_names':companies,
              'Email_address':full_emails_data,'Phone_Contact':full_phone_numbers})
        
        
        lead_data.to_csv("apollo_lead.csv",index=False)


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

# entry point
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



