""" Hubspot API wrapper """
import urllib
import requests
import json


class HubspotApi():
    """Hubspot API class """
    api_key = "8ca152ea-d372-43d1-ad2e-d2ed05ba455d"

    def get_analytics_data_breakdowns(self, breakdown_by='totals', time_period="total"):
        """Analytics data breakdown"""
        try:
            request_url = "https://api.hubapi.com/analytics/v2/reports/{0}/{1}?hapikey={2}&start=20180101&end=20180301".format(
                breakdown_by, time_period, self.api_key)
            response = requests.get(request_url)
            json_response = response.json()
            return json_response
        except Exception as error:
            raise Exception(
                {"HubspotApi.get_analytics_data_breakdowns.error: ": str(error)})

    def get_analytics_data_by_object(self, object_type='pages', time_period="total"):
        """Analytics data by Object type"""
        try:
            request_url = "https://api.hubapi.com/analytics/v2/reports/{0}/{1}?hapikey={2}&start=20180101&end=20180301".format(
                object_type, time_period, self.api_key)
            response = requests.get(request_url)
            json_response = response.json()
            return json_response
        except Exception as error:
            raise Exception(
                {"HubspotApi.get_analytics_data_by_object.error: ": str(error)})
