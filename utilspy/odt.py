"""Constructs ramps relevant to the ODT
	
"""
import wfm, gen, math, cnc, time, os, numpy, hashlib, evap

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])
	
def odt_evap(image):
	evap_ss = f('EVAP','evapss')

	p0   = f('ODT','odtpow')
	p1   = f('EVAP','p1')
	t1   = f('EVAP','t1')
	tau  = f('EVAP','tau')
	beta = f('EVAP','beta')
	
	offset = f('EVAP','offset')
	t2     = f('EVAP','t2')
	tau2   = f('EVAP','tau2')
		
	odtpow = odt_wave('odtpow', p0, evap_ss)
	#odtpow.Evap(p0, p1, t1, tau, beta, image)
	#odtpow.Evap2(p0, p1, t1, tau, beta, offset, t2, tau2, image)
	finalcpow = odtpow.Evap3(p0, p1, t1, tau, beta, offset, t2, tau2, image)
	
	#ipganalog starts out at full power
	ipganalog = ipg_wave('ipganalog', 10., evap_ss)
	
	if f('ODT','use_servo') == 0:
		ipganalog.extend( odtpow.dt() )
	elif f('ODT','use_servo') == 1:
		ipganalog.follow( odtpow )
		
	
	#~ odtpow.Exponential(pow0,powf,evap_dt,tau)
	#~ odtpow.linear( powf, evap_ss)
	#~ odtpow.appendhold( evap_dt)
	
	maxDT = odtpow.dt()
	
	return odtpow, maxDT, finalcpow, ipganalog
	
def odt_lightshift_evap(image):
	evap_ss = f('EVAP','evapss')

	p0   = f('ODT','odtpow')
	p1   = f('EVAP','p1')
	t1   = f('EVAP','t1')
	tau  = f('EVAP','tau')
	beta = f('EVAP','beta')
	
	offset = f('EVAP','offset')
	t2     = f('EVAP','t2')
	tau2   = f('EVAP','tau2')
		
	odtpow2 = odt_wave('odtpow', p0, evap_ss)
	#odtpow.Evap(p0, p1, t1, tau, beta, image)
	#odtpow.Evap2(p0, p1, t1, tau, beta, offset, t2, tau2, image)
	ficpow = odtpow2.Evap3(p0, p1, t1, tau, beta, offset, t2, tau2, image)
	
	uvdet = wfm.wave('uvdet', None , evap_ss, volt=3.744)
	uvdet.linear( f('UVLS','uvdet'), 100 )
	
	maxDT = odtpow2.dt()
	uvdet.extend(maxDT)
	
	return odtpow2, uvdet, maxDT
	
def odt_lightshift(odtpow0):
	ls_ss = f('UVLS','ls_ss')

	odtpow  = odt_wave('odtpow',  None, ls_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), ls_ss)
	uv1freq = wfm.wave('uv1freq', None , ls_ss, volt=7.600)
	uvpow2   = wfm.wave('uvpow2',   f('UV','uvpow2'), ls_ss)


	uv1freq.linear( None, 10.0, volt=f('UVLS','uvfreq'))
	uvpow2.linear(  f('UVLS','lspow2'), 10.0)
		
	odtpow.linear( f('UVLS','cpow'), f('UVLS','cdt') )
	odtpow.appendhold( f('UVLS','waitdt'))
	bfield.extend(odtpow.dt())
	
	bfield.linear( f('UVLS','bpulse'), f('UVLS','bdt') )
	bfield.appendhold( f('UVLS','waitdt2'))
	bfield.appendhold( f('UVLS','waitdt3'))
	ENDC=bfield.dt()

	#~ bfield.linear( f('UVLS','bpulse') , f('UVLS','bdt') )
	#~ bfield.appendhold(f('UVLS','waitdt'))
	#~ odtpow.extend(bfield.dt())
	
	#~ odtpow.linear( f('UVLS','cpow'), f('UVLS','cdt') )
	#~ odtpow.appendhold( f('UVLS', 'waitdt2'))
	#~ ENDC = odtpow.dt()
	
	#~ bfield.extend( odtpow.dt() )
	
	odtpow.extend( bfield.dt() )
	bfield.appendhold( f('UVLS','dtpulse')) 
	

	bfield.linear( f('ZEROCROSS','zcbias') , f('UVLS','hframpdt'))
	#Change f('FESHBACH','bias') -> f('ZEROCROSS','zcbias') 110911 by Ernie
	#bfield.linear( 0.0, f('UVLS','hframpdt'))
	
	totalDT = bfield.dt()
	
	odtpow.extend(totalDT)
	uv1freq.extend(totalDT)
	uvpow2.extend(totalDT)
	
	return odtpow, bfield, uv1freq, uvpow2, ENDC
	
def odt_trapfreq(odtpow0):
	mod_ss = f('TRAPFREQ','mod_ss')

	odtpow  = odt_wave('odtpow',  None, mod_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), mod_ss)
	
	odtpow.linear( f('TRAPFREQ','cpow'), f('TRAPFREQ','cdt') )
	odtpow.appendhold( f('TRAPFREQ','waitdt'))
	bfield.extend(odtpow.dt())
	
	bfield.linear( f('TRAPFREQ','bmod'), f('TRAPFREQ','bdt') )
	bfield.appendhold( f('TRAPFREQ','waitdt2'))
	
	odtpow.extend( bfield.dt() )
	#odtpow.SineMod( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	#odtpow.SineMod2( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	odtpow.SineMod3( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	
	return odtpow, bfield, odtpow.dt()
	
def odt_flicker(odtpow0):
	flicker_ss = f('FLICKER','flicker_ss')

	odtpow  = odt_wave('odtpow',  None, flicker_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), flicker_ss)
	
	odtpow.linear( f('FLICKER','cpow'), f('FLICKER','cdt') )
	odtpow.appendhold( f('FLICKER','waitdt'))
	bfield.extend(odtpow.dt())
	
	bfield.linear( f('FLICKER','bflick'), f('FLICKER','bdt') )
	bfield.appendhold( f('FLICKER','waitdt2'))
	
	odtpow.extend( bfield.dt() )
	
	return odtpow, bfield, odtpow.dt()
	
def odt_dbz(odtpow0):
	dbz_ss = f('DBZ','dbz_ss')

	odtpow  = odt_wave('odtpow',  None, dbz_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), dbz_ss)
	
	odtpow.linear( f('DBZ','cpow'), f('DBZ','cdt') )
	odtpow.appendhold( f('DBZ','waitdt'))
	bfield.extend(odtpow.dt())
	
	#Field goes to zero
	bfield.linear( 0.0, f('DBZ','bdt') )
	bfield.appendhold( f('DBZ','waitdt2'))
	#Field TTL goes off here
	OFFDT1 = bfield.dt()
	bfield.appendhold( f('DBZ','switchdt'))
	#Field switches from feshbach to gradient here
	bfield.appendhold( f('DBZ','switchdt'))
	#Field TTL goes back on here
	bfield.appendhold( f('DBZ','switchdt'))
	bfield.linear( f('DBZ', 'dbz'), f('DBZ','rampdt'))
	bfield.appendhold( f('DBZ','holddt'))
	#Field goes off here (atoms should be oscillating in the trap)
	bfield.linear( 0.0, f('DBZ','dbz_ss'))
	
	odtpow.extend( bfield.dt() )
	return odtpow, bfield, OFFDT1


###########################################
#### IPG ANALOG WAVEFORM ###
###########################################


class ipg_wave(wfm.wave):
	"""The ipg_wave class helps construct the waveform that 
		will be used to reduce the 50 Watt ipg power during
		evaporation. 
		
		The main method is 'follow', which allows the 
		ipg to be reduced as evaporation proceeds, always putting
		out enough power to let the servo be in control and also
		taking care not to go below 20% ipg output power, where
		the noise spectrum of the laser is increased.
		"""
	def follow(self, odtpow):
		ipgmargin =  10.; #  5% margin for ipg
		ipgmin    = 50.; # 20% minimum output power for ipg 
		# Change to 50 ( 03022012 by Ernie, since we see 20 is noisey on light)
		self.y = numpy.copy(odtpow.y)
		
		print "Inside follow"
		
		for i in range(self.y.size):
			odt = OdtpowConvertPhys(self.y[i])
			ipg =  odt + 10.*ipgmargin/100.
			if ipg > 10.0:  #can't do more than 10.0 Volts
				ipg = 10.0
			if ipg < 10.*ipgmin/100.:  #should not do less than ipgmin
				ipg = 10.*ipgmin/100.
			self.y[i] = ipg
			print "%.3f -> %.3f\t" % (odt,ipg)


###########################################
#### LOWER LEVEL CODE FOR ODT WAVEFORMS ###
###########################################

if f('ODT','use_servo') == 0:
	b=float(report['ODTCALIB']['b_nonservo'])
	m1=float(report['ODTCALIB']['m1_nonservo'])
	m2=float(report['ODTCALIB']['m2_nonservo'])
	kink=float(report['ODTCALIB']['kink_nonservo'])
elif f('ODT','use_servo') == 1:
	b=float(report['ODTCALIB']['b'])
	m1=float(report['ODTCALIB']['m1'])
	m2=float(report['ODTCALIB']['m2'])
	kink=float(report['ODTCALIB']['kink'])

it=0

def OdtpowConvert(phys):
	# odt phys to volt conversion
	# max odt power = 10.0
	volt = b+m1*kink+m2*(phys-kink) if phys > kink else b+m1*phys
	global it
	#if it  <10:
	#	print "phys=%.3f  ==> volt = %.3f" % (phys,volt)
	it = it + 1 
	return volt
	
def OdtpowConvertPhys(volt):
	# odt volt to phys conversion
	phys = (volt-b)/m1
	if phys > kink:
		phys = (volt - (b+m1*kink))/m2 + kink
	return phys


class odt_wave(wfm.wave):
	"""The odt_wave class helps construct arbitrary waveforms
		that will be ouutput to the odtpow channel. 
		It inherits from the base wave class defined in wfm 
		and adds further functionality for evaporation, etc."""
	def __init__(self,name,val,stepsize,N=1,volt=-11):
		"""Initialize the waveform  """
		self.idnum = time.time()*100
		self.name = name
		if volt != -11:
			val=volt
		else:
				val=OdtpowConvert(val)
				
		self.y= numpy.array(N*[val])
		self.ss=stepsize
		#print ("...Initialized waveform %s, idnum=%s" % ( self.name, self.wfm_id()))
		
	def odt_linear(self,p0,pf,dt):
		"""Adds linear ramp to waveform, starts at 'p0' 
			value and goes to 'pf' in 'dt' 
			CAREFUL: This uses OdtpowConvert and is only valid for odtpow"""
		print "...ODT Linear from %.3f to %.3f" % (p0,pf)
		if dt == 0.0:
			self.y[ self.y.size -1] = OdtpowConvert(pf)
			return
		else:
			N = int(math.floor(dt/self.ss))
			for i in range(N):
				self.y=numpy.append(self.y, [OdtpowConvert( p0 + (pf-p0)*(i+1)/N )])
		return 


	def Evap(self, p0, p1, t1, tau, beta, duration):
		"""Evaporation ramp v1"""
		if duration <=0:
			return
		else:
			N=int(round(duration/self.ss))
			print '...Evap nsteps = ' + str(N)
			ramp=[]
			ramphash = 'L:/software/apparatus3/seq/ramps/' + 'Evap_' \
					   + hashlib.md5(str(self.name)+str(self.ss)+str(duration)+str(p0)+str(p1)+str(t1)+str(tau)+str(beta)).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new Evap ramp'
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = evap.v1(t,p0,p1,t1,tau,beta)
					volt = cnv(self.name,phys)
					ramp = numpy.append( ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated Evap ramp'
				ramp = numpy.fromfile(ramphash,sep=',')

			self.y=numpy.append(self.y,ramp)
		return
		
		
	def Evap2(self, p0, p1, t1, tau, beta, offset, t2, tau2, duration):
		"""Evaporation ramp v2"""
		if duration <=0:
			return
		else:
			N=int(round(duration/self.ss))
			print '...Evap nsteps = ' + str(N)
			ramp=[]
			ramphash = 'L:/software/apparatus3/seq/ramps/' + 'Evap2_' \
					   + hashlib.md5(str(self.name)+str(self.ss)+str(duration)+str(p0)+str(p1)+str(t1)+str(tau)+str(beta)\
					                  + str(offset)+str(t2)+str(tau2)).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new Evap2 ramp'
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = evap.v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)
					volt = cnv(self.name,phys)
					ramp = numpy.append( ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated Evap2 ramp'
				ramp = numpy.fromfile(ramphash,sep=',')

			self.y=numpy.append(self.y,ramp)
		return
		

	def Evap3(self, p0, p1, t1, tau, beta, offset, t2, tau2, duration):
		"""Evaporation ramp v2"""
		if duration <=0:
			return
		else:
			N=int(round(duration/self.ss))
			print '...Evap nsteps = ' + str(N)
			ramp=[]
			hashbase = '%.8f,%.8f,%.8f,%.8f,%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f ' \
			           % ( b,m1,m2,kink, self.name, self.ss, duration, p0, p1, t1, tau, beta, offset, t2, tau2)
			ramphash = 'L:/software/apparatus3/seq/ramps/'+'Evap3_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new Evap3 ramp'
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = evap.v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)                    
					volt = OdtpowConvert(phys)
					ramp = numpy.append( ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated Evap3 ramp'
				ramp = numpy.fromfile(ramphash,sep=',')

			self.y=numpy.append(self.y,ramp)

		#This returns the last value of the ramp
		return evap.v2(N*self.ss,p0,p1,t1,tau,beta,offset,t2,tau2)
		
	def SineMod(self, p0, dt, freq, depth):
		"""Sine wave modulation on channel"""
		if dt <= 0.0:
			return
		else:
			N=int(math.floor(dt/self.ss))
			ramp=[]
			hashbase = '%s,%.3f,%.3f,%.3f,%.3f,%.3f ' % ( self.name, self.ss, p0, dt, freq, depth)
			ramphash = 'L:/software/apparatus3/seq/ramps/'+'SineMod_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new SineMod ramp:  %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = p0 + (0.5*p0*depth/100.)* math.sin(  t * 2 * math.pi * freq/1000. )
					volt = cnv(self.name,phys)
					ramp = numpy.append(ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated SineMod ramp %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				ramp = numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y,ramp)
		return
		

		
		
	def SineMod2(self, p0, dt, freq, depth):
		"""Sine wave modulation on channel"""
		if dt <= 0.0:
			return
		else:
			N=int(math.floor(dt/self.ss))
			ramp=[]
			hashbase = '%s,%.3f,%.3f,%.3f,%.3f,%.3f ' % ( self.name, self.ss, p0, dt, freq, depth)
			ramphash = 'L:/software/apparatus3/seq/ramps/'+'SineMod2_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new SineMod ramp:  %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = p0 + (0.5*p0*depth/100.)* math.sin(  t * 2 * math.pi * freq/1000. )
					volt = OdtpowConvert(phys)
					ramp = numpy.append(ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated SineMod ramp %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				ramp = numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y,ramp)
		return
		
	def SineMod3(self, p0, dt, freq, depth):
		"""Sine wave modulation on channel"""
		if dt <= 0.0:
			return
		else:
			N=int(math.floor(dt/self.ss))
			ramp=[]
			hashbase = '%.8f,%.8f,%.8f,%.8f,%s,%.3f,%.3f,%.3f,%.3f,%.3f ' % ( b,m1,m2,kink, self.name, self.ss, p0, dt, freq, depth)
			ramphash = 'L:/software/apparatus3/seq/ramps/'+'SineMod3_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new SineMod3 ramp:  %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = p0 + (0.5*p0*depth/100.)* math.sin(  t * 2 * math.pi * freq/1000. )
					volt = OdtpowConvert(phys)
					ramp = numpy.append(ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated SineMod3 ramp %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				ramp = numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y,ramp)
		return