import re
import pymongo
import time
import requests
from requests import session
import json
import html
from dateutil.parser import parse
from dateutil import tz
import secrets
username = secrets.username
password = secrets.password
url = secrets.url
dbsecret = secrets.dbsecret
def sendPayload(postObj):
    data = {}
    dt = parse(postObj['created_at'])
    central = dt.astimezone(tz.gettz('America/Chicago'))
    day = central.strftime('%m/%d/%Y %H:%M') + ' CST'

    data["content"] = "New **" +  postObj['category'] + "** post: " + day
    data["username"] = "EDSTEM BOT"
    data["embeds"] = []

    embed = {}
    embed["description"] = html.unescape(re.sub('<[^<]+?>', '', str(postObj['document'])))
    embed["title"] =  html.unescape(re.sub('<[^<]+?>', '', str(postObj['title'])))
    embed["url"] = "https://edstem.org/us/courses/3413/discussion/"  + str(postObj['id'])
    embed["color"] = 0XF0BAFF
    data["embeds"].append(embed)
    result = requests.post(url, json=data, headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
        time.sleep(5)
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("succ {}.".format(result.status_code))

def getEdstemPosts():
  payload = {
      'action': 'login',
      'username': username,
      'password': password
  }

  tPayload = {"login":username,"password":password}
  with session() as c:
      c.post('https://edstem.org/us/login', data=payload)
      # cookie = h.headers['Set-Cookie']
      # headers2 = {"cookie": cookie, "origin": "https://edstem.org", "connection": "keep-alive", "content-type": "application/json", "accept": "*/*", "accept-encoding": "gzip, deflate, br"}
      check = c.post('https://us.edstem.org/api/token',json=tPayload)
      token = json.loads(check.text)['token']

      headers = {"origin": "https://edstem.org", "x-token": token}
      response = c.get('https://us.edstem.org/api/courses/3413/threads?limit=10&sort=date&order=desc', headers=headers)
      posts = json.loads(response.text)['threads']
      return posts



def edstem(event, context):
    client = pymongo.MongoClient(dbsecret)
    db = client.get_database('edstem')
    table = db.posts
    existingPosts = []
    query = table.find()
    print(query)
    output = {}
    i = 0
    for x in query:
        output[i] = x
        output[i].pop('_id')
        existingPosts.append(output[i]['ID'] )
        i += 1
    print(existingPosts)
    posts = getEdstemPosts()
    for post in posts:
        postId = post['id']
        if postId not in existingPosts:
            print(postId)
            queryObject = {
                'ID': postId,
            }
            queryMongo = table.insert_one(queryObject)
            sendPayload(post)

        else:
            print("edstem channel up to date")
    return {
        'statusCode': 200,
        'body': json.dumps('hey')
    }







