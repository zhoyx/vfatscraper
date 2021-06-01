from bs4 import BeautifulSoup as bs
import datetime
import requests
import json
from datetime import datetime
import urllib3
import time
import logging
import os
from os import environ

WEBHOOK = environ['WEBHOOK']
DELAY = environ['DELAY']

logging.basicConfig(filename='VFATscraperlog.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s', level=logging.DEBUG)

PROJECTS = {
    "all": [],
    "bsc": [],
    "polygon": [],
    "xdai":[],
    "avax":[],
    "fantom":[],
}

#scrapes "https://vfat.tools/" pages and outputs result as objects
def scraper(chain):
    base_url = "https://vfat.tools"

    projectnames =[]
    projecttokens = []
    projectlinks = []

    items = []

    r = requests.get("https://vfat.tools/{}/".format(chain))
    soup = bs(r.text, 'html.parser')
    # currently website loads a JS script to load in pool provider data, hence have to find this script
    scripts = soup.find_all('script')
    link_r = [x.get("src") for x in scripts if x.get("src") != None and x.get("src").startswith("/js/{}.".format(chain))]

    response = requests.get(base_url+link_r[0])
    list1 = response.text
    list1 = list1.split('"rows": [')[1]
    list1 = list1.split('}')[0]
    list1 = list1.replace('\n', '')
    list1 = list1.replace(' ', '')
    list1 = list1.split(']')
    list1 = [x.split(',') for x in list1]
    for index,x in enumerate(list1):
        try:
            if list1[index][0] != '':
                pool = list1[index][0].replace('"', '')
                projectnames.append(pool.replace("[",'')) 
            else:
                pool = list1[index][1].replace('"', '')
                projectnames.append(pool.replace("[",''))
            projectlinks.append(list1[index][-1].replace('"', ''))
            projecttokens.append(list1[index][-2].replace('"', ''))
        except:
            pass
    
    output = [list(x) for x in zip(projectnames, projectlinks, projecttokens)]
    for item in output:
        output_item = {
            'name': item[0], 
            'URL': item[1], 
            'token': item[2]}
        items.append(output_item)

    
    logging.info(msg='Successfully scraped site!')
    print('Successfully scraped {} page!'.format(chain))

    return items



def test_webhook(): # Sends a test webhook
    data = {
        "username": "VFat Scraper",
        "embeds": [{
            "title": "Starting Up Scraper",
            "description": "test",
            "color": int(5172613),
            "timestamp": str(datetime.utcnow())
        }]
    }

    result = requests.post(WEBHOOK, data=json.dumps(data), headers={"Content-Type": "application/json"})
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error(msg=err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))
        logging.info(msg="Payload delivered successfully, code {}.".format(result.status_code))

def discord_webhook(title, description, name, url, token, color): # Sends webhook notification to specified webhook URL
    data = {
        'username': "VFat Scraper",
        'embeds': [{
            'title': title,
            'description': description,
            'color': int(color),
            'timestamp': str(datetime.utcnow()),
            'fields': [
                {'name': 'Project Name', 'value': name},
                {'name': 'Project URL', 'value': url},
                {'name': 'Project Token', 'value': token}
            ]
        }]
    }
    
    result = requests.post(WEBHOOK, data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error(msg=err)
    else:
        print("New project added! Payload delivered successfully, code {}.".format(result.status_code))
        logging.info(msg="Payload delivered successfully, code {}.".format(result.status_code))



def checker(project, chain): #returns Boolean regarding project status
    return project in PROJECTS[chain]


def comparator(item, start, chain):
    output_item = [item['name'], item['URL'], item['token']]
    if checker(output_item, chain) == True:
        pass
    else:
        PROJECTS[chain].append(output_item)
        if start == 0:
            print('Sending notification to Discord...')
            dictOfColors = {
                "all": 16224321,
                "bsc": 13818639,
                "polygon": 6883479,
                "xdai":13429692,
                "avax": 16711680,
                "fantom":255,
            }
            discord_webhook(
                title = 'New Entry Detected on {}!'.format(chain),
                description = '\b',
                name = output_item[0],
                url = output_item[1],
                token = output_item[2],
                color = dictOfColors[chain])
        


def monitor(): #initiates monitor
    print('STARTING MONITOR')
    logging.info(msg='Successfully started monitor')

    # Tests webhook URL
    test_webhook()

    # Ensures that first scrape does not notify all products
    start = 1

    while True:
        for chain in PROJECTS:
            items = scraper(chain)
            for item in items:
                try:
                    comparator(item, start, chain)
                except Exception as e:
                    pass
        
        print("Completed Scan")
        start = 0

        time.sleep(float(DELAY))



if __name__ == '__main__':
    urllib3.disable_warnings()
    monitor()
