""" Load ODT:  To test this sequence make sure the report file given by
	(L:/data/app3/comms/Savedir)report(L:/data/app3/comms/RunNumber).INI
	exists otherwise this code won't compile. 
"""

__author__ = "Pedro M Duarte"
__version__ = "$Revision: 0.5 $"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, cnc, uvcooling, odt, andor
from convert import cnv
report=gen.getreport()


#PARAMETERS
stepsize = float(report['CNC']['cncstepsize'])
ss       = float(report['SEQ']['analogstepsize'])
intrap   = float(report['ODT']['intrap'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

s.digichg('hfimg',1)

#Keep ODT on
ODT = gen.bstr('ODT',report)
if ODT == True:
    s.digichg('odtttl',1)
s.wait(20.0)

# Cool and Compress MOT
# ENDCNC is defined as the time up to release from the MOT
motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()

# Load UVMOT from CNCMOT
uvfppiezo, uvpow, motpow, repdet, trapdet, reppow, trappow, bfield, ENDUVMOT = uvcooling.uvcoolRamps(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC)


#trappow, reppow = cnc.state_transfer(trappow, reppow)

# Set imaging values
camera = 'ANDOR'
motpow, repdet, trapdet, reppow, trappow, maxDT = cnc.imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow, camera)

#Switch bfield to FESHBACH
switchdt  = float(report['FESHBACH']['switchdt'])
fstatedt  = float(report['ODT']['fstatedt'])
#bfield.appendhold(fstatedt)
bfield.linear(0.0,0.0)
bfield.appendhold(4*switchdt)
bias  = float(report['FESHBACH']['bias'])
bfield.linear(cnv('bfield',bias),1.0)
#bfield.ExponentialTurnOn( bias, 20.0, 3.0, 'bfield')


uvfppiezo.extend(maxDT)
uvpow.extend(maxDT)
	
# Add adiabatic ramp down to ODT
odtpow = wfm.wave('odtpow', 10.0,ss)
odtpow.extend(ENDUVMOT +  float(report['ODT']['intrap']))
odtpow.linear(2.5,1500.)
#odtpow = odt.odt_adiabaticDown(ss,ENDUVMOT)
	
#Add waveforms to sequence
s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow, odtpow])
#s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow])
	
#wait normally rounds down using floor, here the duration is changed before so that
#the wait is rounded up
ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
#insert QUICK pulse  for fast ramping of the field gradient
s.wait(-10.0)
quickval = 1 if gen.bstr('CNC',report) == True else 0
s.digichg('quick',quickval)	
s.digichg('hfquick',1)
s.wait(10.0)


#insert UV pulse
uvtime  = float(report['UV']['uvtime'])
s.wait(ENDCNC)
s.wait(uvtime)
s.digichg('uvaom1',1)
s.wait(-uvtime - ENDCNC)
	
#Go to MOT release time and set QUICK back to low
s.wait(ENDUVMOT)
s.digichg('quick',1)

s.wait(-10.)
s.digichg('odtttl',1)
s.wait(10.)

#Leave UVMOT on for state transfer

print fstatedt
s.wait(fstatedt)
s.digichg('uvaom1',0)
s.wait(-fstatedt) 
s.digichg('motswitch',0) 
s.digichg('motshutter',1)
s.digichg('field',0)



#RELEASE FROM MOT

#Go a little in the future to switch field from MOT to FESHBACH and Probe detuning
s.digichg('field',0)
s.wait(switchdt)
s.digichg('feshbach',1)
s.wait(switchdt)
s.digichg('field',1)
s.wait(100.)
s.digichg('quick',0)
s.wait(-100.)
s.wait(-2*switchdt)

#s.wait(intrap)
#wait for adiabatic ramp down
#tau = float(report['ODT']['tau'])
#s.wait( 2*tau )
#s.digichg('odtttl',0)
#s.wait(-2*tau)

s.wait(tof)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
kinetics = gen.bstr('Kinetics',report)
print 'kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms)

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')