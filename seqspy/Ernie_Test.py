"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
   Test for double Servo
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

print "\n----- odt_uv_hf_evap_repump_test.py -----\n"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm_test, gen, cnc, odt_test, andor, highfield_repump_test
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
s.digichg('odt7595',0)

#Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_repump_test.go_to_highfield(s)

# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
image= float(report['EVAP']['image'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at least ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
    print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,free)
    exit(1)
s.wait(free)
odtpow, ENDEVAP = odt_test.odt_evap(image)
odtpow_nonservo, ENDEVAP = odt_test.odt_evap(image,0)
evap_ss = float(report['EVAP']['evapss'])
s.analogwfm_add(evap_ss,[odtpow,odtpow_nonservo])
# ENDEVAP should be equal to image
s.wait(image)


#RELEASE FROM IR TRAP
s.digichg('odtttl',0)
odttof = float(report['ODT']['odttof'])
s.wait(odttof)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
trap_on_picture = 1
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
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
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)
