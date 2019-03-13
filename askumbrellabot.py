# Copyright (C) 2019  Alexandre Argeris

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
 
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
 
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/


import requests
import json
import sys
import re
import time
import datetime

from json2html import *

try:
    from flask import Flask
    from flask import request
except ImportError as e:
    print(e)
    print("Looks like 'flask' library is missing.\n"
          "Type 'pip3 install flask' command to install the missing library.")
    sys.exit()

requests.packages.urllib3.disable_warnings()

# Please modify with your Bot ACCESS TOKEN
bearer = 'YOUR-BOT-ACCESS-TOKEN-HERE'

# Please enter your webex-teams logs room
logs_roomId = 'YOUR-roomId-FOR-LOGS-HERE'

# Please modify with your Umbrella Investigate token
UMB_Investigate_token = 'UMBRELLA-INVESTIGATE-TOKEN-HERE'

# Please modify with your Webex Teams Domain name
webex_domain = 'YOUR-WEBEX_TEAM-DOMAIN-NAME-HERE'

# Please modify with your admin email address
admin_email = 'YOUR-ADMIN-EMAIL-ADDRESS-HERE'

# Please modify with your webhook listening TCP port
webhook_port = '4980'

# Log file location and prefix 'Example : /var/log/webexteams-bot-'
log_directory = ''
log_prefix = 'askumbrellabot'

headers = {"Accept": "application/json", "Content-Type": "application/json; charset=utf-8", "Authorization": "Bearer " + bearer}

expected_messages = {"help me": "help",
                     "need help": "help",
                     "can you help me": "help",
                     "ayuda me": "help",
                     "help": "help",
                     "greetings": "greetings",
                     "hello": "greetings",
                     "hi": "greetings",
                     "how are you": "greetings",
                     "what's up": "greetings",
                     "what's up doc": "greetings"}

def send_spark_get(url, payload=None, js=True):
    if payload is None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js is True:
        request = request.json()
    return request

def send_spark_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request

def help_me():
    return "Sure! I can help. Below are the commands that I understand:<br/>" \
           "`help me` - I will display what I can do.<br/>" \
           "`hello` - I will display my greeting message<br/>" \
           "`domain:` - Enter the domain to query - Example 'domain: internetbadguys.com'<br/>" \
           "`toplist XX` - I will display the top Umbrella Popularity Domain List - Global list - Ex: toplist 25'<br/>"           

def greetings():
    return "Hi my name is {}.<br/>" \
           "I'm currently integrated with Cisco Umbrella Threat Intelligence - Investigate <br/>" \
           "This Bot is run by {} - script avaialble upon request <br/>" \
           "Type `Help me` to see what I can do.<br/>".format(bot_name,admin_email)

def umbrella_get(varDOMAIN, roomType, room_title, today, timestamp, personEmail):
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')
        var_HEADERS = {
            'Authorization': "Bearer %s" % UMB_Investigate_token,
            }

        var_URL_CATEGORIES = "https://investigate.api.umbrella.com/domains/categorization/" + varDOMAIN
        var_LABELS = {"showLabels":""}
        var_RESPONSE_CATEGORIES = requests.request("GET", var_URL_CATEGORIES, headers=var_HEADERS, params=var_LABELS)
        var_OUTPUT0 = var_RESPONSE_CATEGORIES.text
	
        re1='.*?'	# Non-greedy match on filler
        re2='([-+]\\d+)'	# Integer Number 1
        rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT0)
        if m:
            sec_status = m.group(1)
        else:
            re1='.*?'	# Non-greedy match on filler
            re2='(\\d+)'	# Integer Number 1
            rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
            m = rg.search(var_OUTPUT0)
            sec_status = m.group(1)

        re1='.*?'	# Non-greedy match on filler
        re2='(\\[.*?\\])'	# Square Braces 1
        rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT0)
        sec_cat = m.group(1)
         
        re1='.*?'	# Non-greedy match on filler
        re2='\\[.*?\\]'	# Uninteresting: sbraces
        re3='.*?'	# Non-greedy match on filler
        re4='(\\[.*?\\])'
        rg = re.compile(re1+re2+re3+re4,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT0)
        web_cat=m.group(1)

        var_URL_RISK = "https://investigate.api.umbrella.com/domains/risk-score/" + varDOMAIN
        var_RESPONSE_RISK = requests.request("GET", var_URL_RISK , headers=var_HEADERS)
        var_OUTPUT1 = var_RESPONSE_RISK.text
        re1='.*?'
        re2='(\\d+)'
        rg = re.compile(re1+re2,re.IGNORECASE|re.DOTALL)
        m = rg.search(var_OUTPUT1)
        risk_level = m.group(1)

        f = open((log_directory+log_prefix+'-'+today+'.log'), "a")
        time.sleep(5)
        f.write(timestamp +", "+personEmail+", RoomType: " +roomType+", Room Name: "+room_title+", Answer: Security Status= " +sec_status+", Risk Level= "+risk_level+", Security_Cat= "+sec_cat+", Web_Cat= "+web_cat+'\n')
        msg = "Cisco Umbrella Investigate result for {} :<br/>" \
              "Domain Security Status = [ {} ] (-1 = malicious, 1 = benign, 0 = not classified)<br/>" \
              "Domain Risk Level = [ {} ] (0=no risk at all, 100 highest risk)<br/>" \
              "Domain Security Categories : {} <br/>" \
              "Domain Web Categories : {} <br/>".format(varDOMAIN, sec_status, risk_level, sec_cat, web_cat)
        return "{}".format(msg)

def umbrella_toplist(top, roomType, room_title, today, timestamp, personEmail):
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')
        top_int = int(top)
        if top_int > 101:
                  return "Cisco Umbrella Top domains - Global List<br/>" \
                         "Please request a number between 0- 100 <br/>"
        elif top_int < 0:
                  return "Cisco Umbrella Top domains - Global List<br/>" \
                         "Please request a number between 0- 100 <br/>"
        else:
            var_HEADERS = {
            'Authorization': "Bearer %s" % UMB_Investigate_token,
            }

            var_URL = "https://investigate.api.umbrella.com/topmillion?limit="+top
            get_toplist = requests.request("GET", var_URL, headers=var_HEADERS)
            toplist = get_toplist.text
            toplist_json = get_toplist.json()
            return "Cisco Umbrella Top {} domains - Global List<br/>" \
                   "{}<br/>".format(top, (json2html.convert(json = toplist_json)))


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def spark_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        #print(json.dumps(webhook, indent=4))
        today = datetime.datetime.today()
        timestamp = today.strftime('%Y-%m-%d %H:%M:%S')
        date = datetime.date.today()
        today = date.strftime('%Y-%m-%d')
        if (webhook['resource'] == "memberships") and (webhook['event'] == "created") and (webhook['data']['personEmail'] == bot_email):
            msg = ""
            msg = greetings()
            send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})

        elif ("@webex.bot" not in webhook['data']['personEmail']) and (webhook['resource'] == "messages"):
            result = send_spark_get('https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
            roomId_query = send_spark_get('https://api.ciscospark.com/v1/rooms/{0}'.format(webhook['data']['roomId']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower() + " ", '')
            personEmail =  result.get('personEmail', '')
            roomType = result.get('roomType', '')
            room_title = roomId_query.get('title', '')
            emaildomain = personEmail.split('@')[1]
            #print (result)
            f = open((log_directory+log_prefix+'-'+today+'.log'), "a")
            #print ("print command to log")
            f.write(timestamp +", "+personEmail+", RoomType: " +roomType+", Room Name: "+room_title+", Command: " +in_message + '\n')
            msg = ""

            if in_message in expected_messages and expected_messages[in_message] is "help":
                msg = help_me()

            elif in_message in expected_messages and expected_messages[in_message] is "greetings":
                msg = greetings()

            elif emaildomain != webex_domain:
                msg = 'Sorry but you are not allow to use this Bot, please contact {} for more informations'.format(admin_email)

            elif in_message.startswith("domain:"):
                domain = in_message.split(' ')[1].lower()
                msg = umbrella_get(domain, roomType, room_title, today, timestamp, personEmail) 

            elif in_message.startswith("domain"):
                domain = in_message.split(' ')[1].lower()
                msg = umbrella_get(domain, roomType, room_title, today, timestamp, personEmail)

            elif in_message.startswith("toplist"):
                top = in_message.split(' ')[1].lower()
                msg = umbrella_toplist(top, roomType, room_title, today, timestamp, personEmail)

            elif in_message.startswith("top"):
                top = in_message.split(' ')[1].lower()
                msg = umbrella_toplist(top, roomType, room_title, today, timestamp, personEmail)

            else:
                msg = "Sorry, but I did not understand your request. Type `Help me` to see what I can do"

            if msg is not None:
                send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})
                log = (timestamp+", "+personEmail+", RoomType: " +roomType+", Room Name: "+room_title+', Command: '+in_message)
                anwser = ("Anwser : <br/>" \
			  "{}".format(msg))
                send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": logs_roomId, "text": log})
                send_spark_post("https://api.ciscospark.com/v1/messages", {"roomId": logs_roomId, "markdown": anwser})

        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Spark Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Don't forget to create Webhooks to start receiving events from Cisco Spark!</i></b></center>" % bot_name
        return message

def main():
    global bot_email, bot_name
    if len(bearer) != 0:
        test_auth = send_spark_get("https://api.ciscospark.com/v1/people/me", js=False)
        if test_auth.status_code == 401:
            print("Looks like the provided access token is not correct.\n"
                  "Please review it and make sure it belongs to your bot account.\n"
                  "Do not worry if you have lost the access token. "
                  "You can always go to https://developer.ciscospark.com/apps.html "
                  "URL and generate a new access token.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName", "")
            bot_email = test_auth.get("emails", "")[0]
    else:
        print("'bearer' variable is empty! \n"
              "Please populate it with bot's access token and run the script again.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.ciscospark.com/apps.html "
              "URL and generate a new access token.")
        sys.exit()

    if "@webex.bot" not in bot_email:
        print("You have provided an access token which does not relate to a Bot Account.\n"
              "Please change for a Bot Account access toekneview it and make sure it belongs to your bot account.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.ciscospark.com/apps.html "
              "URL and generate a new access token for your Bot.")
        sys.exit()
    else:
        app.run(host='0.0.0.0', port= webhook_port)

if __name__ == "__main__":
    main()
