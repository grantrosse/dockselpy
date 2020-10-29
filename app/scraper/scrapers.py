from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains
import time
import requests
import pickle
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import logging
from .data_utils import getApprovalLink
# from dotenv import load_dotenv

# load_dotenv()
log = logging.getLogger(__name__)

with open('security_questions.json') as json_file:    
    security_questions = json.load(json_file)

def getSession(api):
    log.info(f'getting session for {api}')
    session = requests.Session()
    if api == 'AMZL':
        try:
            with open('cookies_AMZL.pkl', 'rb') as f:
                session.cookies.update(pickle.load(f))
            log.info(f'created session for {api}')
        except:
            pass
        # session.headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',\
        #         'Accept-Encoding':	'gzip, deflate, br',\
        #         'Accept-Language':	'en-US,en;q=0.5',\
        #         'Connection': 'keep-alive',\
        #         'Host':	'logistics.amazon.com',\
        #         'Upgrade-Insecure-Requests': '1',\
        #         'User-Agent':	'Mozilla/5.0 Gecko/20100101 Firefox/81.0'}
        session.headers = {
                'Accept-Encoding':	'gzip, deflate, br',\
                'Accept-Language':	'en-US,en;q=0.5',\
                'Connection': 'keep-alive',\
                'Host':	'logistics.amazon.com',\
                'Upgrade-Insecure-Requests': '1',\
                'User-Agent':	'Mozilla/5.0 Gecko/20100101 Firefox/81.0'}        
        return session
    if api == 'Paycom':
        try:
            with open('cookies_Paycom.pkl', 'rb') as f:
                session.cookies.update(pickle.load(f))
            log.info(f'created session for {api}')
        except:
            pass
        session.headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding':	'gzip, deflate, br',
                        'Accept-Language':	'en-US,en;q=0.5',
                        'Connection': 'keep-alive',
                        'Host' : "www.paycomonline.net",
                        'Upgrade-Insecure-Requests': '1',
                        'Referer': "https://www.paycomonline.net/v4/cl/web.php/schedule/manage-schedules",
                        'User-Agent':	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0'
                        }
        return session

class webDriver:
    def __init__(self):
        self.options = Options()
        self.options.headless = True
        # self.options.add_argument("--disable-gpu")
        # self.options.add_argument("--no-sandbox")
        # self.options.add_argument("enable-automation")
        # self.options.add_argument("--disable-infobars")
        # self.options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Firefox(options=self.options)

class AmazonScraper(webDriver):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.name = 'AMZL'

    def getAMZLCookies(self):
        log.info('fetching amazon cookies')
        self.driver.get("https://www.amazon.com/gp/sign-in.html")

        time.sleep(5)

        elem = self.driver.find_element_by_xpath('//*[@id="ap_email"]')
        elem.send_keys(os.getenv('EMAIL'))
        elem.send_keys(Keys.RETURN)
        time.sleep(5)

        elem = self.driver.find_element_by_xpath('//*[@id="ap_password"]')
        elem.send_keys(os.getenv('PASS'))
        elem.send_keys(Keys.RETURN)
        time.sleep(5)

        approvalURL = getApprovalLink()
        print(approvalURL)

        cookies = self.driver.get_cookies()
        # print(cookies)

        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])

        with open('cookies_AMZL.pkl', 'wb') as f:
            pickle.dump(self.session.cookies, f)

        self.driver.quit()
        self.session.close()

    def authorize(self):
        self.session = getSession(self.name)
        response = self.session.get(self.url)
        try:
            try:
                data=response.json()
                self.session.close()
                return True
            except:
                log.info('starting AMZN scraper')
                self.getAMZLCookies()
                return True
        except:
            False

    def getReservations(self):
        log.info('fetching amazon reservations')
        self.session = getSession(self.name)
        print(self.url)
        print('----------')
        response = self.session.get(self.url)
        print(response.request)
        print(response.request.headers)
        print('----------------')
        print(response.request.url)
        print(response.text)
        print('-------------')
        data = response.json()
        reservationArray = []

        for item in data['data']:
            driverName = item['driverName']
            for date in item['reservationsMap']:
                for assignment in item['reservationsMap'][date]:
                    reservationArray.append({"driverName" : driverName, 
                                                "date": date, 
                                                "status": assignment['status'], 
                                                "startTimeInMinutes": str(assignment['startTimeInMinutes']),
                                                "driverPersonID": assignment['daPersonId'],
                                                "serviceTypeName": assignment['serviceTypeName'],
                                                }) 
        return reservationArray

    def getShifts(self):
        log.info('fetching amazon shifts')
        self.session = getSession(self.name)
        response = self.session.get(self.url)
        data = response.json()
        shiftArray = []

        for item in data['data']:
            driverName = item['driverName']
            for date in item['shiftAssignmentsMap']:
                for assignment in item['shiftAssignmentsMap'][date]:
                    shiftArray.append({"driverName" : driverName,
                                                "driverPersonId": item['driverPersonId'],
                                                "driverEmail": item['driverEmail'],
                                                "workPhoneNumber": item['workPhoneNumber'],
                                                "employeeId": item['employeeId'],
                                                "date": date, 
                                                "employeeId": assignment['employeeId'],
                                                "shiftName": assignment['shiftName'],
                                                "shiftType": assignment['shiftType'],
                                                "assignmentType": assignment['assignmentType'],
                                                "mappingReason": assignment['mappingReason'],
                                                "state": assignment['state'],
                                                "type": assignment['type'],
                                                "mappingStatus": assignment['mappingStatus'], 
                                                })
        return shiftArray


class PaycomScraper(webDriver):
    def __init__(self, employeeUrl, shiftUrl):
        super().__init__()
        self.employeeUrl = employeeUrl
        self.shiftUrl = shiftUrl
        self.name = 'Paycom'

    def getPAYCookies(self):
        log.info('fetching paycom cookies')
        self.driver.get("https://www.paycomonline.net/v4/cl/cl-login.php")

        elem = self.driver.find_element_by_xpath('//*[@id="clientcode"]')
        elem.send_keys(os.getenv('PAYCOMCLIENTCODE'))
        time.sleep(2)
        elem = self.driver.find_element_by_xpath('//*[@id="txtlogin"]')
        elem.send_keys(os.getenv('PAYCOMUSER'))
        time.sleep(2)
        elem = self.driver.find_element_by_xpath('//*[@id="password"]')
        elem.send_keys(os.getenv('PASS'))
        elem.send_keys(Keys.RETURN)
        time.sleep(7)

        question1 = self.driver.find_element_by_name("firstSecurityQuestion")
        question2 = self.driver.find_element_by_name("secondSecurityQuestion")
        try:
            answer1 = security_questions[question1.get_attribute("aria-label")]
            answer2 = security_questions[question2.get_attribute("aria-label")]
        except Exception as e:
            log.error(f'Missing security question. Please add to dictionary: question1:{question1.get_attribute("aria-label")}, question2:{question2.get_attribute("aria-label")}')
            raise ValueError(f'Missing security question. Please add to dictionary: question1:{question1}, question2:{question2}')

        question1.send_keys(answer1)
        question2.send_keys(answer2)
        time.sleep(2)

        Button = self.driver.find_element_by_xpath('/html/body/div[4]/div/div/form/div[5]/button')
        Button.click()
        time.sleep(5)

        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
        with open('cookies_Paycom.pkl', 'wb') as f:
            pickle.dump(self.session.cookies, f)

        self.driver.quit()
        self.session.close()

    def authorize(self):
        self.session = getSession(self.name)
        response = self.session.get(self.shiftUrl)
        try:
            try:
                data=response.json()
                self.session.close()
                return True
            except:
                self.getPAYCookies()
                return True
        except:
            False

    def getEmployees(self):
        log.info('fetching employee data')
        self.session = getSession(self.name)
        response = self.session.get(self.employeeUrl)
        data = response.json()

        paycomEmployeeArray = []
        for item in data['results']:
            paycomEmployeeArray.append({ "firstName": item['firstName'],
                                            "lastName": item['lastName'],
                                            "employeeCode": item['employeeCode'],
                                            "employeeStatus": item['employeeStatus'],
                                            "primaryPhone": item['employeeContactInfo']['primaryPhone'],
                                            "workEmail": item['employeeContactInfo']['workEmail'],
                                            "personalEmail": item['employeeContactInfo']['personalEmail'],
                                            "isClockedIn": item['isClockedIn'],
                                            })

        return paycomEmployeeArray
    
    def getShifts(self):
        log.info('fetching paycom shift data')
        self.session = getSession(self.name)
        response = self.session.get(self.shiftUrl)
        data = response.json()   

        paycomShiftArray = []
        for item in data['results']:
            driverID = item
            for shift in data['results'][item]:
                paycomShiftArray.append({"employeeCode": shift['employeeCode'],
                                            "description": shift['description'],
                                            "startDate": shift['startDate'],
                                            "endDate": shift['endDate'],
                                            "duration": shift['duration'],
                                            "isOnCall": shift['isOnCall'],
                                            "isOvernight": shift['isOvernight'],
                                            "isPending": shift['isPending'],
                                            "overlappingShiftInstanceIds": True if len(shift["overlappingShiftInstanceIds"]) > 0 else False,
                                            "overlappingAssignedShiftIds": True if len(shift["overlappingAssignedShiftIds"]) > 0 else False,
                                            })

        return paycomShiftArray