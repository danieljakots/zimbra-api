#!/usr/bin/env python3

import datetime
import getpass
import json
import os
import pickle
import sys
import time

# besoin d'installer py3-requests (OpenBSD) - python3-requests (Debian)
import requests
from requests.auth import HTTPBasicAuth

COOKIES_FILE = "/path/to/cookies"
zimbra_domain = "example.com"
url_zimbra = "https://" + zimbra_domain + "/zimbra/"
# laisse vide si ton user unix == ton user zimbra
USER = ""


def save_cookies(requests_cookiejar):
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(requests_cookiejar, f)


def load_cookies():
    with open(COOKIES_FILE, 'rb') as f:
        return pickle.load(f)


def date_cookies(filename):
    try:
        cookie_epoch = int(os.path.getmtime(filename))
    except FileNotFoundError:
        return 21601
    now = int(time.time())
    return now - cookie_epoch


def get_login():
    if not USER:
        login = os.environ['USER']
        print("Connexion avec " + login)
    else:
        login = USER
    return login


def log_in(login, url_zimbra):
    passwd = getpass.getpass()
    with requests.Session() as s:
        p = s.get(url_zimbra + "home/" + login + "@" + zimbra_domain
                  + "/Inbox/?fmt=sync&auth=sc",
                  auth=HTTPBasicAuth(login, passwd))
        print(p.status_code)
        if p.status_code == 200:
            save_cookies(s.cookies)


def ensure_login(login):
    if date_cookies(COOKIES_FILE) > 21600:
        print("Pas de cookies en cours de validité trouvé")
        log_in(login, url_zimbra)
    else:
        print("cookies encore valides")


def get_calendar(login):
    today = datetime.date.today().strftime('%Y/%m/%d')
    tomorrow = (datetime.datetime.now()
                + datetime.timedelta(days=1)).strftime('%Y/%m/%d')
    with requests.Session() as s:
        p = s.get(url_zimbra + "home/" + login
                  + "/calendar?fmt=json&auth=co&start=" + today + "&end="
                  + tomorrow, cookies=load_cookies())
    if p.status_code != 200:
        sys.exit(1)
    data = json.loads(p.text)
    try:
        for appt in data["appt"]:
            name = appt["inv"][0]["comp"][0]["name"]
            print("Rendez vous : " + name)
            print("Créé par "
                  + appt["inv"][0]["comp"][0]["or"]["a"].split('@')[0])
            try:
                for participant in appt["inv"][0]["comp"][0]["at"]:
                    print("Participant-e : " + participant["a"].split('@')[0])
            except KeyError:
                print("Pas de participant-e")
            print("epoch début "
                  + str(int(appt["inv"][0]["comp"][0]["s"][0]["u"] / 1000)))
    except KeyError:
                print("Rien de prévu")


def main():
    login = get_login()
    ensure_login(login)
    get_calendar(login)


if __name__ == "__main__":
    main()
