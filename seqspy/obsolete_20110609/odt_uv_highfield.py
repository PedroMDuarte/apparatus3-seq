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
stepsize = float(report['SEQ']['stepsize'])
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

ss = float(report['SEQ']['analogstepsize'])

# Cool and Compress MOT
# ENDCNC is defined as the time up to release from the MOT
motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()

# Load UVMOT from CNCMOT
uvfppiezo, uvpow, motpow, repdet, trapdet, reppow, trappow, bfield, ENDUVMOT = uvcooling.uvcoolRamps(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC)

# Set imaging values
camera = 'ANDOR'
motpow, repdet, trapdet, reppow, trappow, maxDT = cnc.imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow, camera)

#Switch bfield to FESHBACH
switchdt  = float(report['FESHBACH']['switchdt'])
offdelay  = float(report['FESHBACH']['offdelay'])
quickdelay  = float(report['FESHBACH']['quickdelay'])
switchdelay  = float(report['FESHBACH']['switchdelay'])
bias  = float(report['FESHBACH']['bias'])
biasrampdt  = float(report['FESHBACH']['rampdt'])
bfield.linear(0.0,0.0)
bfield.appendhold(offdelay)
bfield.appendhold(2*switchdt)
bfield.appendhold(quickdelay)
bfield.appendhold(switchdelay)
bfield.linear(cnv('bfield',bias),biasrampdt)
#bfield.Exponential( 0.0, bias, biasrampdt, 30.0)
	
#Add waveforms to sequence
s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow])
	
#wait normally rounds down using floor, here the duration is changed before so that
#the wait is rounded up
ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
#insert QUICK pulse  for fast ramping of the field gradient
s.wait(-10.0)
quickval = 1 if gen.bstr('CNC',report) == True else 0
s.digichg('quick',quickval)	
s.wait(10.0)

#insert UV pulse
uvtime  = float(report['UV']['uvtime'])
s.wait(ENDCNC)
s.wait(uvtime)
s.digichg('uvaom1',1)
s.wait(-uvtime - ENDCNC)
	
#Go to MOT release time
s.wait(ENDUVMOT)
s.digichg('quick',0)

#Insert ODT overlap with UVMOT
overlapdt = float(report['ODT']['overlapdt'])
s.wait(-overlapdt)
s.digichg('odtttl',1)
s.digichg('odt7595',1)
s.wait(overlapdt)

#Leave UVMOT on for state transfer
fstatedt  = float(report['ODT']['fstatedt'])
s.wait(fstatedt)
s.digichg('uvaom1',0)
s.wait(-fstatedt) 

#RELEASE FROM MOT
waitshutter=5.0
s.wait(waitshutter)
s.digichg('uvshutter',0)
s.wait(-waitshutter)

s.digichg('motswitch',0) 
s.digichg('motshutter',1)


# Go a little in the future to switch field from MOT to FESHBACH
# and further in the future to switch QUICK back to low
s.wait(offdelay)
s.digichg('field',1)
s.wait(switchdt)
s.digichg('feshbach',1)
s.wait(switchdt)
s.digichg('field',1)
s.wait(quickdelay)
do_quick=0
s.digichg('hfquick',do_quick)
s.digichg('quick',do_quick)
#Can't leave quick ON for more than quickmax
quickmax=100.
s.wait(quickmax)
s.digichg('hfquick',0)
s.digichg('quick',0)
s.wait(-quickmax)
s.wait(switchdelay+biasrampdt)
s.digichg('quick',0)
s.wait(-biasrampdt-switchdelay-quickdelay-2*switchdt-offdelay)

s.wait(tof)

#~ braggtime=0.15
#~ waittime=1.0
#~ s.wait(-braggtime-waittime)
#~ s.digichg('bragg',1)
#~ s.wait(braggtime)
#~ s.digichg('bragg',0)
#~ s.wait(waittime)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
trap_on_picture = 1
kinetics = gen.bstr('Kinetics',report)
print 'kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)


#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')