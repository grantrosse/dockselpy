from scraper.scrapers import AmazonScraper, PaycomScraper
import scraper.data_utils
from scraper.database import init_db, db_session, rowInsert
from datetime import datetime, timedelta
import pandas as pd
import logging
from dotenv import load_dotenv

load_dotenv()

#create tables/set up base for ORM
init_db()
from scraper.models import Test, Employees, ScheduleRecon

logging.basicConfig(filename='pladlog.log',format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.captureWarnings(True)


fromDate = datetime.today().strftime('%Y-%m-%d')
toDate = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d')


AMZL = AmazonScraper(f'https://logistics.amazon.com/scheduling/home/api/v2/rosters?fromDate={fromDate}&serviceAreaId=6f0c423f-f609-4e32-a7f1-e624143b9d49&toDate={toDate}')
PAY = PaycomScraper('https://www.paycomonline.net/v4/cl/web.php/scheduling/api/manage-schedules/employee?skip=0&take=100&q=&filterInstanceId=f1f61f69ac734e5c81c3027684388a&filterName=cl-manage-scheds',\
                        f'https://www.paycomonline.net/v4/cl/web.php/scheduling/api/manage-schedules/employee-shift?startDate={fromDate}&endDate={toDate}&skip=0&take=500&q=&filterInstanceId=52766f934b3d48d8a1df9db39eb537&filterName=cl-manage-scheds&scheduleGroupCode=2237')


try:
    if AMZL.authorize():
        amzlReservationsdf = pd.DataFrame(AMZL.getReservations())
        amzlReservationsdf.to_csv('amzn_reservations.csv')

        amzlShiftsdf = pd.DataFrame(AMZL.getShifts())
        amzlShiftsdf.to_csv('amzn_shifts.csv')
    else:
        logging.error("amazon authorization fail")   
        scraper.data_utils.sendEmail("amazon authorization fail", False)   
        AMZL.driver.quit()  

except Exception as e:
    logging.error("amzl scrape fail", exc_info = True) 
    scraper.data_utils.sendEmail("amazon scrape fail", False)
    AMZL.driver.quit()

# try:
#     if PAY.authorize():
#         paycomEmployeedf = pd.DataFrame(PAY.getEmployees())
#         paycomEmployeedf.to_csv('paycom_employees.csv')

#         paycomShiftdf = pd.DataFrame(PAY.getShifts())
#         paycomShiftdf.to_csv('paycom_shifts.csv')
#     else:
#         logging.error("paycom authorization fail")
#         scraper.data_utils.sendEmail("paycom authorization fail", False)
#         PAY.driver.quit()
        
# except Exception as e:
#     logging.error("paycom scrape fail", exc_info = True)
#     scraper.data_utils.sendEmail("paycom scrape fail", False) 
#     PAY.driver.quit()

# try:
#     compdf = scraper.data_utils.getComparison(paycomShiftdf, paycomEmployeedf, amzlShiftsdf, False)
# except Exception as e:
#     logging.error("comparison fail", exc_info = True)
#     scraper.data_utils.sendEmail("comparison fail", False)



###insert into DB
# array = PAY.getEmployees()
# employeeInsert=[]
# for item in array:
#     employeeInsert.append({'email': item['workEmail'],
#                             'firstName': item['firstName'],
#                             'lastName': item['lastName'],
#                             'paycomEmployeeCode': item['employeeCode'],
#                             'phoneNumber': item['primaryPhone'],
#                             'personalEmail': item['personalEmail']
#                             })
# rowInsert(Employees, employeeInsert)

# compInsert = []
# for row in compdf.itertuples():
#     compInsert.append({'startDate': row.startDate, #datetime.strptime(row.startDate, '%m/%d/%Y %H:%M:%S'),
#                         'email': row.workEmail,
#                         'firstName': row.firstName,
#                         'lastName': row.lastName,
#                         'shiftDescription': row.description,
#                         'phoneNumber': row.primaryPhone,
#                         'personalEmail': row.personalEmail,
#                         'amazonShiftType': row.shiftName,
#                         })
# rowInsert(ScheduleRecon, compInsert)

scraper.data_utils.sendEmail("successful run", True)

db_session.remove()