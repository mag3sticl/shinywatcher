import mapadroid.utils.pluginBase
from functools import update_wrapper, wraps
from flask import render_template, Blueprint, jsonify
from mapadroid.madmin.functions import auth_required
from threading import Thread
import os
import sys
import time
from datetime import datetime
# from dateutil import tz
import requests
import json


class ShinyWatcher(mapadroid.utils.pluginBase.Plugin):
    """This plugin is just the identity function: it returns the argument
    """
    def __init__(self, mad):
        super().__init__(mad)

        self._rootdir = os.path.dirname(os.path.abspath(__file__))

        self._mad = mad

        self._pluginconfig.read(self._rootdir + "/plugin.ini")
        self._versionconfig.read(self._rootdir + "/version.mpl")
        self.author = self._versionconfig.get("plugin", "author", fallback="unknown")
        self.url = self._versionconfig.get("plugin", "url", fallback="https://www.maddev.eu")
        self.description = self._versionconfig.get("plugin", "description", fallback="unknown")
        self.version = self._versionconfig.get("plugin", "version", fallback="unknown")
        self.pluginname = self._versionconfig.get("plugin", "pluginname", fallback="https://www.maddev.eu")
        self.staticpath = self._rootdir + "/static/"
        self.templatepath = self._rootdir + "/template/"

        self._routes = [
            ("/mswreadme", self.mswreadme_route),
        ]

        self._hotlink = [
            ("Plugin Readme", "/mswreadme", "ShinyWatcher - Readme Page"),
        ]

        if self._pluginconfig.getboolean("plugin", "active", fallback=False):
            self._plugin = Blueprint(str(self.pluginname), __name__, static_folder=self.staticpath,
                                     template_folder=self.templatepath)

            for route, view_func in self._routes:
                self._plugin.add_url_rule(route, route.replace("/", ""), view_func=view_func)

            for name, link, description in self._hotlink:
                self._mad['madmin'].add_plugin_hotlink(name, self._plugin.name+"."+link.replace("/", ""),
                                                       self.pluginname, self.description, self.author, self.url,
                                                       description, self.version)

    def perform_operation(self):
        """The actual implementation of the identity plugin is to just return the
        argument
        """

        # do not change this part ▽▽▽▽▽▽▽▽▽▽▽▽▽▽▽
        if not self._pluginconfig.getboolean("plugin", "active", fallback=False):
            return False
        self._mad['madmin'].register_plugin(self._plugin)
        # do not change this part △△△△△△△△△△△△△△△

        # do not start plugin when in config mode
        if self._mad['args'].config_mode == True:
            self._mad['logger'].info("Plugin - ShinyWatcher is not aktive while configmode")
            return False

        # create shiny_history table in db, if it does not already exist
        try:
            dbstatement = "CREATE TABLE IF NOT EXISTS shiny_history(encounter_id BIGINT UNSIGNED NOT NULL)"
            self._mad['logger'].debug("DB call: " + dbstatement)
            results = self._mad['db_wrapper'].execute(dbstatement, commit=True)
            self._mad['logger'].debug("DB results: " + str(results))
        except:
            self._mad['logger'].info("Plugin - ShinyWatcher had 'no result set to fetch from' exception")

        # populate shiny_history table with existing shiny encounters, if they do not yet exist in the history table
        try:
            dbstatement = "INSERT INTO shiny_history (encounter_id) SELECT pokemon.encounter_id FROM pokemon LEFT JOIN trs_stats_detect_mon_raw t ON pokemon.encounter_id = t.encounter_id WHERE t.is_shiny = 1 and pokemon.encounter_id NOT IN (SELECT encounter_id FROM shiny_history)"
            self._mad['logger'].debug("DB call: " + dbstatement)
            results = self._mad['db_wrapper'].execute(dbstatement, commit=True)
            self._mad['logger'].debug("DB results: " + str(results))
        except:
            self._mad['logger'].info("Plugin - ShinyWatcher had exception when trying to populate shiny_history with existing pokmeon")

        # read config parameter
        self._workers: dict = {}

        self._timzone_offset = datetime.now() - datetime.utcnow()
        self._language = self._pluginconfig.get("plugin", "language", fallback='en')
        self._os = self._pluginconfig.get("plugin", "OS", fallback=None)
        self._only_show_workers = self._pluginconfig.get("plugin", "only_show_workers", fallback=None)
        self._exlude_mons = self._pluginconfig.get("plugin", "exlude_mons", fallback=None)
        self._webhookurl = self._pluginconfig.get("plugin", "discord_webhookurl", fallback=None)
        self._mask_mail = self._pluginconfig.get("plugin", "mask_mail", fallback='no')
        self._pinguser = self._pluginconfig.get("plugin", "pinguser", fallback='no')

        self.mswThread()

        return True

    def mswThread(self):
        msw_worker = Thread(name="MadShinyWatcher", target=self.MadShinyWatcher)
        msw_worker.daemon = True
        msw_worker.start()

    def get_mon_name_plugin(self, mon_id):
        mons_file = mapadroid.utils.language.open_json_file('pokemon')
        if mon_id in mons_file:
            if self._language != "en":
                return self.i8ln_plugin(mons_file[mon_id]["name"])
            else:
                return mons_file[mon_id]["name"]
        else:
            return "No-name-in-pokemon-json"

    def i8ln_plugin(self, word):
        lang_file = 'locale/' + self._language + '/mad.json'
        if os.path.isfile(lang_file):
            with open(lang_file, encoding='utf8') as f:
                language_file = json.load(f)
            if word in language_file:
                return language_file[word]
        return word

    def do_mask_email(self, email):
        #finding the location of @
        lo = email.find('@')
        if lo > 0:
            memail = email[0] + email[1] + "*****" + email[lo-2] + email[lo-1:]
        else:
            memail = email[0] + email[1] + email[2] + "*****" + email[lo-3] + email[lo-2] + email[lo-1]
        return memail

    def strip_end_email(self, pogologin):
        pos = pogologin.rfind('.')
        stripped = pogologin
        if pos >= 0:
            stripped = pogologin[:pos]
        return stripped

    def MadShinyWatcher(self):
        devicemapping = self._mad['mapping_manager'].get_all_devicemappings()
        self._mad['logger'].debug(devicemapping)

        worker_filter = ""
        if not self._only_show_workers == "":
            self._only_show_workers = "'" + (self._only_show_workers).replace(",","','") + "'"
            worker_filter = f"AND t.worker in ({self._only_show_workers})"

        for worker in devicemapping:
            devicesettings = devicemapping[worker]
            self._mad['logger'].debug(devicesettings)
            query = (
                "SELECT name, settings_pogoauth.device_id, logintype, username FROM settings_pogoauth,"
                " settings_device WHERE settings_pogoauth.device_id = settings_device.device_id AND"
                " logintype = login_type AND name = '%s'" %
                (str(worker))
            ).format(worker_filter)
            self._mad['logger'].debug("MSW DB query: " + query)
            results = self._mad['db_wrapper'].autofetch_all(query)
            self._mad['logger'].debug("MSW DB result: " + str(results))
            loginaccount = results[0]['username'] # only one active account [0]
            self._workers[worker] = loginaccount

        while True:

            query = (
                "SELECT pokemon.encounter_id, pokemon_id, disappear_time, individual_attack,"
                " individual_defense, individual_stamina, cp, cp_multiplier, gender, longitude, latitude, t.worker" # , t.timestamp_scan
                " FROM pokemon LEFT JOIN trs_stats_detect_mon_raw t ON"
                " pokemon.encounter_id = t.encounter_id WHERE t.is_shiny = 1 AND pokemon.encounter_id"
                " NOT IN (SELECT encounter_id FROM shiny_history) {} ORDER BY pokemon_id DESC, disappear_time DESC"
            ).format(worker_filter)
            self._mad['logger'].debug("MSW DB query: " + query)
            results = self._mad['db_wrapper'].autofetch_all(query)
            self._mad['logger'].debug("MSW DB result: " + str(results))
            for result in results:

                encounterid = result['encounter_id']
                encid = str(encounterid)
                pid = str(result['pokemon_id'])

                # pokemon CP
                cpval = str(result['cp'])

                # pokemon name
                mon_name = self.get_mon_name_plugin(pid)

                if pid in self._exlude_mons:
                    self._mad['logger'].info(f"Skipping excluded shiny: {mon_name}")
                    continue

                mon_img = f"https://raw.githubusercontent.com/Plaryu/PJSsprites/master/pokemon_icon_{pid.zfill(3)}_00.png"

                self._mad['logger'].info(f"Reporting shiny: {mon_name}")

                # Pokemon gender
                gendericon = '⚪' #genderless
                gendervalue = int(result['gender'])
                if gendervalue == 1:
                    gendericon = '♂' #male
                elif gendervalue == 2:
                    gendericon = '♀' #female

                # Pokemon IV
                att = int(result['individual_attack'])
                dfn = int(result['individual_defense'])
                sta = int(result['individual_stamina'])
                iv = int(round((((att + dfn + sta) / 45) * 100), 0))

                # Pokemon level
                mon_level = 0
                cpmult = result['cp_multiplier']
                if cpmult < 0.734:
                    mon_level = round(58.35178527 * cpmult * cpmult - 2.838007664 * cpmult + 0.8539209906)
                else:
                    mon_level = round(171.0112688 * cpmult - 95.20425243)

                #### REMOVED (NOT IMPORTANT/USEFUL) # encounter/found time
                #encounterdate = datetime.fromtimestamp(result['timestamp_scan'], tz.tzlocal())
                #encountertime = encounterdate.strftime("%-I:%M:%S %p")

                # Despawn time and remaining min/sec
                despawndate = result['disappear_time']
                despawndatelocal = despawndate + self._timzone_offset
                despawntime = despawndatelocal.strftime("%-I:%M:%S %p")
                if despawndate > datetime.utcnow():
                    remainingtime = despawndate - datetime.utcnow()
                    remainingminsec = divmod(remainingtime.seconds, 60)
                else:
                    remainingminsec = "??" # the actual despawn time is unknown or occurred before this report has been processed

                # Location coords
                lat = result['latitude']
                lon = result['longitude']

                # Worker
                worker = "Unknown" # default in case worker was removed from the MAD db
                if 'worker' in result:
                    worker = result['worker']

                # PoGo user login
                pogologin = ""
                if worker in self._workers:
                    pogologin = self._workers[worker]
                if self._mask_mail == 'yes':
                    pogologin = self.do_mask_email(pogologin)
                elif self._mask_mail == 'total':
                    pogologin = '**@*.*'
                else:
                    pogologin = self.strip_end_email(pogologin)
                self._mad['logger'].info(f"Pogo Login set for {worker}:{pogologin}")

                if self._pinguser == 'yes':
                    worker = self._pluginconfig.get("pingusermapping", worker, fallback=worker)

                # Report shiny encounter
                if self._os == "android":
                    data = {
                        "username": mon_name,
                        "avatar_url": mon_img,
                        "content": f"**{mon_name}** {iv}% L{mon_level} CP{cpval} Gender:{gendericon}\nDespawns: **{despawntime}** ({remainingminsec[0]}m {remainingminsec[1]}s left)\n{worker}/{pogologin}",
                        "embeds": [
                            {
                            "description": f"{lat},{lon}"
                            }
                        ]
                    }
                    result = requests.post(self._webhookurl, json=data)
                    self._mad['logger'].info(result)

                elif self._os == "ios":
                    data = {
                        "username": mon_name,
                        "avatar_url": mon_img,
                        "content": f"**{mon_name}** {iv}% L{mon_level} CP{cpval} Gender:{gendericon}\nDespawns: **{despawntime}** ({remainingminsec[0]}m {remainingminsec[1]}s left)\n{worker}/{pogologin}"
                    }
                    result = requests.post(self._webhookurl, json=data)
                    self._mad['logger'].info(result)

                    time.sleep(1)
                    data = {
                        "username": mon_name,
                        "avatar_url": mon_img,
                        "content": f"```{lat},{lon}```"
                    }
                    result = requests.post(self._webhookurl, json=data)
                    self._mad['logger'].info(result)

                elif self._os == "both":
                    data = {
                        "username": mon_name,
                        "avatar_url": mon_img,
                        "content": f"**{mon_name}** {iv}% L{mon_level} CP{cpval} Gender:{gendericon}\nDespawns: **{despawntime}** ({remainingminsec[0]}m {remainingminsec[1]}s left)\n{worker}/{pogologin}\n\n Android:",
                        "embeds": [
                            {
                            "description": f"{lat},{lon}"
                            }
                        ]
                    }
                    result = requests.post(self._webhookurl, json=data)
                    self._mad['logger'].info(result)

                    time.sleep(1)
                    data = {
                        "username": mon_name,
                        "avatar_url": mon_img,
                        "content": f"iOS: ```\n{lat},{lon}```"
                    }
                    result = requests.post(self._webhookurl, json=data)
                    self._mad['logger'].info(result)

                #update shiny_history in db table to include reported encounter
                reported_data = dict([('encounter_id', encounterid)])
                self._mad['db_wrapper'].autoexec_insert('shiny_history', reported_data)

                time.sleep(2)

            time.sleep(30)


    @auth_required
    def mswreadme_route(self):
        return render_template("mswreadme.html",
                               header="ShinyWatcher Readme", title="ShinyWatcher Readme"
                               )

