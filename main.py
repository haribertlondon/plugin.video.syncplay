# -*- coding: utf-8 -*-
# Module: default
# Author: haribertlondon
# Created on: 28.06.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
import json
import urllib,urllib2
import time
import datetime

_url = sys.argv[0] # Get the plugin url in plugin:// notation.
_handle = int(sys.argv[1]) # Get the plugin handle as an integer number.

def getJSON(url,select):
    html = ""
    try:
        req = urllib2.Request(url) #run html request
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        html=response.read()
        response.close()
        js = json.loads(html) #convert json -> dic 
        return js['result'][select]
    except Exception as e:        
        xbmc.log('Syncplayer: Json Error: '+str(e) +' Url='+str(url) + ' Response' + str(html), level=xbmc.LOGNOTICE)
        return {}

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_percentage(ip):      
      
    for x in range(3): #set 3 retries                    
        url = 'http://'+ip+'/jsonrpc?request={"jsonrpc":"2.0","method":"Player.GetProperties","params":{"playerid":1,"properties":["percentage"]},"id":"1"}'
        percentage = getJSON(url,'percentage')
                
        if percentage > 0:
            break
        else:             
            xbmc.log('Syncplayer: Position could not be found. Response:' + str(percentage) + 'Retry...',level=xbmc.LOGNOTICE)            
            
    return percentage


def get_position(percentage, duration):
    try:
        position = float(percentage) * float(duration) / 100.0            
    except:
        position = 0
        
    return position
        

def get_video(ip):    
    url = 'http://'+ip+'/jsonrpc?request={"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "album", "artist", "season", "episode", "duration", "showtitle", "tvshowid", "thumbnail", "file", "fanart", "streamdetails"], "playerid": 1 }, "id": "VideoGetItem"}'
    dic = getJSON(url,'item')
    
    if not dic or not dic['title']: # if no movie found, exit
        dic = {}
    else:
        dic['ip'] = ip
        dic['percentage'] = get_percentage(ip)
        dic['duration'] = dic['streamdetails']['video'][0]['duration'] 
        dic['position'] =  get_position(dic['percentage'], dic['duration'])        
        dic['label'] = ip + ' - ' +time.strftime('%H:%M:%S', time.gmtime(dic['position'])) + " : " + dic['title']

    xbmc.log('Syncplayer:' + str(dic),level=xbmc.LOGNOTICE)
    return dic 
    
def get_videos():
    ips = [ xbmcplugin.getSetting(_handle, "ip1"), xbmcplugin.getSetting(_handle, "ip2"), xbmcplugin.getSetting(_handle, "ip3"), xbmcplugin.getSetting(_handle, "ip4")]
    videos = []
    
    #last played
    for ip in ips:        
        if len(ip)>4:
            dic = get_video(ip)
            if dic:
                videos.append(dic)
    return videos

def list_videos():
    category = "Currently Playing"
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get the list of videos in the category.
    videos = get_videos()
    # Iterate through videos.

    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['title'])
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': video['label'] , 'mediatype': 'video'})
        
        list_item.setArt({'thumb': video['thumbnail'], 'icon': video['thumbnail'], 'fanart': video['fanart']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', file=video['file'], position=video['position'], ip=video['ip'], duration=video['duration'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
    
def set_position(position):
    for i in range(30*2): # wait 30 seconds        
        if xbmc.Player().isPlaying():
            xbmc.log('Syncplayer: Player says Item now playing. Now waiting until is is really playing',level=xbmc.LOGNOTICE)

            
            stableWait = 0.75

            xbmc.log('Syncplayer: Waiting now for stability ' + str(stableWait),level=xbmc.LOGNOTICE)
            
            for j in range(30*2): #wait 30seconds                    
                if xbmc.Player().getTime()> stableWait:
                    xbmc.log('Syncplayer: Player has reached now '+str(xbmc.Player().getTime())+' sec',level=xbmc.LOGNOTICE)
                    for i in range(30*2): # wait 30 seconds
                        xbmc.log('Syncplayer: Try to seek '+str(float(position))+' sec',level=xbmc.LOGNOTICE)
                        try:                            
                            xbmc.Player().seekTime(float(position))
                        except:            
                            xbmc.log('Syncplayer: Seek did not work',level=xbmc.LOGNOTICE)
                        
                        if abs( float(xbmc.Player().getTime()) - float(position) )<60: #seek has worked +/- 60sec                                     
                            xbmc.log('Syncplayer: Seek applied successfully',level=xbmc.LOGNOTICE)                    
                            return True
                        else:
                            xbmc.log('Syncplayer: Seek has deviation of '+str(abs( float(xbmc.Player().getTime()) - float(position) )) + 'seconds. Wait again 0.5sec and try again',level=xbmc.LOGNOTICE)                    
                            time.sleep(0.5)
                else:
                    xbmc.log('Syncplayer: Player says playing, but item is still at less than '+str(stableWait)+' seconds. Waiting...',level=xbmc.LOGNOTICE)
                    time.sleep(0.5)
        else:
            xbmc.log('Syncplayer: Item is not playing yet. Waiting 0.5 sec and try again...',level=xbmc.LOGNOTICE)
            time.sleep(0.5)
            
    xbmc.log('Syncplayer: Could not set position',level=xbmc.LOGNOTICE)
    return False

def play_video(path, position, ip, duration):
    # Create a playable item with a path to play.    
    
    percentage = get_percentage(ip)    
    newPosition =  get_position(percentage, duration)        
    maxposition =  max(newPosition, position)    
    
    xbmc.log('Syncplayer: maxposition=' + str(maxposition) + 'newpos=' + str(newPosition) + 'pos=' + str(position) + "percent="+ str(percentage) + ' dur=' + str(duration),level=xbmc.LOGNOTICE)
    xbmc.log('Syncplayer: Start play path'+str(path),level=xbmc.LOGNOTICE)
    #xbmc.Player().play(path)

    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    
    set_position(maxposition)


def router(paramstring):
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['file'], params['position'], params['ip'], params['duration'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_videos()

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
