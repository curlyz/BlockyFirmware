from Blocky.Indicator import indicator
import network,socket,time,random,binascii,machine,re,ustruct,gc,ujson
from json import dumps , loads
from os import stat
from _thread import start_new_thread
import socket
from Blocky.MicroWebSrv import MicroWebSrv
from time import sleep_ms
"""
class config is called when esp boot and cant connect or the connection is dropped randomly 
therefore , when the network is restore  , this will reset ,
"""

indicator.animate(type='heartbeat',color=(50,0,0),speed=10)
sleep_ms(2000)

class ConfigManager:
	def __init__ (self,config = {}):
		self.config = config
		self.wlan_ap = network.WLAN(network.AP_IF)
		self.wlan_sta = network.WLAN(network.STA_IF)
		
		id = binascii.hexlify(machine.unique_id()).decode('ascii')
		code = [id[i:i+2] for i in range(0, len(id), 2)]

		max_index = 0 ; max_value = 0
		for x in range(6):
		  if int(code[x],16) > max_value:
			max_value = int(code[x],16)
			max_index = x
		color = []
		if max_index == 0 : color = ['red',(255,59,48)]
		if max_index == 1 : color = ['green',(76,217,100)]
		if max_index == 2 : color = ['blue',(0,122,255)]
		if max_index == 3 : color = ['pink',(255,45,85)]
		if max_index == 4 : color = ['purple',(88,86,214)]
		if max_index == 5 : color = ['yello',(255,204,0)]
			
		
		try :
			f = open('config.json')
			self.ap_name = loads(f.read()).get('device_name')
			if self.ap_name == None :
				raise Exception
		except Exception:
			self.ap_name = 'Blocky ' + color[0].upper() +' '+ binascii.hexlify(machine.unique_id()).decode('ascii')[0:4];print(self.ap_name)
		indicator.animate()
		indicator.rgb[0] = color[1]
		indicator.rgb.write()
		self.ap_password = ''
		self.wifi_status = 0
	def connect(self, ssid, password):
		self.wlan_sta.active(True)
		self.wlan_sta.connect(ssid, password)
		a=0
		print('Connecting to wifi')
		#indicator.animate('pulse',(100,50,0),10)
		while not self.wlan_sta.isconnected() | (a > 99) :
			time.sleep(0.1)
			a+=1
			print('.', end='')
		
		if self.wlan_sta.isconnected():
			#indicator.animate('pulse',(0,100,50),10)
			print('\nConnected. Network config:', self.wlan_sta.ifconfig())
			self.wifi_status = 1
			return True
		else : 
			#indicator.animate('hearbeat',(0,100,50),10)
			print('\nProblem. Failed to connect to :' + ssid)
			self.wifi_status = 2
			self.wlan_sta.active(False)
			return False
	def _httpHandlerIndexGet(self, httpClient, httpResponse):
		print('Get index request')	
		htmlFile = open('Blocky/index.html', 'r')
		content = ''
		for line in htmlFile:
			print(line)
			content = content + line
		httpResponse.WriteResponseOk( headers = None,
			contentType	 = "text/html",	contentCharset = "UTF-8",	content = content)
	
	def _httpHandlerCheckStatus(self, httpClient, httpResponse):
		print('Get check status request')
		if self.wifi_status == 1:
			content = 'OK'
		elif self.wifi_status == 2:
			content = 'Failed'
		else:	
			content = ''
		
		httpResponse.WriteResponseOk(headers = None,
			contentType	 = "text/html",
			contentCharset = "UTF-8",
			content = content)
			
		if self.wifi_status == 1:
			print('Wait for rebooting')
			time.sleep(5)
			print('Rebooting')
			machine.reset()

	def _httpHandlerSaveConfig(self, httpClient, httpResponse):
		print('Get save config request')
		request_json = ujson.loads(httpClient.ReadRequestContent().decode('ascii'))
		self.wifi_status = 0
		print(request_json)
		httpResponse.WriteResponseOk(headers = None,
			contentType	 = "text/html",
			contentCharset = "UTF-8",
			content = 'OK')
		
		if self.connect(request_json['ssid'], request_json['password']):
			# save config
			if not self.config.get('known_networks'):
				self.config['known_networks'] = [{'ssid': request_json['ssid'], 'password': request_json['password']}]
			else:
				exist_ssid = None
				for n in self.config['known_networks']:
					if n['ssid'] == request_json['ssid']:
						exist_ssid = n
						break
				if exist_ssid:
					exist_ssid['password'] = request_json['password'] # update WIFI password
				else:
					# add new WIFI network
					self.config['known_networks'].append({'ssid': request_json['ssid'], 'password': request_json['password']})
			
			self.config['device_name'] = request_json['deviceName']
			self.config['auth_key'] = request_json['authKey']
			f = open('config.json', 'w')
			f.write(ujson.dumps(self.config))
			f.close()
		
	def is_ascii(self, s):
		return all(ord(c) < 128 for c in s)
	
	def _httpHandlerScanNetworks(self, httpClient, httpResponse) :
		print('Receive request to scan networks')
		self.wlan_sta.active(True)
		networks = []
		for nw in self.wlan_sta.scan():
			if (self.is_ascii(nw[0].decode('ascii'))):
				networks.append({'ssid': nw[0].decode('ascii'), 'rssi': nw[3]})
			else:
				print('Unicode error found in WiFi SSID')
				continue
		print(networks)
		content = ujson.dumps(networks)
	 
		httpResponse.WriteResponseOk(headers = None,contentType= "application/json",contentCharset = "UTF-8",content = content)
									 
	def start(self):		
		self.wlan_sta.active(True)
		self.wlan_ap.active(True)

		self.wlan_ap.config(essid=self.ap_name, password=self.ap_password)

		routeHandlers = [
			("/", "GET", self._httpHandlerIndexGet),
			("/aplist", "GET", self._httpHandlerScanNetworks),
			("/status", "GET", self._httpHandlerCheckStatus),
			("/save", "POST",	self._httpHandlerSaveConfig)
		]

		srv = MicroWebSrv(routeHandlers=routeHandlers)
		srv.Start(threaded=True)

		print('Now enter config mode')
		print('Connect to Wifi ssid :' + self.ap_name + ' , default pass: ' + self.ap_password)
		print('And connect to Blocky via at 192.168.4.1')
		
		gc.collect()
		print(gc.mem_free())

		return True
		
    
config_manager = ConfigManager()
config_manager.start()

while True :
  pass


