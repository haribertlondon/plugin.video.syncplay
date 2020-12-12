import xbmc
import xbmcplugin
import json
import urllib,urllib2
import time
import datetime
from urllib import urlencode
from urlparse import parse_qsl

def log(s, level=xbmc.LOGNOTICE):
    xbmc.log('[Syncplayer]:' + str(s),level)
    

def get_videos(ips, ExitOnFirstSuccess = False):    
    videos = []
    
    #last played
    for ip in ips:        
        if len(ip)>4:
            dic = get_video(ip)
            if dic:
                videos.append(dic)
                if ExitOnFirstSuccess:
                    break
    return videos
 

def get_video(ip):    
    url = 'http://'+ip+'/jsonrpc'
    post = '{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "file", "streamdetails"], "playerid": 1 }, "id": "VideoGetItem"}'
    dic = getJSON(url,post,'item')
    
    if not dic or not dic['title']: # if no movie found, exit
        dic = {}
    else:
        dic['ip'] = ip
        dic['duration'] = dic['streamdetails']['video'][0]['duration'] 
        dic['label'] = ip + ": " +dic['title']
    return dic 


def getJSON(url,post, select):
    html = ""
    try:
        req = urllib2.Request(url) #run html request
        req.add_header('Content-Type','application/json')
        response = urllib2.urlopen(req, data = post, timeout=4)
        html=response.read()
        response.close()
        js = json.loads(html) #convert json -> dic 
        log(js)
        if select is not None:
            return js['result'][select]
        else:
            return js['result']
    except Exception as e:        
        log('Syncplayer: Json Error: '+str(e) +' Url='+str(url) +' Post='+str(post) + ' Response' + str(html), level=xbmc.LOGNOTICE)
        return {}

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_percentage(ip):      
      
    for x in range(3): #set 3 retries                    
        url = 'http://'+ip+'/jsonrpc'
        post = '{"jsonrpc":"2.0","method":"Player.GetProperties","params":{"playerid":1,"properties":["percentage"]},"id":"1"}'
        percentage = getJSON(url, post,'percentage')
                
        if percentage > 0:
            break
        else:             
            log('Syncplayer: Position could not be found. Response:' + str(percentage) + 'Retry...')            
            
    return percentage


def get_position(ip, duration):
    percentage = get_percentage(ip)
    try:
        position = float(percentage) * float(duration) / 100.0            
    except:
        position = 0
        
    log("Playing video: "+str(percentage)+'% Time: '+str(position)+' Duration: '+str(duration))
        
    return position


def set_position(ip, duration):
    for i in range(30*2): # wait 30 seconds        
        if xbmc.Player().isPlaying():
            log('Syncplayer: Player says Item now playing. Now waiting until is is really playing',level=xbmc.LOGNOTICE)

            
            stableWait = 0.75

            log('Syncplayer: Waiting now for stability ' + str(stableWait),level=xbmc.LOGNOTICE)
            
            for j in range(30*2): #wait 30seconds                    
                if xbmc.Player().getTime()> stableWait:
                    log('Syncplayer: Player has reached now '+str(xbmc.Player().getTime())+' sec',level=xbmc.LOGNOTICE)
                    
                    position =  get_position(ip, duration)
                    
                    for i in range(30*2): # wait 30 seconds
                        log('Syncplayer: Try to seek '+str(float(position))+' sec',level=xbmc.LOGNOTICE)
                        try:                            
                            xbmc.Player().seekTime(float(position))
                        except:            
                            log('Syncplayer: Seek did not work',level=xbmc.LOGNOTICE)
                        
                        if abs( float(xbmc.Player().getTime()) - float(position) )<60: #seek has worked +/- 60sec                                     
                            log('Syncplayer: Seek applied successfully',level=xbmc.LOGNOTICE)                    
                            return True
                        else:
                            log('Syncplayer: Seek has deviation of '+str(abs( float(xbmc.Player().getTime()) - float(position) )) + 'seconds. Wait again 0.5sec and try again',level=xbmc.LOGNOTICE)                    
                            time.sleep(0.5)
                else:
                    log('Syncplayer: Player says playing, but item is still at less than '+str(stableWait)+' seconds. Waiting...',level=xbmc.LOGNOTICE)
                    time.sleep(0.5)
        else:
            log('Syncplayer: Item is not playing yet. Waiting 0.5 sec and try again...',level=xbmc.LOGNOTICE)
            time.sleep(0.5)
            
    log('Syncplayer: Could not set position',level=xbmc.LOGNOTICE)
    return False

def start_videofile_from_beginning(path):
    url = 'http://localhost:8080/jsonrpc'
    post = '{ "jsonrpc": "2.0", "method": "Player.Open", "params": {"item":{"file":'+json.dumps(path)+'}},"id":1}'
    
    return getJSON(url, post, 'item')     

def play_video(path, ip, duration):
    # Create a playable item with a path to play.    
    log("Playing video: "+str(path))
        
    start_videofile_from_beginning(path) 
    
    log('Syncplayer: Start play path'+str(path), level=xbmc.LOGNOTICE)
    
    set_position(ip, duration)