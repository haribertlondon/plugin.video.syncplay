import time
import xbmc
import xbmcaddon
import sys
import general

if __name__ == '__main__':
    
    
    general.log("SyncPlay start: "+str(time.time()) + str(sys.argv), level=xbmc.LOGINFO)
    
    monitor = xbmc.Monitor()
    
    addon_id = 'plugin.video.syncplay'
    selfAddon = xbmcaddon.Addon(addon_id)    
    autostart=selfAddon.getSetting('autostart').lower() == 'true'    
    ip1=selfAddon.getSetting('ip1')
    ip2=selfAddon.getSetting('ip2')
    ip3=selfAddon.getSetting('ip3')
    ip4=selfAddon.getSetting('ip4')
    ips = [ip1, ip2, ip3, ip4]
    
    general.log("Autostart: " + str(autostart) + str(ips), level=xbmc.LOGINFO)
    
    if autostart:
        #check for autostart
        videos = general.get_videos(ips, True)  
        general.log("Found Videos: " + str(videos), level=xbmc.LOGINFO)        
        
        
        if videos is not None and len(videos)>0:
            video = videos[0]
            general.play_video(video['file'], video['ip'], video['duration'])  
        
        #while not monitor.abortRequested():
        #    
            # Sleep/wait for abort for 10 seconds
        #    if monitor.waitForAbort(10):
        #        # Abort was requested while waiting. We should exit
        #        break
            
            
        #    general.log("hello addon! %s" % time.time(), level=xbmc.LOGINFO)
    else:
        general.log("No Autostart set. Exiting", level=xbmc.LOGINFO)