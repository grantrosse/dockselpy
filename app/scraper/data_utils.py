import pandas as pd
import os

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