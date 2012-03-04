import math

def getAndorConf():
	#The parameters are loaded from the andorconf.INI file
	from configobj import ConfigObj
	andorconf=ConfigObj('L:/software/apparatus3/andor/andorconf.INI')
	return andorconf


def OpenShuttersFluor(s):
	#open camera and probe beam shutters  (back in time)
	#for test purposes give it an extra 1.0ms
	test=2.0
	cameraSHUT=3.4+test #full-on time for the camera shutter (3.4ms)
	s.wait(-cameraSHUT) 
	s.digichg('camerashut',1)
	s.wait(cameraSHUT)
	motSHUT=3.5+test#full-on time for the probe shutter
	s.wait(-motSHUT)
	s.digichg('motshutter',0)
	s.wait(motSHUT)
	return s

def OpenProbeShutter(s):
	probeSHUT=5.0#full-on time for the probe shutter
	s.wait(-probeSHUT)
	s.digichg('prshutter',0)
	s.wait(probeSHUT)
	return s


def OpenShuttersProbe(s):
	#open camera and probe beam shutters  (back in time)
	#for test purposes give it an extra 1.0ms
	test=2.0
	cameraSHUT=3.4+test #full-on time for the camera shutter (3.4ms)
	s.wait(-cameraSHUT)
	s.digichg('camerashut',1)
	s.wait(cameraSHUT)

	probeSHUT=35.0#full-on time for the probe shutter
	s.wait(-probeSHUT)
	s.digichg('prshutter',0)
	s.wait(probeSHUT)
	return s
	

def AndorPictureWithClear(s,stepsize,exp,light,flash):
	#Shine probe light and return to t=0
	aoSHUT=0.0 #full-on time for the probe ao
	s.wait(-aoSHUT)
	s.digichg(light,flash)
	s.wait(aoSHUT+exp)
	s.digichg(light,0)
	s.wait(-exp)
	
	andorconf=getAndorConf()
	rows = float(andorconf['IMAGE']['rows'])
	kexp = float(andorconf['IMAGE']['kexp'])
	shif = float(andorconf['IMAGE']['shift'])
	
	if shif != 1:
		print "Error:  Shift rate is not 0.5us/row as expected."
		exit(1)
	shiftrate=0.0005
	shifttime=stepsize*math.ceil(rows*shiftrate/stepsize) #0.5us/row
	
	preexp=0.3
	
	#Pulse clear trigger
	s.wait(-(kexp/1000.+shifttime+preexp))
	s.digichg('cameratrig',1)
	trigpulse=0.05
	s.wait(trigpulse)
	s.digichg('cameratrig',0)
	s.wait(-trigpulse+kexp/1000.+shifttime+preexp)
	#This gives the camera enough time to take the trigger, expose for kexp, 
	# and then shift the rows, with an extra 0.3 ms added just in case.  
	
	
	#Pulse end of accumulation trigger 
	#Recall that probe light has already been shined right as this
	#function entered
	postexp=preexp
	s.wait(exp+postexp-kexp/1000.)
	s.digichg('cameratrig',1)
	s.wait(trigpulse)
	s.digichg('cameratrig',0)
	s.wait(-(trigpulse+exp+postexp-kexp/1000.))
	#returns the sequence at t=0 for the next picture
	return s, kexp/1000.+shifttime+preexp+exp+postexp-kexp/1000.+trigpulse

def AndorKinetics(s,exp,light,flash):
	#Shine probe light and return to t=0
	aoSHUT=0.0 #full-on time for the probe ao
	s.wait(-aoSHUT)
	s.digichg(light,flash)
	s.wait(aoSHUT+exp)
	s.digichg(light,0)
	s.wait(-exp)
	
	preexp = 0.5
	s.wait(-preexp)
	s.digichg('cameratrig',1)
	trigpulse=0.2
	s.wait(trigpulse)
	s.digichg('cameratrig',0)
	s.wait(preexp-trigpulse)
	return s

def KineticSeries4(s, exp, light, noatoms, trap):
    #Takes a kinetic series of 4 exposures:  atoms, noatoms, atomsref, noatomsref
    
    t0 = s.tcur
    
    #OPEN SHUTTERS
    if light == 'probe':
        s=OpenShuttersProbe(s)
    elif light == 'motswitch':
        s=OpenShuttersFluor(s)
        
    #PICTURE OF ATOMS
    s=AndorKinetics(s,exp,light,1)
    
    
    #SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
    #minimum time for no atoms is given by max trigger period in Andor settings
    s.wait(noatoms)
    s.digichg('field',0)
    s.digichg('odtttl',0)
    s.wait(noatoms)
    s.digichg('odtttl',trap)
    s.wait(noatoms)
    #PICTURE OF BACKGROUND
    s=AndorKinetics(s,exp,light,1)
    
    s.wait(noatoms*4)
    s.digichg('camerashut',0)
    s.digichg('prshutter',1)
    #REPRODUCE THE ABOVE TO TAKE REFERENCE IMAGES: flash=0
    s.wait(500) #Allow generous time for camera to complete a keep clean cycle
    
    if light == 'probe':
        s=OpenShuttersProbe(s)
    elif light == 'motswitch':
        s=OpenShuttersFluor(s)
    
    #PICTURE OF ATOMS
    s=AndorKinetics(s,exp,light,0)
    
    #SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
    #minimum time for no atoms is given by max trigger period in Andor settings
    s.wait(noatoms) 
    s.wait(noatoms)
    s.wait(noatoms)
    #PICTURE OF BACKGROUND
    s=AndorKinetics(s,exp,light,0)
    
    tf = s.tcur
    return s, tf-t0
    
def FKSeries2(s, stepsize, exp, light, noatoms, trap):
    #Takes a FastKinetics series of 2 exposures: atoms, noatoms
    
    t0 = s.tcur
    
    #OPEN SHUTTERS
    if light == 'probe':
        s=OpenShuttersProbe(s)
    elif light == 'motswitch':
        s=OpenShuttersFluor(s)
    
    #PICTURE OF ATOMS
    s,dt=AndorPictureWithClear(s,stepsize,exp,light,1)
    
    #CHECK THAT BACKGROUND PICTURE IS NOT TAKEN TOO FAST
    if 3*noatoms < 200.:
        print "Error:  need to wait longer between shots when using Basler\n"
        exit(1) 
    if noatoms < dt:
        print "Error:  need to wait longer between shots, clear trigger of NoAtoms will overlap with\
        \n end of accumulation trigger of Atoms"
        exit(1)    
    #SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
    s.wait(noatoms)
    s.digichg('odtttl',0)
    s.wait(noatoms)
    s.digichg('odtttl',trap)
    s.wait(noatoms)
    #PICTURE OF BACKGROUND
    s,dt=AndorPictureWithClear(s,stepsize,exp,light,1)
    
    tf = s.tcur
    
    return s, tf-t0

    
#The functions below were written before when playing with the andor but have not been tested    
    

def AndorPictureExternal(s,kexp,exp,im,flash):
	#Shine light on first frame (back in time)
	aoSHUT=0.0 #full-on time for the probe ao
	s.wait(-aoSHUT)
	s.digichg(im,flash)
	s.wait(aoSHUT+exp)
	s.digichg(im,0)
	#return to t=0
	s.wait(-exp)
	#Trigger camera (back in time)
	CamTrigDelay=(float(kexp)/1000-exp)/2.
	s.wait(-CamTrigDelay)
	s.digichg('cameratrig',1)
	#Set trigger low
	trigpulse=0.01
	s.wait(trigpulse)
	s.digichg('cameratrig',0)
	s.wait(CamTrigDelay-trigpulse)
	#returns the sequence at t=0 for the next frame
	return s
	


def multiProbe(s, light, multiN, multiDelta, multidt):\
	#Shine probe multiple times before taking the final picture
	#Test for how far detuned is the phase-contrast imaging

	s.wait(-multiDelta*multiN)
	
	#OPEN SHUTTERS
	if light == 'probe':
		s=OpenShuttersProbe(s)
	elif light == 'motswitch':
		s=OpenShuttersFluor(s)
		

	for i in range(multiN):
		print "iter = %d" % i
		s.digichg(light,1)
		s.wait(multidt)
		s.digichg(light,0)
		s.wait(-multidt)
		s.wait(multiDelta)
		
	return s
	
	
	
