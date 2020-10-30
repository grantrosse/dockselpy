import pandas as pd
import os
import smtplib
import imaplib
import email
import re
from email.message import EmailMessage
import logging
# from .scrapers import AmazonScraper
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver import ActionChains
import time

log = logging.getLogger(__name__)

# desktopPath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

def getComparison(paycomshift, employeedata, amzlshift, debug=False):
    ##merge so we can correlate the shift data to the pladcloud email
    paycomData = pd.merge(paycomshift, employeedata, how='left', on=["employeeCode"])
    ##fix dates for merge
    paycomData['startDate'] = pd.to_datetime(paycomData['startDate']).dt.date
    amzlshift['date'] = pd.to_datetime(amzlshift['date']).dt.date

    if debug:
        paycomData.to_csv('paycomdata.csv')
        amzlshift.to_csv('amzlshift.csv')
        print(paycomData.head(10))
        print(amzlshift.head(10))

    output = pd.merge(paycomData, amzlshift, how='left', left_on=['workEmail','startDate'], right_on=['driverEmail','date'])

    output = output[output.workEmail.notnull()]
    output = output.fillna("") ##was inserting nan values causing an error for SQL insert

    # output.to_csv(os.path.join(desktopPath, 'comparison.csv'))  
    output.to_csv('comparison.csv')  
    return output

def sendEmail(message, success):
    msg = EmailMessage()

    sent_from = os.getenv('ERROREMAIL')
    to = os.getenv('CLIENTEMAIL')
    subject = f"SUCCESS - Scrape Processed for {os.getenv('CLIENTNAME')}" if success else f"CRITICAL - Scrape Failed for {os.getenv('CLIENTNAME')}"
    body = f"Hello,\nPlease rerun scraper for {os.getenv('CLIENTNAME')}\nerror message:{message}\n\n- PLADcloud Team" if not success else f"Hello,\nScraper successfully run for {os.getenv('CLIENTNAME')}\n\n- PLADcloud Team"

    msg.set_content(body)

    msg['Subject'] = subject
    msg['From'] = sent_from
    msg['To'] = to

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(os.getenv('ERROREMAIL'), os.getenv('ERROREMAILPASSWORD'))
        server.send_message(msg)
        server.close()
        log.info(f"sent email to {os.getenv('CLIENTNAME')}")
        return True
    except:
        log.error(f"email to {os.getenv('CLIENTNAME')} failed")
        return False

def getApprovalLink():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(os.getenv('EMAIL'), os.getenv('PASS'))
    mail.select("inbox") 
    result, data = mail.search(None, '(FROM "account-update@amazon.com" UNSEEN)' )

    ids = data[0] # data is a list.
    id_list = ids.split() # ids is a space separated string
    latest_email_id = id_list[-1] # get the latest
    result, data = mail.fetch(latest_email_id, "(RFC822)") 
    raw_email = data[0][1]
    msg = email.message_from_bytes(data[0][1])

    nospaces = "".join(str(msg).split())
    log.info(nospaces)
    link = re.search(r'(https://www.amazon.com/a/c/r\?.+)</a',nospaces).group(1)

    mail.close()

    return link





