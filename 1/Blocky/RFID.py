import Blocky.uasyncio as asyncio
from Blocky.Pin import *
from Blocky.Network import network
from Blocky.Timer import clock
from time import *
PN532_MIFARE_ISO14443A				= 0x00
#PN532_ACK_STRING					= "0000ff00ff00"
PN532_ACK_STRING					= bytearray([0x00,0x00,0xFF,0x00,0xFF,0x00])
#PN532_ACK_FRAME						= "\x00\x00\xFF\x00\xFF\x00"
PN532_ACK_FRAME						= bytearray([0x00,0x00,0xFF,0x00,0xFF,0x00])
def reduce(function, iterable, initializer=None):
    it = iter(iterable)
    if initializer is None:
        try:
            initializer = next(it)
        except StopIteration:
            raise TypeError('reduce() of empty sequence with no initial value')
    accum_value = initializer
    for x in it:
        accum_value = function(accum_value, x)
    return accum_value

class RFID:
	def __init__ (self,port):
		self.last = None 
		self.status = False 
		self.message = None
		self.pin = getPin(port)
		self.cb = None
		from machine import UART 
		self.ser = UART ( 1 , tx = self.pin[0] , rx = self.pin[1] , baudrate = 115200 )
		self.status = True
		self.ser.write( '\x55\x55\x00\x00\x00') # wakeup babe
		self.SAM_configuration()
		
		loop = asyncio.get_event_loop()
		loop.call_soon(self._handler())
	def _uint8_add(self,a,b): return ((a & 0xFF) + (b & 0xFF)) & 0xFF
	def _write_frame(self,data):
		length = len(data)
		frame = bytearray(length+7)
		frame[0] = 0x00
		frame[1] = 0x00
		frame[2] = 0xFF
		frame[3] = length & 0xFF
		frame[4] = self._uint8_add(~length, 1)
		frame[5:-2] = data
		checksum = reduce(self._uint8_add,data,0xFF)
		frame[-2] = ~checksum & 0xFF
		frame[-1] = 0x00
		ack = False
		while not ack:
			self.ser.write(frame)
			ack = self._ack_wait(1000)
			sleep_ms(200)
		return ack 
	def _ack_wait(self , timeout):
		ack = False 
		rx_info = bytearray()
		start_time = ticks_ms()
		current_time = start_time
		while current_time-start_time<timeout and not ack :
			sleep_ms(120)
			while self.ser.any():
				rx_info.extend(self.ser.read())
			current_time = ticks_ms()
			if len(rx_info):
				ack = True 
		if ack:
			self.message = rx_info
		else :
			self.message = ''
		return ack
	def _read_data(self , count):
		timeout = 1000
		rx_info = ''
		if self.message == '':
			self._ack_wait(1000)
		else :
			rx_info = self.message
		return rx_info
		
	def _read_frame(self,length):
		response = self._read_data(length+8)
		frame_len = 0
		offset = 0
		if not len(response):return None
		if response[0]!=0 : return None
		if PN532_ACK_FRAME == response : return None
		for i in range(0 , len(response)):
			if response[i] != 0 and response[i] != 255:
				frame_len = response[i]
				offset = i
				break
		if frame_len == 0:return None
		if frame_len+response[offset+1]&0xFF!=0:return None
		checksum = reduce(self._uint8_add, response[offset+2:offset+2+frame_len+1], 0)
		if checksum != 0: return None
		return response[offset+2:offset+2+frame_len] 
	def call_function(self,command,response_length=0,params=[],timeout_sec = 1):
		data = bytearray(2 + len(params))
		data[0] = 0xD4 #PN532_HOSTTOPN532
		data[1] = command & 0xFF
		for i in range(len(params)):data[2+i] = params[i]
		if not self._write_frame(data): return None
		response = self._read_frame(response_length+2)
		if not response == None : 
			if not (response[0] == 0xD5 and response[1] == (command+1)): return None#PN532_PN532TOHOST
			return response[2:]
		else :
			return response
	
	def fw(self):
		response = self.call_function(0x02,4) #PN532_COMMAND_GETFIRMWAREVERSION
		if response == None : return None
		else :
			return (response[0], response[1], response[2], response[3])
			
	def SAM_configuration(self):
		self.call_function(0x14, params=[0x01, 0x14, 0x01])#PN532_COMMAND_SAMCONFIGURATION
	def read_passive_target(self, card_baud=PN532_MIFARE_ISO14443A, timeout_sec=1):
		response = self.call_function(0x4A,params=[0x01, card_baud], response_length=17)#PN532_COMMAND_INLISTPASSIVETARGET
		if response == None : return None
		else :
			if response[0] != 0x01 or response[5] > 7:
				return None
			list = []
			for x in range(6,6+response[5]):
				list.append(response[x])
			return list
		
	def event(self,function):
		self.cb = function
		
	async def _handler(self):
		while True :
			await asyncio.sleep_ms(500)
			now = self.read_passive_target()
			if (self.last != now and now != None):
				try :
					print('rfid',now)
					if callable(self.cb):
						self.cb(now)
				except Exception as err:
					print('rfid-event' , err , now )
					
			self.last = now
		
	



