#All times in MILLISECONDS !!

#The required modules are imported
import copy, pxi, easygui, math, os
#The descriptors of the hardware are initialized according to system.txt
digitalout=pxi.digitalout()
analogout=pxi.analogout()
device=pxi.device()

verbose= False
#change to True to get warnings. 


class stchg:
	""" The statechange (stch) class contains information for
		a simple state change:
		the values of all the DIGITAL_OUT's and the time of
		the state change.
		"""
	def __init__(self,digi=digitalout.dflts,time=0.0): 
		self.digi=digi
		self.time=time
	def __cmp__(self,other):
		return cmp(self.time,other.time)
	def __str__(self):
		s=str(self.time).rjust(8)+'!'
		for state in self.digi:
			s=s+str(state).rjust(10)+'!'
		s=s+'\n'
		return s
	def fileoutput(self):
		return self.__str__()
		
class wfmout_plus:
	""" The wfmout_plus class is an improved version of the wfmout class. It intends to replace
		the wfmout class completely.
		
		wfmout_plus consists of a list of sublists, called aouts, where each sublist is of the form
		[ "channelname", wfm ]  
		where wfm is an instance of the wfm class defined in wfm.py,  for example:
		
			[ ['bfield', bfield0], ['odtpow', evapramp], ...]
			
		all wfm's in a wfmout_plus instance should have the same time step, otherwise an exception
		will be raised and the sequence won't compile.  
		
		... 10/12/2011 ... I'm still working on this class ( pedro m duarte) 
				
	"""
	def __init__(self,tcur,wfmstep):
		self.time=tcur
		self.step=wfmstep
		self.aouts=[]
		#aouts is a list of sublists of the form:
		#Example: ['chname',wfm]
		self.isvalid=True
		self.length=0  #max number all samples... all channels must have the same # of samples
	def __cmp__(self,other):
		return cmp(self.time,other.time)
	def __str__(self):
		s1='#\nWAVEFORM:\nTIME\t%.4f\nSTEP\t%.4f\n' % (self.time, self.step)
		s2=''
		# find max number of samples and assign it to length
		for ch in self.aouts:
			s2=s2+ch[0]+'\n'
			try:
				print None
				#print the contents of wfm here
			except:
				#show error if for some reason contents of wfm could not be printed
				print 'ERROR: Cannot print wfm for ch %s' % ch[0]
				return ''
			#Append all the needed extra samples
			for i in range(self.length-ch[1].N()):
				s2=s2+endvalue
			s2=s2+'\n'
		return s1+s2
	def fileoutput(self):
		return self.__str__()

class wfmout:
	""" The wfmout  class contains information for a
		waveform output (wfmout) in the sequence.  In the sequence,
		a wfmout consists of an arbitrary waveform on one or more
		ANALOG_OUT's in one or more ANALOG_DEVICE's that is triggered
		at a certain time. This time is a multiple of the sequence STEP.

		The waveform outputs are added to the sequence one at a time
		using the anlgwfm function (see sequence class).  Once added they
		cannot be modified (e.g. you can't add more channels to the
		waveform)

		To create a wfmout you need the step size and a parameter called
		aouts which is a list of dictionaries, for example:

			 [{'name':'channelname',\
			   'path':adiabaticOff},\
			  {'name':'nc-01',\
			   'path':adiabaticOff}]

		Each dictionary in the list represents a physical analog out channel.
		The dictionary contains the keys:

		'name'  :  The ANALOG_OUT channel name.
		'path'  :  A file path that contains the values to output:

		The file should be a text file with JUST 1 line in the following format:
		value1,value2,value3,...value###

		If the files for different channels don't have the same length, constant
		samples will be appended as necessary to make all the channels have the
		same duration. To do this the __init__ method creates an extra dictionary
		key called 'length' for each channel in the output.  This extra key
		is used when writing the sequence fileoutput.

		Since there are buffer limitations there will be an error if a waveform
		has too many samples or lasts too long.  There might also be PXI buffer
		related errors if the waveform is too short.
		"""
	def __init__(self,tcur,wfmstep,aouts):
		self.time=tcur
		self.step=wfmstep
		self.aouts=aouts
		#aouts is a list of dictionaries of the form:
		#Example: {'name':'chname', 'path':'arb.txt'}
		self.aouts=aouts
		self.isvalid=True
		self.length=0
		maxlen=0
		for ch in self.aouts:
			try:
				arb=open(ch['path'],"r")
				line=arb.readline().split(',')
				if int(len(line))>maxlen:
					maxlen=int(len(line))
				ch['length']=int(len(line))
				arb.close()
			except:
				print 'ERROR: Cannot open %s' % ch['path']
				self.isvalid=False
		self.length = maxlen
		if (self.length % 2) != 0:
			self.length = self.length +1
		if self.length*len(self.aouts) > 1e7:
			print 'There are probably too many samples (>1e7) in this waveform. Beware of buffer errors'
		print "...Added wfmout to sequence: %d samples" % self.length
	def __cmp__(self,other):
		return cmp(self.time,other.time)
	def __str__(self):
		s1='#\nWAVEFORM:\nTIME\t%.4f\nSTEP\t%.4f\n' % (self.time, self.step)
		s2=''
		for ch in self.aouts:
			s2=s2+ch['name']+'\n'
			try:
				arb=open(ch['path'],"r")
				s2=s2+arb.readline()
				arb.close()
			except:
				print 'ERROR: Cannot open %s' % ch['path']
				return ''
			#Find the value after the last ',' and strips the end of line
			endvalue=',%.4f' % float(s2[s2.rfind(',')+1:-1])
			#Append all the needed extra samples
			for i in range(self.length-ch['length']):
				s2=s2+endvalue
			s2=s2+'\n'
		return s1+s2
	def fileoutput(self):
		return self.__str__()
		
			
class sequence:
	""" The sequence class is the responsible for creating arbitrary time sequences.
		It relies on the stchg and wfmout classes. A sequence simply consists of
		a list of stchg's and a list of wfmout's.  It keeps track of the current
		time as events are added to it and when an event is added it stores the time
		for the event inside the event itself.  
		"""
	def __init__(self,step=0.01):
		self.tcur=0.0 #The current time in ms.
		#The first stch is created. This has the default states
		#as specified in 'system.txt' and a time=0.0
		self.chgs=[]
		self.chgs.append(stchg())
		self.wfms=[]
		self.step=step
	def __str__(self):
		string='';
		string = string +'#\nSTEP '+str(self.step)+'\n'
		string = string + 'time(ms)!'
		global digitalout
		for name in digitalout.names:
			string = string+ name.rjust(10)+'!'
		string = string +'\n'
		for elem in self.chgs:
			string = string + elem.fileoutput()
		for elem in self.wfms:
			string = string + elem.fileoutput()
		string = string +'#\n'
		return string
	def timesort(self):
		self.chgs.sort()
	def save(self,filename=None):
		self.timesort()
		if filename == None:
			filename=easygui.filesavebox(None,'Select file to save compressed sequence','L:/software/apparatus3/sequence/')
		f = open(filename,"w")
		f.write(self.__str__())
		f.close()
		#Get SaveDir and RunNumber to save a copy of expseq
		f=open('L:/data/app3/comms/SaveDir')
		savedir=f.readline()
		f.close
		f=open('L:/data/app3/comms/RunNumber')
		shotnum=f.readline()
		f.close
		expseq=savedir+'expseq'+shotnum+'.txt'
		f = open(expseq,"w")
		f.write(self.__str__())
		f.close()
	def clear_disk(self):
		for elem in self.wfms:
			for ch in elem.aouts:
				try : 
					#print 'Removing %s' % ch['path']
					os.remove(ch['path'])
				except:
					print 'ERROR: Cannot delete from disk %s' % ch['path']

	#Here are the four key methods for creating a sequence
	#
	# digichg
	# digpulse
	# analogwfm
	# wait
		
	def digichg(self,name,state):
		""" digichg appends to sequence a stchg that consists of 
			setting the state of a specified DIGITAL_OUT. """		
		global digitalout
		global verbose
		if state!=0 and state !=1:
			print "Invalid DIGITAL_OUT state!! (not boolean)"
			return
		if self.chgs[-1].time > self.tcur:
			if verbose:
				print 'Be careful, you are going back in time.'
			#If you go back in time, the new state has to propagate to other times in the future !!
			#First find out where the state change goes by looking into self.chgs, also determine if there is already a state change for
			#this same_time
			stch_tcur =-1
			same_time =False
			for index in range(len(self.chgs)):
				if self.chgs[index].time < self.tcur:
					stch_tcur=index
				if self.chgs[index].time == self.tcur:
					stch_tcur=index	  
					same_time = True;
			if stch_tcur == -1:	
				if verbose:
					print 'Something went wrong going back in time. Revise the program'
				exit(1)
			#This if statement prevents writing when there is no change.
			if self.chgs[stch_tcur].digi[digitalout.num[name]]!=state:
				if same_time ==True:
					self.chgs[stch_tcur].digi[digitalout.num[name]]=state 
				
				else:
					#Create a copy of the last state
					lastcopy=copy.deepcopy(self.chgs[stch_tcur])
					#Modify the state change line
					lastcopy.time=self.tcur
					lastcopy.digi[digitalout.num[name]]=state
					#Insert
					self.chgs.append(lastcopy)		
					self.timesort()
					#~ print
					#~ print 'If you have digichg`s, digpulse`s and analogwfm`s that need to'
					#~ print 'occur at the same tick add them in that order.'
					#~ print
					#~ print 'In other words never put a digichg right after a digpulse or analogwfm!'
					#~ print 
					#~ print 'Check your output to see if the program did what you wanted.'
					#If it is still the same time just change the last state.
			#Propagate change to the future (even if there is no change at tcur),  Be careful this could overwrite previously programmed state changes.
			for index in range(len(self.chgs)):
				if self.chgs[index].time > self.tcur:
					self.chgs[index].digi[digitalout.num[name]]=state
		#Below is the normal stuff,(when there has been no back in time)
		#If time is still the same change last state
		elif self.chgs[-1].time==self.tcur:
			#This if statement prevents writing when there is no change.
			if self.chgs[-1].digi[digitalout.num[name]]!=state:
				self.chgs[-1].digi[digitalout.num[name]]=state             
		#If time has passed create a new state and insert
		else:
			#This if statement prevents writing when there is no change.
			if self.chgs[-1].digi[digitalout.num[name]]!=state:
				#Creaty a copy of the last state
				lastcopy=copy.deepcopy(self.chgs[-1])
				#Modify the line in question (name)
				lastcopy.time=self.tcur
				lastcopy.digi[digitalout.num[name]]=state
				#Insert
				self.chgs.append(lastcopy)


	def digpulse(self,names,duration=None):
		""" digpulse appends to the sequence a change to high
			and then to low of the DIGITAL_OUT specified by name.
			The DIGITAL_OUT is kept high for the duration of step.
			"""
		if duration == None:
			duration = self.step
		for name in names:
			if self.chgs[-1].digi[digitalout.num[name]] == 1:
				print 'Cant append pulse on ' + name \
					  + '\n. It is already high!'
				print 'Why would the trigger line be idle high?'
				print 'Please investigate'
			else:
				self.digichg(name,1)
				self.wait(duration)
				self.digichg(name,0)
				#Goes back in time to leave self.tcur where it was.
				self.wait(-duration)
		
	def digdflts(self):
		""" digdflts appends to the sequence a change to the digital 
		default values that are stored in system.txt
		"""
		global digitalout
		append=True
		i=0
		for i in range(digitalout.len):
			if self.chgs[-1].digi[i] != digitalout.dflts[i]:
				append=True
		#~ print digitalout.dflts
		if append:
			self.chgs.append(stchg(digitalout.dflts,self.tcur))
			
			
	def diglow(self):
		""" diglow sets all the DIGITAL_OUT lines to low.
			"""
		global digitalout
		append=False
		i=0
		for i in range(digitalout.len):
			if self.chgs[-1].digi[i] != 0:
				append=True
		if append:
			self.chgs.append(stchg([0]*digitalout.len,self.tcur))
	
	def analogwfm(self,step,aouts):
		""" analogwfm adds a waveform output to the sequence.
			The device is determined from the name and a pulse
			is added to the DIGITAL_OUT that triggers the device.
			This function makes sure that the added waveform does
			not conflict with any waveform ouptuts already in the
			sequence.
			"""
		global analogout, device
		w=wfmout(self.tcur,step,aouts)
		if w.isvalid:
			self.wfms.append(w)
			#Sets pulses to trigger the waveform in the necessary devices.
			devs=[]
			for elem in w.aouts:
				devname=analogout.physCh[elem['name']].split('/')[0]
				if devname not in devs:
					devs.append(devname)
			trigs=[]
			for dev in devs:
				trigs.append(device.trigout[dev])
			#Pulse width is wd times the step size
			wd = 5
			self.digpulse(trigs,wd*self.step)
			return w.step*w.length
		else:
			return 0
			
	def analogwfm_add(self,step,wfms):
		""" analogwfm_add adds a waveform output ot the sequence.
			aouts is an array of waveforms (instances of the wfm class)
			The device is determined from the names of the wfm's 
			and a pulse is added to the DIGITAL_OUT that triggers
			the device.  This function makes sure that the added
			waveform does not conflict with any waveform outputs
			already in the sequence.
			"""
		aouts = []
		
		#print("...start adding waveforms.")
		for elem in wfms:
			dict = {}
			dict["name"] = elem.name
			filename = 'L:/software/apparatus3/seq/ramps/'+elem.name+ '_'+ elem.wfm_id() +'.txt'
			elem.fileoutput(filename)
			#print ("filename = %s" % filename)
			dict["path"] = filename
			aouts.append(dict)
			
		#print("...end adding waveforms.")
		
		self.analogwfm(step,aouts)
		return 0
	
	def wait(self,delay):
		""" wait changes the current time.
			"""
		#Ensures you only wait intervals that are multiples of
		#the step size.
		self.tcur = self.tcur + math.floor(delay/self.step)*self.step
		if self.tcur<0:
				print "Sequence time (t=" + str(self.tcur) + ") is less than zero. Went back in time too far."
				print "Solution: Add a small delay at the beggining of the sequence to compensate."
				exit(1)

	###########################################################
	# Sequence call EXAMPLES:
	#
	
	def PrimitiveSeqCall(self,delay):
		""" A primitive sequence call contains only digichg's,
			analogwfm's and wait's.
			"""
		self.digichg('nc-00',1)
		self.digichg('nc-01',1)
		self.wait(delay)
		self.digichg('nc-01',0)
			
	def UserDefined(self,state):
		""" A user defined calls can be defined with arguments
			and conditionals to have a more clear way of doing stuff.
			"""
		#This way you can turn on/off 'nc-01'
		#by changing the 'state' argument of the function.
		self.digichg('nc-01',state)

   

	def TwoChsAdiabaticOn(self):
		""" An example that shows how to use the analogwfm method.
			"""
		#A waveform to turn on adiabatically nc-00 and nc-01 is added.
		#The step size is 0.001ms and the values are in the indicated path.
		self.analogwfm(0.001,[{'name':'nc-00',\
							   'path':'L:/software/apparatus3/ramps/adiabatic_tanh_On.txt'},\
							  {'name':'nc-01',\
							   'path':'L:/software/apparatus3/ramps/adiabatic_tanh_On.txt'}])
							   
	def TwoChsAdiabaticOff(self):
		""" An example that shows how to use the analogwfm method.
			The paths don't have to be hardcoded, they can be arguments
			defined somewehere else for ease of use.
			"""
		#A waveform to turn off adiabatically nc-00 and nc-01 is added.
		#The step size is 0.001ms and the values are in the indicated path.
		self.analogwfm(0.001,[{'name':'nc-00',\
							   'path':'L:/software/apparatus3/seq/ramps/adiabatic_tanh_Off.txt'},\
							  {'name':'nc-01',\
							   'path':'L:/software/apparatus3/seq/ramps/adiabatic_tanh_Off.txt'}])

	def DownLeft(self,state):
		""" Draws an LED arrow pointing downleft in the front panel. """
		self.digichg('nc-00',state)
		self.digichg('nc-01',state)
		self.digichg('nc-02',state)
		self.digichg('nc-03',state)
		self.digichg('nc-04',state)
		self.digichg('nc-05',state)
		self.digichg('nc-06',state)
		self.digichg('nc-07',state)
		self.digichg('nc-11',state)
		self.digichg('nc-12',state)
		self.digichg('nc-14',state)
		self.digichg('nc-15',state)
		self.digichg('nc-16',state)
		self.digichg('nc-22',state)
		self.digichg('nc-23',state)
	
	def row1(self,state):
		self.digichg('nc-00',state)
		self.digichg('nc-02',state)
		self.digichg('nc-04',state)
		self.digichg('nc-06',state)
	def row2(self,state):
		self.digichg('nc-01',state)
		self.digichg('nc-03',state)
		self.digichg('nc-05',state)
		self.digichg('nc-07',state)    
	def row3(self,state):
		self.digichg('nc-08',state)
		self.digichg('nc-10',state)
		self.digichg('nc-12',state)
		self.digichg('nc-14',state)
	
	def letterA(self,state):
		self.row1(state)
		self.digichg('nc-01',state)
		self.digichg('nc-03',state)
		self.row3(state)
	def letterT(self,state):
		self.digichg('nc-00',state)
		self.row2(state)
		self.digichg('nc-08',state)
	def letterO(self,state):
		self.row1(state)
		self.digichg('nc-01',state)
		self.digichg('nc-07',state)
		self.row3(state)
	def letterM(self,state):
		self.row1(state)
		self.digichg('nc-03',state)
		self.row3(state)
	def letterC(self,state):
		self.row1(state)
		self.digichg('nc-01',state)
		self.digichg('nc-07',state)
		self.digichg('nc-08',state)
		self.digichg('nc-14',state)
	def letterL(self,state):
		self.row1(state)
		self.digichg('nc-07',state)	
		self.digichg('nc-14',state)
	
	def atomcool(self):
		self.diglow()
		self.letterA(1)
		self.wait(800)
		self.letterA(0)
		self.wait(200)
		self.letterT(1)
		self.wait(800)
		self.letterT(0)
		self.wait(200)
		self.letterO(1)
		self.wait(800)
		self.letterO(0)
		self.wait(200)
		self.letterM(1)
		self.wait(800)
		self.letterM(0)
		self.wait(200)
		self.letterC(1)
		self.wait(800)
		self.letterC(0)
		self.wait(200)
		self.letterO(1)
		self.wait(800)
		self.letterO(0)
		self.wait(200)
		self.letterO(1)
		self.wait(800)
		self.letterO(0)
		self.wait(200)
		self.letterL(1)
		self.wait(800)
		self.letterL(0)
		self.wait(200)
		self.diglow()
 

	
	

	###########################################################
	# Define sequence calls below:
	#	
