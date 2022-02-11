# Version Dashboard Cluster Info
# Jason Fowler, 2020

# The goal is to obtain a list of images from a remote cluster
# using an API key and hostname

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv
load_dotenv()
import os
import logging
import datetime
import json
import time
import uuid
import re
import boto3
dynamodb = boto3.resource('dynamodb')
import urllib3
urllib3.disable_warnings()

# set to True for connection debugging etc
debug = False

# set up logging
logger = logging.getLogger('script')
ch = logging.StreamHandler()
if debug:
    logger.setLevel(logging.DEBUG)
    ch.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# K8S Settings
# set to namespace for micro-services, typically 'default'
namespace = "default"

# this is the EKS Admin token - will need to set to EKS Read-Only
#  ** for each cluster! **
apitoken = os.environ.get("API_TOKEN")

configuration = client.Configuration()
configuration.host = os.environ.get("CLUSTER_HOST")
# could be noisy setting to True
configuration.verify_ssl=False
# set to true to debug connection headers, etc
configuration.debug = debug
configuration.api_key={"authorization":"Bearer "+ apitoken}
client.Configuration.set_default(configuration)
kubeApi = client.CoreV1Api()

# create empty list to put pods from cluster into
podlist = set()

def postDB(applist):
    timestamp = str(time.time())
    # create post to add to collection in DynamoDB
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    post = {
        'id': str(uuid.uuid1()),
        "cluster": os.environ.get("EPCC_ENV"),
        'images': applist,
        'checked': False,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }
    try:
        table.put_item(Item=post)
        logger.info("Posted to DynamoDB")
        response = {
            "statusCode": 200,
            "body": json.dumps(post)
        }
        return response
    except Exception as e:
        logger.critical("Exception posting to DB: %s\n" % e)
        return False

def getImages():
    # get all pods running on cluster
    try:
        allPods = kubeApi.list_namespaced_pod(namespace,watch=False)
        logger.info("Retrieving list of images from %s", configuration.host)
        for item in allPods.items :
            #pprint(item.metadata.name, item.status.container_statuses[0].image)
            podlist.add(item.status.container_statuses[0].image)
    except ApiException as e:
        logger.critical("Exception retrieving list of images: %s\n" % e)

    # strip out cruft from list of apps from original entry:
    #'quay.io/moltin/inventories.svc.molt.in:commit-9255353ec3c623ca2150edfbb7058a59a381b8d3'
    # and commit hashes to limit posting to db as:
    # service:<commit-hash>
    # TODO: create env var for "docker_registry" in case we move away from quay.io
    if podlist:
        appregex = re.compile("quay.*")
        servicelist = list(filter(appregex.match, podlist))
        applist = [re.sub(r'quay.io/moltin/', '', i) for i in servicelist]
        applist = [re.sub(r'.svc.molt.in:commit-', ':', i) for i in applist]
        applist = [re.sub(r'.svc:commit-', ':', i) for i in applist]
        applist = [re.sub(r'.svc.molt.in', '', i) for i in applist]
        #pprint(applist)
        postDB(applist)
    else:
        logger.critical("No pods running on cluster or unable to authenticate: %s\n" % e)

def main(event, context):
    getImages()
