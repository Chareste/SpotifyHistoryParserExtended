
# Spotify History EXtended Parser
A parser for the Extended Streaming History (all time) sent to you by Spotify [after requesting it there](https://www.spotify.com/us/account/privacy/).  
They are elaborated through the Spotify API so it requires internet connection to function.

## Getting started

There are a few things you'll need to do before starting:
- Download *spotifyParserEX.py* and *settings.ini* and place them into the same folder. This will be your root.
- Create a new folder in your root called *out*, open it and create a new folder called *dump* inside.
- Put the folder of the data sent to you from Spotify (called MyData) in the root folder.
- Get your client ID and secret
- Update the settings.ini file
- Have **Python** installed

### How do I get my client ID and secret?

You have to access [Spotify Developers](https://developer.spotify.com/), then login.

You then have to access **dashboard > create app**, then fill the fields (not important with what).  
Once you have your app, access **dashboard > [YOUR-APP] > settings > basic informations**. Here you'll find your
client ID and your secret. These need to be added into the settings. 

### Update settings
You'll find a settings.ini file that contains the parameters that need to be edited for the correct functioning 
of the program. 
- ClientID: the client ID you got from the developers app
- ClientSecret: the client secret you got from the developers app
- filesNumber: how many Streaming_History_Audio_xxxx.json are in the MyData folder.
  >Note: put the total number of Streaming_History_Audio_ files and not the greatest index, they start from 0 and not 1!  
  Also do not add any Streaming_History_Video_ files. There is currently no support for them.
- filename_0 to filename_(filesNumber-1): the names of the files after the ***Streaming_History_Audio_*** part.  
  > Add or remove as many as you need, it's important they go from 0 to total-1. If you have only one, keep the one with the 0.
- lastValue: the last index elaborated by the parser.  
  - don't touch it (you will miss records/have duplicates)
  - unless you want to [restart](#restarting-) 

### Installing Python
[There are plenty of guides in the sea but I'll link you one for ease](
https://gist.github.com/MichaelCurrin/57caae30bd7b0991098e9804a9494c23)

## Running the program

Open the terminal and move into the folder where you placed SpotifyParser.py. Then run it with Python with this command:  
```
python3 spotifyParserEX.py
```
Or, if you're on windows:
```
python spotifyParserEX.py
```
And it's done! Let it run, it will take a while depending on your internet connection but it should be faster than the 
non-extended version since I could do batch searches.

### Restarting 
If you want to restart from scratch, make sure you delete **EVERYTHING** in your dump folder. 
Then set the *lastvalue* option in the settings file to 0 and you're good to go.


## Output

The program will return you two main JSON files, *tracks.json*, *shows.json*, *additionalInfo.json* and *discarded.json*.  

### tracks.json

This file contains the effective elaborated output with all the tracks elaborated from your streaming
history.

#### Structure
```
{
  "TRACK_ID": {
    "Artist": ARTIST_NAME,
    "Title": TRACK_NAME,
    "msDuration": LENGTH_IN_MILLISECONDS,
    "TimesPlayed": TIMES_PLAYED>=1/3_TRACK_LEN,
    "msPlayed": TOTAL_MILLIS_PLAYED,
    "timeDistribution": [ PLAYS_PER_3HR_BLOCKS ],
    "Popularity": TRACK_POPULARITY
  },
  [...]
  }
```
### shows.json

This file contains the elaborated output with all the shows elaborated from your streaming
history.

#### Structure
```
{
  "SHOW_ID": {
    "Show": SHOW_NAME,
    "Publisher": PUBLISHER_NAME,
    "totalEpisodes": TOTAL_EPISODES,
    "totalMillis": TOTAL_MILLIS_PLAYED,
    "totalPlayed": EPISODES_PLAYED>=5MIN_OR_>=1/2_LENGTH,
    "playedEpisodes": {
    "EPISODE_ID:{ "Name": EPISODE_NAME }
    }
    "timeDistribution": [ PLAYS_PER_3HR_BLOCKS ],
  },
  [...]
  }
```
### additionalInfo.json

This file contains other data collected from the user that will be used by 
the stats analyzer.

#### Structure
```
{
  "User": SPOTIFY_USERNAME,
  "TotalMS": TOTAL_MILLIS_PLAYED,
  "DayDistribution": [ PLAYS_PER_HOUR ],
  "LastUpdated": TIMESTAMP_LATEST_INSTANCE
  "IsExtended": True
}
```


### discarded.json 

These are the listening instances of the tracks and episodes that couldn't be found. 
They most likely are deleted episodes/tracks.  
There is also an array containing indexes with no data. I am investigating why they exist in the first place.


It contains the [JSON directly from the StreamingHistory file]
(https://support.spotify.com/us/article/understanding-my-data/#:~:text=What%27s%20included-,Extended%20Streaming%20History,-(audio%2C%20video%2C%20and), 
indexed by the position in the (concatenation of) file(s). 
#### Structure 
```
{
  "No Data": [INDEXES_W/O_DATA]
  "Other":[
      {
        "position": INDEX_IN_FILEMAP
        "reason": DISCARD_REASON,
        ...all the other rows in the filemap index
      }
      [...]
    ]
  }
```
### Dump folder
You'll find other kinds of files there. These are all temporary files used in intermediate saves.

## Troubleshooting

It's unlikely you'll run into any error except server-side ones [response 5xx]. 
The program will save its state so you just need to rerun it.
- [check response codes here](https://developer.spotify.com/documentation/web-api/concepts/api-calls#response-status-codes)

## Known issues

### 'No data' records

I am currently unaware of the reason why some records have no informations regarding their track/episode whatsoever, 
it seems *it's an issue on Spotify's side* so there's no solution for it.

