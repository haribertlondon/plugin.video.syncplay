import json
import time
try:
    import xbmc
    import urllib.request, urllib.error, urllib.parse
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl
    import urllib2 as urlrequest #@UnresolvedImport @Reimport
except:
    import urllib.request as urlrequest #@UnusedImport


def log(s, level=None):
    try:
        if level is None:
            level = xbmc.LOGNOTICE
        xbmc.log('[Syncplayer]:' + str(s),level)
    except:
        print((str(s)))
    

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
    post = '{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "file", "streamdetails", "thumbnail", "fanart"], "playerid": 1 }, "id": "VideoGetItem"}'
    dic = getJSON(url,post,'item')
    
    if not dic or not dic['label']: # if no movie found, exit
        dic = {}
    else:
        dic['ip'] = ip
        dic['duration'] = dic['streamdetails']['video'][0]['duration']
        dic['title'] = dic['label'] 
        dic['label'] = ip + ": " +dic['title']
    return dic 


def getJSON(url,post, select):
    html = ""
    try:
        
        try:   
            post = str.encode(post) # set to byte array
        except:
            post = post.encode("utf-8")
        
        req = urlrequest.Request(url) #run html request
        req.add_header('Content-Type','application/json')
        response = urlrequest.urlopen(req, data = post, timeout=4)
        html=response.read()
        response.close()
        js = json.loads(html) #convert json -> dic 
        log(js)
        if select is not None:
            return js['result'][select]
        else:
            return js['result']
    except Exception as e:        
        log('Syncplayer: Json Error: '+str(e) +' Url='+str(url) +' Post='+str(post) + ' Response' + str(html))
        return {}




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


def start_videofile_from_resumePoint(path):
    url = 'http://localhost:8080/jsonrpc'
    post = '{ "jsonrpc": "2.0", "method": "Player.Open", "params": {"item":{"file":'+json.dumps(path)+'},"options": {"resume": true}},"id":1}'
    return getJSON(url, post, None)     

def setResumePoint(path, position, duration):
    url = 'http://localhost:8080/jsonrpc'
    post = '{ "jsonrpc": "2.0", "method": "Files.SetFileDetails", "params": { "file":'+json.dumps(path)+', "media": "video", "resume": {"position":'+str(position)+',"total":'+str(duration)+'} },"id":1}'
    
    return getJSON(url, post, None)

def play_video(path, ip, duration):
    # Create a playable item with a path to play.    
    log("Playing video: "+str(path))
    position =  get_position(ip, duration)
        
    setResumePoint(path, position, duration)
    start_videofile_from_resumePoint(path) 
    
    log('Syncplayer: Start play path'+str(path))    
    
    
if __name__ == "__main__":
    path = 'sftp://192.168.0.100:22/share/Multimedia/Filme/Im_Norden_strahlt_der_Weihnachtsstern_19.12.16_20-15_disney_105_TVOON_DE.mpg.HQ.cut.avi'
    play_video(path, "192.168.0.69",60*60)
    print("Finished script")