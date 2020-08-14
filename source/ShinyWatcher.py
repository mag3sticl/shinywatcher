import mapadroid.utils.pluginBase
from functools import update_wrapper, wraps
from flask import render_template, Blueprint, jsonify
from mapadroid.madmin.functions import auth_required
from threading import Thread
import os
import sys
import time
import datetime
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

        # dont start plugin in config mode
        if self._mad['args'].config_mode == True:
            self._mad['logger'].info("Plugin - ShinyWatcher is not aktive while configmode")
            return False

        # read config parameter
        self._shinyhistory: list = []
        self._workers: dict = {}

        self._timzone_offset = datetime.datetime.now() - datetime.datetime.utcnow()
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
        str_id = str(mon_id)
        if str_id in mons_file:
            if self._language != "en":
                return self.i8ln_plugin(mons_file[str_id]["name"])
            else:
                return mons_file[str_id]["name"]
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

    def MadShinyWatcher(self):
        devicemapping = self._mad['mapping_manager'].get_all_devicemappings()
        self._mad['logger'].debug(devicemapping)
        for worker in devicemapping:
            devicesettings = devicemapping[worker]
            self._mad['logger'].debug(devicesettings)
            if devicesettings['settings'].get('logintype', '') == 'google':
                pogoaccount = devicesettings['settings'].get("ggl_login_mail", "unknown")
            elif devicesettings['settings'].get('logintype', '') == 'ptc':
                pogoaccount = ((devicesettings['settings'].get("ptc_login", "unknown")).split(','))[0]
            self._workers[worker] = pogoaccount

        worker_filter = ""
        if not self._only_show_workers == "":
            self._only_show_workers = "'" + (self._only_show_workers).replace(",","','") + "'"
            worker_filter = f"AND t.worker in ({self._only_show_workers})"

        while True:

            query = (
                "SELECT pokemon.encounter_id, pokemon_id, disappear_time, individual_attack, individual_defense, individual_stamina, cp_multiplier, longitude, latitude, t.worker FROM pokemon LEFT JOIN trs_stats_detect_mon_raw t ON pokemon.encounter_id = t.encounter_id WHERE disappear_time > utc_timestamp() AND t.is_shiny = 1 {} ORDER BY pokemon_id DESC, disappear_time DESC"
            ).format(worker_filter)
            self._mad['logger'].debug("MSW DB query: " + query)
            results = self._mad['db_wrapper'].autofetch_all(query)
            self._mad['logger'].debug("MSW DB result: " + str(results))
            for result in results:
                if str(result['encounter_id']) in self._shinyhistory:
                    continue
                if str(result['pokemon_id']) in self._exlude_mons:
                    continue
                
                mon_name = self.get_mon_name_plugin(result['pokemon_id'])
                mon_img = f"https://raw.githubusercontent.com/Plaryu/PJSsprites/master/pokemon_icon_{str(result['pokemon_id']).zfill(3)}_00.png"
            
                self._mad['logger'].info(f"found shiny {mon_name}")

                encid = str(result['encounter_id'])    
                iv = int(round((((int(result['individual_attack']) + int(result['individual_defense']) + int(result['individual_stamina'])) / 45) * 100), 0))
                etime = result['disappear_time'] + self._timzone_offset
                end = etime.strftime("%H:%M:%S")
                td = etime - datetime.datetime.now()
                timeleft = divmod(td.seconds, 60)
                lat = result['latitude']
                lon = result['longitude']
                worker = result['worker']
				
                email = ""
                email = self._workers[worker]
                if self._mask_mail == 'yes':
                    email = self.do_mask_email(email)
                elif self._mask_mail == 'total':
                    email = '**@*.*'

                if self._pinguser == 'yes':
                    worker = self._pluginconfig.get("pingusermapping", worker, fallback=worker)				
		
                if result['cp_multiplier'] < 0.734:
                    mon_level = round(58.35178527 * result['cp_multiplier'] * result['cp_multiplier'] - 2.838007664 * result['cp_multiplier'] + 0.8539209906)
                else:
                    mon_level = round(171.0112688 * result['cp_multiplier'] - 95.20425243)
        
                if self._os == "android":
                    data = {
                        "username": mon_name,
                        "avatar_url": mon_img,
                        "content": f"**{mon_name}** ({iv}%, lv{mon_level}) until **{end}** ({timeleft[0]}m {timeleft[1]}s)\n{worker} ({email})",
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
                        "content": f"**{mon_name}** ({iv}%, lv{mon_level}) until **{end}** ({timeleft[0]}m {timeleft[1]}s)\n{worker} ({email})"
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
                        "content": f"**{mon_name}** ({iv}%, lv{mon_level}) until **{end}** ({timeleft[0]}m {timeleft[1]}s)\n{worker} ({email})\n\n Android:",
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

                self._shinyhistory.append(encid)

                time.sleep(2)

            if datetime.datetime.now().hour == 3 and datetime.datetime.now().minute < 10:
                self._shinyhistory.clear()
            time.sleep(60)


    @auth_required
    def mswreadme_route(self):
        return render_template("mswreadme.html",
                               header="ShinyWatcher Readme", title="ShinyWatcher Readme"
                               )
							   

