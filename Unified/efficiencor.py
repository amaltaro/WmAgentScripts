import os
import json
import time
from utils import sendEmail
import sys

## get the wf from many places

c=0   
while True:
    c+=1
    if len(sys.argv)>1 and c>int(sys.argv[1]): break

    ow = open('/afs/cern.ch/user/v/vlimant/public/ops/retrievers.json')
    whos = json.loads(ow.read())
    ow.close()
    print json.dumps( whos , indent=2)
    print "Can get stuff in"
    wfs = []
    for who in whos:
        try:
            rw = open('/afs/cern.ch/user/%s/%s/public/ops/retrieve.json'%(who[0],who))
            wfs.extend(json.loads(rw.read()))
            rw.close()
        except:
            print who,"is not ready"
        
    for (wf,lf) in wfs:
        print "#"*30
        print "Getting",wf.strip(),lf.strip()
        expose_all='/eos/project/c/cms-unified-logs/www/logmapping/%s/'% wf
        os.system('mkdir -p %s'% expose_all)

        agent,jobid = None, None
        if ":" in lf:
            agent,jobid = lf.split(":")
            if not 'vocms' in agent: 
                print "cannot do non cern agents"
                continue
            ## get the archive from the agent
            com = 'ssh %s %s/WmAgentScripts/Unified/exec_expose.sh %s %s %s %s %s %s'%(
                agent,
                '/afs/cern.ch/user/c/cmst2/Unified/',
                wf,
                jobid,
                0,
                '/afs/cern.ch/user/c/cmst2/Unified/',
                '/eos/project/c/cms-unified-logs/www/logmapping/',
                'ATask'
                )
            ## parse the condor logs for the tar.gz
            condor_dir ='/eos/project/c/cms-unified-logs/www/logmapping/condorlogs/%s/0/ATask/%s/%s_%s/Job_%s'%(wf,
                                                                                                                jobid[:3],
                                                                                                                agent.split('.')[0],
                                                                                                                jobid,
                                                                                                                jobid)
            if not os.path.isdir( condor_dir ):
                print "Ex: ",com
                os.system(com)

            outs = os.popen('find %s -name "*.out"'% ( condor_dir )).read()
            #print outs
            found_log = False
            for out in outs.split('\n'):
                if not out: continue
                fh = open(out)
                for line in fh.read().split('\n'):
                    if 'logArchive.tar.gz' in line:
                        fullpath = filter(lambda w : 'logArchive.tar.gz' in w, line.split())[0]
                        lf = fullpath.split('/')[-1]
                        found_log = True
                        print "found log name", lf,"in condor log",out.split('/')[-1]
                        break
                fh.close()
            if not found_log:
                print "Could not find trace of a log file for",lf
                continue
        else:
            continue

        ## then do the rest
        not_found = (lf and 'nothing found' in os.popen('python /afs/cern.ch/user/v/vlimant/public/ops/whatLog.py --workflow %s --log %s'%(wf,lf)).read())
        nothing_indexed = ('nothing found' in os.popen('python /afs/cern.ch/user/v/vlimant/public/ops/whatLog.py --workflow  %s'%wf).read())

        print ("log index NOT found" if not_found else "log index found"),"for",lf
        print ("log NOT indexed" if nothing_indexed else "log indexed"),"for",wf

        if not_found or nothing_indexed:
            print "Making the full query from eos to create the index of ",wf
            com = 'python /afs/cern.ch/user/v/vlimant/public/ops/createLogDB.py --workflow %s'% (wf)
            print "Ex :",com
            os.system(com) ## heavy

        ## list things     ## put the text somewhere useful
        mapf = '%s/mapping.txt'% expose_all
        if not os.path.isfile( mapf ) or not_found or nothing_indexed:
            com = 'python /afs/cern.ch/user/v/vlimant/public/ops/whatLog.py --workflow %s --where > %s'%( wf,
                                                                                                          mapf)
            print "Ex :",com
            os.system(com)
        else:
            print "mapping file already there"


        if lf:
            final_dest = '%s/%s'%( expose_all, lf)
            print "\t and specifically",lf
            if os.path.isfile( final_dest ):
                print final_dest,"already on the web"
                continue
            ## show that one
            com = 'python /afs/cern.ch/user/v/vlimant/public/ops/whatLog.py --workflow  %s --log %s > %s/%s.txt'%(wf, lf, expose_all, lf)
            print 'Ex:',com
            os.system(com)
            ## get it locally
            com = 'python /afs/cern.ch/user/v/vlimant/public/ops/whatLog.py --workflow  %s --log %s --get '%( wf, lf )
            print 'Ex:',com
            os.system(com)
            lfile = os.popen('find /tmp/vlimant/ -name "*%s"'% lf ).read().replace('\n','')
            print lfile,"is mean to be the local file"
            if lfile and os.path.isfile( lfile ):
                com = 'cp %s %s/.'%( lfile, expose_all)
                print 'Ex:',com
                os.system( com )
                if agent and jobid:
                    com = 'cp %s %s/%s_%s.tar.gz'%( lfile, expose_all, agent,jobid)
                    print 'Ex:',com
                    os.system( com )

                sendEmail("%s is ready"%lf,"Get the file at http://cms-unified.web.cern.ch/cms-unified/logmapping/%s"%(wf), destination= [whos[who]])
                print "Got the file",lf
            else:
                print "no file yet retreived"
                ##sendEmail("%s is ready"%lf,"Get the file at http://cms-unified.web.cern.ch/cms-unified/logmapping/%s"%(wf), destination= [whos[who]])
           
    print "waiting a bit"
    time.sleep(30)