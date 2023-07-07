#
 # This file is part of the XXX distribution (https://github.com/xxxx or http://xxx.github.io).
 # Copyright (c) 2015 Liviu Ionescu.
 #
 # This program is free software: you can redistribute it and/or modify
 # it under the terms of the GNU General Public License as published by
 # the Free Software Foundation, version 3.
 #
 # This program is distributed in the hope that it will be useful, but
 # WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 # General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License
 # along with this program. If not, see <http://www.gnu.org/licenses/>.
 #
import configparser
import json
import os
import urllib.parse
from pathlib import Path

import requests

print("Welcome to the Spotify Parser - Extended History edition!")
print("It's VERY important to read the README.txt and follow accordingly.")
print("Press enter to continue or ctrl+C to exit.")
input()


config = configparser.ConfigParser()
config.read('settings.ini')
config.sections()

d ={
    "grant_type": "client_credentials",
    "scope": "user-read-playback-position",
    "client_id": config['SETTINGS']['clientID'],
    "client_secret": config['SETTINGS']['clientSecret']
}
if (d["client_id"] == "YOUR_CLIENT_ID") or (d["client_secret"] == "YOUR_CLIENT_SECRET"):
    print("Check if you have put your ID and secret in the program and try again.")
    exit(1)

api_key = requests.post("https://accounts.spotify.com/api/token", data = d).json()["access_token"]

session = requests.Session()
session.headers.update({"Authorization": f"Bearer  {api_key}"})


# loading StreamingHistory
filemap = []
filesNr = int(config['SETTINGS']['filesNumber'])
for x in range(0, filesNr):
    with open(f"{os.getcwd()}/MyData/Streaming_History_Audio_{config['SETTINGS'][f'filename_{str(x)}']}.json") as json_filex:
       filemap += json.load(json_filex)

#loading files for tracks and episodes
track_path = Path(os.getcwd()+'/out/dump/tracks.json')
if track_path.is_file():
    with open(track_path) as dump_file:
        trackdatini = json.load(dump_file)
else:
    trackdatini = {}

episode_path = Path(os.getcwd()+'/out/dump/episodes.json')
if episode_path.is_file():
    with open(episode_path) as dump_file:
        showdatini = json.load(dump_file)
else:
    showdatini = {}

addinf_path = Path(os.getcwd()+'/out/dump/additionalInfo.json')
if addinf_path.is_file():
    with open(addinf_path) as addinf_file:
        additionalInfo = json.load(addinf_file)
else:
    additionalInfo = {"User": "","TotalMS": 0, "DayDistribution": [0]*24,"LastUpdated": "in progress", "IsExtended": "True"}

err_path = Path(os.getcwd()+'/out/dump/error.json')
if err_path.is_file():
    with open(err_path) as err_file:
        err = json.load(err_file)
else:
    err= {"Discarded_IDs":[],"Discarded_records":[], "tr_c":[],"tr_c_ids":[],"ep_c":[],"ep_c_ids":[]}

discarded_ids = err['Discarded_IDs']
discarded_records=err['Discarded_records']
track_cache = err['tr_c']
tr_cache_ids =err['tr_c_ids']
episode_cache = err['ep_c']
ep_cache_ids =err['ep_c_ids']

#get username
resp = (session.get(f"https://api.spotify.com/v1/users/{filemap[0]['username']}"))
if resp.status_code == 200:
    additionalInfo['User'] = resp.json()['display_name']
else:
    print(f"error fetching username for {filemap[0]['username']} :{resp}")
    additionalInfo['User'] = filemap[0]['username']


lastVal = int(config['SETTINGS']['lastValue'])
print("Total records:",len(filemap),"- starting from record number",lastVal+1)
for i, val in enumerate(filemap):
    if i < lastVal:
        continue
    #phase 1: separating podcasts and tracks
    if val['spotify_track_uri'] is None:
        if val['spotify_episode_uri'] is None:
            discarded_ids.append(i)
        else:
            episode_cache.append(val['spotify_episode_uri'].split(":")[2])
            ep_cache_ids.append({"index":i, "ms_played" :val['ms_played'], "endTime": val["ts"],
                                 "show": val['episode_show_name'], "episode": val['episode_name'],
                                 "ep_id": val['spotify_episode_uri'].split(":")[2]})
    else:
        track_cache.append(val['spotify_track_uri'].split(":")[2])
        tr_cache_ids.append({"index":i, "ms_played" :val['ms_played'], "endTime": val["ts"]})
    if (i+1)%50 != 0:
        #print(i)
        continue

     #phase 2: requests and adding records to dicts
    if track_cache:
        tracks_resp = session.get(f"https://api.spotify.com/v1/tracks?ids={','.join(track_cache)}")
        if tracks_resp.status_code != 200:
            print(tracks_resp, tracks_resp.content)
            print("error, saving file and closing...")
            err['tr_c']=track_cache
            err['tr_c_ids']=tr_cache_ids
            err['ep_c']=episode_cache
            err['ep_c_ids']=ep_cache_ids
            err['Discarded_IDs'] = discarded_ids
            err['Discarded_records'] = discarded_records
            with open(track_path, 'w') as tr, open(episode_path, 'w') as ep, open(err_path, 'w') as er, open(
                    'settings.ini', 'w') as settings, open(addinf_path, 'w') as addinf_file:
                json.dump(trackdatini, tr)
                json.dump(showdatini, ep)
                json.dump(err, er)
                json.dump(additionalInfo, addinf_file)
                config['SETTINGS']['lastValue'] = str(i)
                config.write(settings)
            print(f"Save complete, first {str(i)} records saved.")
            exit(1)

        #elaborate tracks
        t_response = tracks_resp.json()
        #if (i+1)%100==0: print(i+1)
        for index,tr in enumerate(t_response['tracks']):
            #print(index)
            try:
                trackID = track_cache[index]
                msDuration = tr["duration_ms"]
                if trackID not in trackdatini:
                    trackdatini[trackID]={"Artist": tr['artists'][0]['name'],"ArtistID": tr['artists'][0]['id'],
                                          "Title": tr["name"], "msDuration": msDuration,"TimesPlayed": 0, "msPlayed": 0,
                                          "timeDistribution": [0]*8,"Popularity": tr['popularity']}
                trackdatini[trackID]["TimesPlayed"] += 1 \
                                                        if tr_cache_ids[index]['ms_played'] > msDuration/3 else 0
                trackdatini[trackID]["msPlayed"] += tr_cache_ids[index]['ms_played']

                time = tr_cache_ids[index]['endTime'].split("T")[1].split(":")[0]
                trackdatini[trackID]["timeDistribution"][int(time)//3] += 1 \
                                                        if tr_cache_ids[index]['ms_played'] > msDuration/3 else 0
                additionalInfo["DayDistribution"][int(time)] += 1 \
                                                        if tr_cache_ids[index]['ms_played'] > msDuration/3 else 0
                additionalInfo["TotalMS"] += tr_cache_ids[index]['ms_played']

            except IndexError as e:
                print("IndexError for",i)
                discarded_records.append({"Position":tr_cache_ids[index]['index'], "Reason": "IndexError"}|filemap[tr_cache_ids[index]['index']])
        track_cache.clear()
        tr_cache_ids.clear()



    #print(','.join(episode_cache))
    #print(ep_cache_ids)
    if episode_cache:
        episode_resp = session.get(f"https://api.spotify.com/v1/episodes?ids={','.join(episode_cache)}&market=US")
        if episode_resp.status_code != 200:
            print(episode_resp,episode_resp.content)
            print("error, saving file and closing...")
            err['tr_c'] = track_cache
            err['tr_c_ids'] = tr_cache_ids
            err['ep_c'] = episode_cache
            err['ep_c_ids'] = ep_cache_ids
            err['Discarded_IDs'] = discarded_ids
            err['Discarded_records'] = discarded_records
            with open(track_path, 'w') as tr, open(episode_path, 'w') as ep, open(err_path, 'w') as er, open(
                    'settings.ini', 'w') as settings, open(addinf_path, 'w') as addinf_file:
                json.dump(trackdatini, tr)
                json.dump(showdatini, ep)
                json.dump(err, er)
                json.dump(additionalInfo, addinf_file)
                config['SETTINGS']['lastValue'] = str(i)
                config.write(settings)
            print(f"Save complete, first {str(i)} records saved.")
            exit(1)

        #elaborate podcast episodes
        e_response = episode_resp.json()
        #print(e_response)
        for index,eps in enumerate(e_response['episodes']):
            #print(index)
            ep=eps
            if not ep:
                #print(index,": None")
                query= f"{ep_cache_ids[index]['show'].replace('#', '')} {ep_cache_ids[index]['episode'].replace('#', '')}"
                #print(query)
                # Imagine if things worked out in this api
                query=(session.get(f"https://api.spotify.com/v1/search?q={query}&type=episode&market=US")).json()
                #print(episode)
                found = False
                for q in query['episodes']['items']:
                    #print(q)
                    if q['name']==ep_cache_ids[index]['episode']:
                        found = True
                        episode = q
                        break
                if not found:
                    print(ep_cache_ids[index]['index'], ": Not Found")
                    #input()
                    discarded_records.append({"Position": ep_cache_ids[index]['index'], "Reason": "Not Found"} | filemap[
                    ep_cache_ids[index]['index']])
                    continue
                else:
                    #print(episode['id'])
                    ep=(session.get(f"https://api.spotify.com/v1/episodes?ids={episode['id']}&market=US")).json()['episodes'][0]

            #print(ep)
            #print(ep['show'])
            showID = ep['show']['id']

            epID = episode_cache[index]
            msDuration = ep["duration_ms"]
            if showID not in showdatini:
                showdatini[showID] = {"Show": ep['show']['name'], "Publisher": ep['show']['publisher'],
                                      "totalEpisodes": ep['show']['total_episodes'], "totalMillis": 0, "totalPlayed":0,
                                       "playedEpisodes": {}, "timeDistribution":[0]*8}

            #considering instances >5min or > 1/2 episode
            if ep_cache_ids[index]['ms_played'] > 5*60*1000 or ep_cache_ids[index]['ms_played'] > msDuration/2:
                if epID not in showdatini[showID]['playedEpisodes']:
                    showdatini[showID]['playedEpisodes'][epID] = {"Name": ep['name']}
                    showdatini[showID]['totalPlayed']+=1

                time = ep_cache_ids[index]['endTime'].split("T")[1].split(":")[0]
                showdatini[showID]['timeDistribution'][int(time)//3]+=1
            showdatini[showID]['totalMillis'] += ep_cache_ids[index]['ms_played']
            additionalInfo["TotalMS"] += ep_cache_ids[index]['ms_played']

        episode_cache.clear()
        ep_cache_ids.clear()


    if (i+1)%1000==0:
        err['Discarded_IDs'] = discarded_ids
        err['Discarded_records'] = discarded_records
        with open(track_path, 'w') as tr, open(episode_path, 'w') as ep, open(err_path, 'w') as er, open(
                'settings.ini', 'w') as settings, open(addinf_path, 'w') as addinf_file:
            json.dump(trackdatini, tr)
            json.dump(showdatini, ep)
            json.dump(err, er)
            json.dump(additionalInfo, addinf_file)
            config['SETTINGS']['lastValue'] = str(i)
            config.write(settings)
        print(f"Save completed: first {i+1} records analyzed")

additionalInfo["LastUpdated"] = filemap[len(filemap)-1]["ts"].replace("T"," ").replace("Z","")

with open(os.getcwd()+"/out/tracks.json", 'w') as tr, open(os.getcwd()+"/out/shows.json", 'w') as ep, open(
        os.getcwd()+"/out/discarded.json", 'w') as dis, open('settings.ini', 'w') as settings, open(
    os.getcwd()+"/out/additionalInfo.json", 'w') as addinf_file:
    json.dump(trackdatini, tr)
    json.dump(showdatini, ep)
    json.dump({"No data":discarded_ids,"Other":discarded_records}, dis)
    json.dump(additionalInfo, addinf_file)
    config['SETTINGS']['lastValue'] = str(len(filemap))
    config.write(settings)

    print(f"Completed! you have {len(trackdatini)} tracks, {len(showdatini)} shows and {len(discarded_records)} records discarded")
