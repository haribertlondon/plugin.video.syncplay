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

_url = sys.argv[0] # Get the plugin url in plugin:// notation.
_handle = int(sys.argv[1]) # Get the plugin handle as an integer number.

def getJSON(url,select):
    try:
        req = urllib2.Request(url) #run html request
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        html=response.read()
        response.close()
        js = json.loads(html) #convert json -> dic 
        return js['result'][select]
    except Exception as e:
        print(e)
        return {}

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_video(ip):
    url = 'http://'+ip+'/jsonrpc?request={"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "album", "artist", "season", "episode", "duration", "showtitle", "tvshowid", "thumbnail", "file", "fanart", "streamdetails"], "playerid": 1 }, "id": "VideoGetItem"}'
    dic = getJSON(url,'item')

    if not dic or not dic['title']:
        return {}
    
    url = 'http://'+ip+'/jsonrpc?request={"jsonrpc":"2.0","method":"Player.GetProperties","params":{"playerid":1,"properties":["percentage"]},"id":"1"}'
    dic['percentage'] = getJSON(url,'percentage')
    
    dic['title'] = ip + ': ' + dic['title']
    try:
        dic['position'] = float(dic['percentage']) * float(dic['streamdetails']['video'][0]['duration']) / 100.0
    except:
        dic['position'] = 0
        xbmc.log('Position could not be found.',level=xbmc.LOGNOTICE)

    xbmc.log(str(dic),level=xbmc.LOGNOTICE)
    return dic 
    
def get_videos():
    ips = [ xbmcplugin.getSetting(_handle, "ip1"), xbmcplugin.getSetting(_handle, "ip2"), xbmcplugin.getSetting(_handle, "ip3"), xbmcplugin.getSetting(_handle, "ip4")]
    videos = []
    
    #last played
    for ip in ips:
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
        list_item.setInfo('video', {'title': video['title'],
                                    'mediatype': 'video'})
        
        list_item.setArt({'thumb': video['thumbnail'], 'icon': video['thumbnail'], 'fanart': video['fanart']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', file=video['file'], position=video['position'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_video(path, position):
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    xbmc.executebuiltin("Seek("+str(position)+")") 

def router(paramstring):
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['file'], params['position'])
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