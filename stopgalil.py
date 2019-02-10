import sys
import string
import gclib
import time


def main():
  g = gclib.py() #make an instance of the gclib python class
  
  try:
    print('gclib version:', g.GVersion())
    
    ###########################################################################
    # Network Utilities
    ###########################################################################
    '''
    #Get Ethernet controllers requesting IP addresses
    print('Listening for controllers requesting IP addresses...')
    ip_requests = g.GIpRequests()
    for id in ip_requests.keys():
      print(id, 'at mac', ip_requests[id])
     
    #define a mapping of my hardware to ip addresses
    ips = {}
    ips['DMC4000-783'] = '192.168.0.42'
    ips['DMC4103-9998'] = '192.168.0.43'
      
    for id in ips.keys():
      if id in ip_requests: #if our controller needs an IP
        print("\nAssigning", ips[id], "to", ip_requests[id])
        g.GAssign(ips[id], ip_requests[id]) #send the mapping
        g.GOpen(ips[id] + ' --direct') #connect to it
        print(g.GInfo())
        g.GCommand('BN') #burn the IP
        g.GClose() #disconnect
        
    print('\nAvailable addresses:') #print ready connections
    available = g.GAddresses()
    for a in sorted(available.keys()):
      print(a, available[a])
    
    print('\n')
    '''
    ###########################################################################
    #  Connect
    ###########################################################################
    g.GOpen('192.168.42.100 --direct -s ALL')
    #g.GOpen('COM1 --direct')
    print(g.GInfo())

    g.GCommand('AB')
    g.GCommand('MO')
  
  except gclib.GclibError as e:
    print('Unexpected GclibError:', e)
  
  finally:
    g.GClose() #don't forget to close connections!
  
  return
  
 
#runs main() if example.py called from the console
if __name__ == '__main__':
  main()
