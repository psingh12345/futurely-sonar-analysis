import json
from django.conf import settings
import requests
import logging
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

# hubspotContactupdateQueryAdded
def create_update_contact_hubspot(email, keys_list, values_list):
    properties = []
    data_dict = {}
    try:
        logger.info(f"In hubspot sns module for : {email}")
        for idx in range(len(keys_list)):
            data_dict["property"] = keys_list[idx]
            data_dict["value"] = values_list[idx]
            properties.append(data_dict.copy())
            data_dict.clear()
        final_data_dict = {"properties" : properties}
        data=json.dumps(final_data_dict)
        print(f"Date after dump : {data}")
        print(final_data_dict["properties"][0]["value"])
        response = settings.CLIENT.publish(
            TopicArn='arn:aws:sns:eu-south-1:994790766462:lambdasns', 
            Message = data
        )
        logger.info(f"In hubspot sns triggered with response {response} for : {email}")
    except Exception as ex:
        logger.critical(f"Error at hubspot SNS module for parameter update {ex} for user : {email}")