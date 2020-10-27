from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains
import time
import requests
import pickle
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import json
import os
import logging
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(filename='Silex_Log.log',format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.captureWarnings(True)

##dates for api pull
fromDate = datetime.today().strftime('%Y-%m-%d')
toDate = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d')

with open('security_questions.json') as json_file:    
    security_questions = json.load(json_file)

desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

def getAMZLCookies():
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get("https://www.amazon.com/gp/sign-in.html")

    elem = driver.find_element_by_xpath('//*[@id="ap_email"]')
    elem.send_keys(os.getenv('EMAIL'))
    elem.send_keys(Keys.RETURN)

    time.sleep(2)

    elem = driver.find_element_by_xpath('//*[@id="ap_password"]')
    elem.send_keys(os.getenv('PASS'))
    elem.send_keys(Keys.RETURN)
    time.sleep(7)

    cookies = driver.get_cookies()

    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])

    with open('cookies_AMZL.pkl', 'wb') as f:
        pickle.dump(s.cookies, f)

    driver.quit()
    s.close()

def getPaycomCookies():
    options = Options()
    options.headless = True
    driver = webdriver.Firefox()#options=options)
    driver.get("https://www.paycomonline.net/v4/cl/cl-login.php")

    elem = driver.find_element_by_xpath('//*[@id="clientcode"]')
    elem.send_keys(os.getenv('PAYCOMCLIENTCODE'))
    time.sleep(2)
    elem = driver.find_element_by_xpath('//*[@id="txtlogin"]')
    elem.send_keys(os.getenv('PAYCOMUSER'))
    time.sleep(2)
    elem = driver.find_element_by_xpath('//*[@id="password"]')
    elem.send_keys(os.getenv('PASS'))
    elem.send_keys(Keys.RETURN)
    time.sleep(7)

    question1 = driver.find_element_by_name("firstSecurityQuestion")
    question2 = driver.find_element_by_name("secondSecurityQuestion")
    try:
        answer1 = security_questions[question1.get_attribute("aria-label")]
        answer2 = security_questions[question2.get_attribute("aria-label")]
    except Exception as e:
        raise ValueError(f'Missing security question. Please add to dictionary: question1:{question1}, question2:{question2}')

    question1.send_keys(answer1)
    question2.send_keys(answer2)
    time.sleep(2)

    Button = driver.find_element_by_xpath('/html/body/div[4]/div/div/form/div[5]/button')
    Button.click()
    time.sleep(5)

    cookies = driver.get_cookies()
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    with open('cookies_Paycom.pkl', 'wb') as f:
        pickle.dump(s.cookies, f)

    driver.quit()
    s.close()

def getShifts(data):
    shiftArray = []
    shifts = {}

    for item in data['data']:
        driverName = item['driverName']
        shifts[driverName] = { "dates": {} }
        for date in item['shiftAssignmentsMap']:
            # reservations[date] = {"status": "UNASSIGNED"}
            shifts[driverName]["dates"][date] = {"status":"UNASSIGNED"}
            for assignment in item['shiftAssignmentsMap'][date]:
                shifts[driverName]["dates"][date] = {"mappingStatus": assignment['mappingStatus'], 
                                    "shiftName": assignment['shiftName'],
                                    "mappingReason": assignment['mappingReason'],
                                    "assignmentType": assignment['assignmentType']
                                        }
                # reservations[driverName]["dates"][date] = {"status" : assignment['status']}
                ##LIST STUFF---better for DF?
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

def getReservations(data):
    reservations = {}
    reservationArray = []
    for item in data['data']:
        # if 'Lachelle' in item['driverName']:
        driverName = item['driverName']
        reservations[driverName] = { "dates": {} }
        for date in item['reservationsMap']:
            # reservations[date] = {"status": "UNASSIGNED"}
            reservations[driverName]["dates"][date] = {"status":"UNASSIGNED"}
            for assignment in item['reservationsMap'][date]:
                reservations[driverName]["dates"][date] = {"status": assignment['status'], 
                                    "startTimeInMinutes": str(assignment['startTimeInMinutes']),
                                    "driverPersonID": assignment['daPersonId'],
                                    "serviceTypeName": assignment['serviceTypeName']
                                        }
                # reservations[driverName]["dates"][date] = {"status" : assignment['status']}
                ##LIST STUFF---better for DF?
                reservationArray.append({"driverName" : driverName, 
                                            "date": date, 
                                            "status": assignment['status'], 
                                            "startTimeInMinutes": str(assignment['startTimeInMinutes']),
                                            "driverPersonID": assignment['daPersonId'],
                                            "serviceTypeName": assignment['serviceTypeName'],
                                            })
        # reservations[driverName]["dates"] = reservationArray   
    return reservationArray

def getPaycomEmployees(session):
    employeeURL = 'https://www.paycomonline.net/v4/cl/web.php/scheduling/api/manage-schedules/employee?skip=0&take=100&q=&filterInstanceId=f1f61f69ac734e5c81c3027684388a&filterName=cl-manage-scheds'
    response = session.get(employeeURL)
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
    df = pd.DataFrame(paycomEmployeeArray)
    df.to_csv('paycom_employees.csv')

    return df

def getPaycomShifts(session):
    url = f'https://www.paycomonline.net/v4/cl/web.php/scheduling/api/manage-schedules/employee-shift?startDate={fromDate}&endDate={toDate}&skip=0&take=500&q=&filterInstanceId=52766f934b3d48d8a1df9db39eb537&filterName=cl-manage-scheds&scheduleGroupCode=2237'
    response = session.get(url)
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
    df = pd.DataFrame(paycomShiftArray)
    df.to_csv('paycom_shifts.csv')
    return df

def getSession(api):
    session = requests.Session()
    if api == 'AMZL':
        try:
            with open('cookies_AMZL.pkl', 'rb') as f:
                session.cookies.update(pickle.load(f))
        except:
            pass
        session.headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',\
                'Accept-Encoding':	'gzip, deflate, br',\
                'Accept-Language':	'en-US,en;q=0.5',\
                'Connection': 'keep-alive',\
                'Host':	'logistics.amazon.com',\
                'Upgrade-Insecure-Requests': '1',\
                'User-Agent':	'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0'}
        return session
    if api == 'Paycom':
        with open('cookies_Paycom.pkl', 'rb') as f:
            session.cookies.update(pickle.load(f))
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

def getAMZLData():
    session = getSession('AMZL')
    url = f'https://logistics.amazon.com/scheduling/home/api/v2/rosters?fromDate={fromDate}&serviceAreaId=6f0c423f-f609-4e32-a7f1-e624143b9d49&toDate={toDate}'
    response = session.get(url)
    if "Invalid" in response.text or "403 ERROR" in response.text:
        print(response.text)
        getAMZLCookies()
        session = getSession('AMZL')
        response = session.get(url)

    data = response.json()
    # print(response.text)

    reservs = getReservations(data)
    df = pd.DataFrame(reservs)
    df.to_csv('amzn_reservations.csv')

    shifts = getShifts(data)
    df = pd.DataFrame(shifts)
    df.to_csv('amzn_shifts.csv')

    return df

def getPaycomData():
    session = getSession('Paycom')
    test = f'https://www.paycomonline.net/v4/cl/web.php/scheduling/api/manage-schedules/employee-shift?startDate={fromDate}&endDate={toDate}&skip=0&take=500&q=&filterInstanceId=52766f934b3d48d8a1df9db39eb537&filterName=cl-manage-scheds&scheduleGroupCode=2237'
    response = session.get(test)
    if 'not logged' in response.text:
        getPaycomCookies()
        session = getSession('Paycom')

    employeedf = getPaycomEmployees(session)
    shiftdf = getPaycomShifts(session)
    
    return employeedf, shiftdf

def getComparison(paycomshift, employeedata, amzlshift):
    paycomData = pd.merge(paycomshift, employeedata, how='left', on=["employeeCode"])

    output = pd.merge(paycomData, amzlshift, how='left', left_on=['workEmail','startDate'], right_on=['driverEmail','date'])
    output.to_csv(os.path.join(desktop, 'comparison.csv'))  


try:
    amzlshiftdf = getAMZLData()
except Exception as e:
    logging.error("amzl data fail", exc_info = True)

try:
    employeedf, paycomshiftdf = getPaycomData()
except Exception as e:
    logging.error("paycom data fail", exc_info = True)    

try:
    getComparison(paycomshiftdf, employeedf, amzlshiftdf)
except Exception as e:
    logging.error("comparison fail", exc_info = True)

