from Blocky.Timer import *

from Blocky.Indicator import indicator
from Blocky.Button import *

from machine import Pin
if  Pin(12,Pin.IN,Pin.PULL_UP).value():
	exec(open('Blocky/ConfigManager.py').read())
	while True :
		pass
#1.First step , check for json file
try :
	from ujson import loads
	f = open('config.json','r')
	config = loads(f.read())
	f.close()
	if not config.get('device_name',False)\
	or not config.get('auth_key',False)\
	or not config.get('known_networks',False):
		raise KeyError('Missing key information')
except Exception:
	print('Missing required info in config. Enter config mode')
	exec(open('Blocky/ConfigManager.py').read()) #this will 
	
print('Finished loading config file' , config)

from Blocky.Network import network
network.connect()
async def service():
  while True :
    await asyncio.sleep_ms(300)
    network.process()
  
loop = asyncio.get_event_loop()
loop.create_task(service())
# network will do the wifi and broker

try :
	exec(open('user_code.py').read())
except Exception as err:
	network.log('Your code crashed because of "' + str(err) + '"')
	


loop.run_forever()


