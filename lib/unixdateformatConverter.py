import datetime

def unixdateformat(datetoconvert):
    DateFormatedToday = datetime.datetime(datetoconvert.year, datetoconvert.month, datetoconvert.day)
    epochUTC = datetime.datetime.utcfromtimestamp(0)
    UnixtimeStamp=(DateFormatedToday - epochUTC).total_seconds() * 1000.0
    return str(int(UnixtimeStamp))
