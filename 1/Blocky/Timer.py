# Data Structure :
"""
[0] :	Next Execute Time 
[1] :	Current mode of running : once , repeat or schedule
[2] :	Function to be call 
[3] :	Argument to be pass through
[4] :	Name of Task to delete or update later 
[5] :	Period Gap between each execute
[6] :	Execute Time (time it take to execute this task )
[7]	:	Original Period gap (this is set by AddTask)
[8] :	Priority bit 
"""

"""
Main Timer Variable 
[0] :	[Low] Time before feeding
[1]	:	[Important] Timer after feeding ( real time )
[2]	:	
	[0]	:	NTP at the last sync
	[1]	:	Runtime at that sync
[3] :	Next Interrupt time based on [1]
[4] : 	True mean the next trigger will run the list[0]
		False if next trigger is just for avoiding overflow
[5]	: 	Percentage calculated by usage()
[6] :	Start execute time of any task 
[7] : 	Total Execution
"""

"""
Timer usage is calulated based on a loop through the list 
p = percentage = loop(list) with formula : p += (task[6]/task[5])
If this percentage is > 90% then each task is the list will be 
for task in list :
	if not priority :
		task[5] += 1
	
If this percentage is < 90 :
	for each task in list 
		if not priority :
			is task[5] > task[7]:
				task[5] -= 1

Whenever a task is ran , the runtime is calulated
	we have runtime , period and percentage
	if percentage > 90:
		task[5] += 2
"""
# TimerInfo[2] = ( _NTP at last sync , _Runtime at last sync )
from machine import Timer 
from time import ticks_ms
from _thread import *
if '_Tasker' not in globals():_Tasker = Timer(1)
if 'TaskList' not in globals():TaskList = []
if 'ScheduleList' not in globals():ScheduleList = []
if 'worktime' not in globals():worktime = 0
if 'TimerInfo' not in globals(): TimerInfo = [ticks_ms() ,0 ,None,0,False,0,0]
import Blocky.uasyncio as asyncio
def runtime():
	global TimerInfo
	now = ticks_ms()
	if now < TimerInfo[0]:offset =  (1073741823 - TimerInfo[1] + now)
	else :	offset =  (now - TimerInfo[0])
	TimerInfo[1] += offset;TimerInfo[0] = now
	return TimerInfo[1]
	
def clock():
	global TimerInfo
	if TimerInfo[2] == None :return None 
	else : return TimerInfo[2][1] + (runtime()-TimerInfo[2][0])//1000


	
def _TimerHanler(source):
	global TaskList , TimerInfo
	TimerInfo[6] = runtime()
	if TimerInfo[4]:
		try :
			global TimerInfo
			
			if TaskList[0][3]:	
				TaskList[0][2](TaskList[0][3])
			else :
				TaskList[0][2]()
			TaskList[0][6] = runtime() - TimerInfo[6] # execute time saved
			if TaskList[0][6]>TaskList[0][5] and TaskList[0][8] == False:
				TaskList[0][5] = TaskList[0][6]*2
			if TaskList[0][1] == 'repeat':
				TaskList[0][0] += TaskList[0][5]
			elif TaskList[0][1] == 'once':
				TaskList.pop(0)
		except Exception as err :
			print('[',runtime(),'] Task {0} removed because {1}'.format(TaskList[0][4],err))
			TaskList.pop(0)
		finally :
			
			TimerInfo[4] = False
	try :
		TaskList.sort(key=lambda x: x[0])
	except Exception as err:
		print(err,TaskList)
	# feed 
	global _Tasker
	if len(TaskList) == 0:
		TimerInfo[3] = TimerInfo[1] + 300000
		TimerInfo[4] = False 
	else :
		if TaskList[0][0] - TimerInfo[1] < 0:
			TimerInfo[3] = TimerInfo[1] + 1
			TimerInfo[4] = True
			_TaskControl()
		else :
			if TaskList[0][0] - TimerInfo[1] > 300000:
				TimerInfo[3] = TimerInfo[1] + 300000
				TimerInfo[4] = False
			else :
				TimerInfo[3] = TimerInfo[1] + (TaskList[0][0]-TimerInfo[1])
				TimerInfo[4] = True
	_Tasker.init(period = (TimerInfo[3]-TimerInfo[1]) , mode = Timer.ONE_SHOT , callback = _TimerHanler)
"""
	Task controll will take care of period value of each task 
	
"""
def DeleteTask(name):
	global TaskList,TimerInfo
	for x in range(len(TaskList)):
		if TaskList[x][4] == name:
			TaskList.pop(x)
			TimerInfo[4] = False
			_TimerHanler(None)
			return True 
	return False
	
def AddTask(function,mode='repeat',name=None,time=1000,arg=None,priority = False):
	global TaskList,TimerInfo
	TimerInfo[6] = runtime()
	if not callable(function):
		print('cant call')
		return 
	# is it new ?
	#not new
	#new
	if mode == 'schedule':
		if 'date' in kwargs and 'time' in kwargs:
			global ScheduleList
			ScheduleList.append({'function':function,'name':name,'date':kwargs['date'],'time':kwargs['time']})
			sync_clock()
	else :
		task = [TimerInfo[6] if mode == 'repeat' else TimerInfo[6] + time,mode,function,arg,name,time,0,time,priority]
		existed = False
		for x in range(len(TaskList)):
			if TaskList[x][4] == name and name != None:
				TaskList[x] = task 
				existed = True
				break 
		if not existed:
			TaskList.append(task)
		TaskList.sort()
		global _Tasker
		
		if len(TaskList) == 0 :
			TimerInfo[3] = TimerInfo[1] + 300000 
			TimerInfo[4] = False
		else :
			if TaskList[0][0] - TimerInfo[1] < 0 :
				TimerInfo[3] = TimerInfo[1] + 1
				TimerInfo[4] = True
			else :
				if TaskList[0][0] - TimerInfo[1] > 300000:
					TimerInfo[3] = TimerInfo[1] + 300000
					TimerInfo[4] = False
				else :
					TimerInfo[3] = TimerInfo[1] + (TaskList[0][0]-TimerInfo[1])
					TimerInfo[4] = True
		_Tasker.deinit()
		_Tasker.init(period = (TimerInfo[3]-TimerInfo[1]) , mode = Timer.ONE_SHOT , callback = _TimerHanler)
	
  
def _TaskControl():
	global TaskList,TimerInfo
	TimerInfo[5] = 0
	for x in range(len(TaskList)):
		TimerInfo[5] += TaskList[x][6] / TaskList[x][5] * 100 
	if TimerInfo[5] > 80 :
		for x in range(len(TaskList)):
			if TaskList[x][8] == False :
				TaskList[x][5] += 10
	else :
		for x in range(len(TaskList)):
			if TaskList[x][5] > TaskList[x][7] :
				TaskList[x][5] -= 10
	
AddTask(name='sys_taskcontrol',mode='repeat',function = _TaskControl,time = 15000)

def sync_clock(Force = False):
	global TimerInfo , ScheduleList
	if TimerInfo[2] == None or Force == True : # Only sync NTP once to avoid float mis-align
		import ustruct , usocket 
		try :
			f = open('System/config.json')
			gmt = ustruct.loads(f.read())['timezone']
		except :
			gmt = 7 # Default for Vietnam timezone
		try :
			NTP_QUERY = bytearray(48)
			NTP_QUERY[0] = 0x1b
			s = usocket.socket(usocket.AF_INET,usocket.SOCK_DGRAM)
			s.settimeout(2)
			res = s.sendto(NTP_QUERY,usocket.getaddrinfo("pool.ntp.org",123)[0][-1])
			msg = s.recv(48)
			s.close()
			ntp = ustruct.unpack("!I",msg[40:44])[0]
			ntp -= 3155673600
			if ntp > 0: # Correct time 
				from time import localtime
				ntp += gmt*3600 #GMT time
				TimerInfo[2] = (time(),ntp)
				print('Synced ' , localtime(ntp))
				
		except:
			AddTask(function=sync_clock,mode='once',time = 10000)
			return 
	from time import mktime , ticks_ms
	for i in range(len(ScheduleList)):
		date,month,year = map(int,ScheduleList[i-1]['date'].split('/'))
		hour,minute,second = map(int,ScheduleList[i-1]['time'].split(':'))
		ntptime = mktime([year,month,date,hour,minute,second,0,0])
		if ntptime < TimerInfo[2][1] :
			continue 
		AddTask(function = ScheduleList[i-1]['function'],name = ScheduleList[i-1]['name'],	mode= 'once',time =  (ntptime - clock())*1000)
	ScheduleList.clear()
	TaskList.sort()
	if len(TaskList) == 0 :
		TimerInfo[3] = TimerInfo[1] + 300000 # Call itself every 5 minutes
		TimerInfo[4] = False
	else :
		if TaskList[0][0] - TimerInfo[1] < 0 :
			TimerInfo[3] = TimerInfo[1] + 1
			TimerInfo[4] = True
		else :
			if TaskList[0][0] - TimerInfo[1] > 300000:
				TimerInfo[3] = TimerInfo[1] + 300000
				TimerInfo[4] = False
			else :
				TimerInfo[3] = TimerInfo[1] + (TaskList[0][0]-TimerInfo[1])
				TimerInfo[4] = True
	global _Tasker
	_Tasker.deinit()
	_Tasker.init(period = TimerInfo[3]-TimerInfo[1] , mode = Timer.ONE_SHOT , callback = _TaskHandler)
      

	





