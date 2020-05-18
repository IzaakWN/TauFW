#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
import os, sys, re, glob, json
from datetime import datetime
import importlib
from collections import OrderedDict
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.PicoProducer.tools.file import ensuredir, ensurefile
from TauFW.PicoProducer.tools.utils import execute, chunkify, repkey
from TauFW.PicoProducer.tools.log import Logger, color, bold, header
from TauFW.PicoProducer.batch.BatchSystem import getbatch
from TauFW.PicoProducer.storage.Sample import Sample
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile
CONFIG = GLOB.getconfig(verb=0)
LOG    = Logger()



###############
#   INSTALL   #
###############

def main_install(args):
  """Install producer."""
  # TODO:
  #  - guess location (lxplus/PSI/...)
  #  - set defaults of config file
  #  - outside CMSSW: create symlinks for standalone
  print ">>> main_install", args
  verbosity = args.verbosity
  


###########
#   SET   #
###########

def main_set(args):
  """Set variables in the config file."""
  print ">>> main_set", args
  variable  = args.variable
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
  print ">>> Setting variable '%s' to '%s' config"%(variable,value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  CONFIG[variable] = value
  CONFIG.write()
  


############
#   LINK   #
############

def main_link(args):
  """Link channels or eras in the config file."""
  print ">>> main_link", args
  variable  = args.subcommand
  varkey    = variable+'s'
  key       = args.key
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
  print ">>> Linking %s '%s' to '%s' in config"%(variable,key,value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  if '_' in value:
    LOG.throw(IOError,"Value given for %s (%s) cannot contain '_'!"%(variable,value))
  if varkey not in CONFIG:
    CONFIG[varkey] = { }
  assert isinstance(CONFIG[varkey],dict), "%s in %s has to be a dictionary"%(varkey,cfgname)
  CONFIG[varkey][key] = value
  CONFIG.write()
  


###########
#   RUN   #
###########

def main_run(args):
  """Run given module locally."""
  # TODO:
  #  - get module for given channel
  #  - run module with post-processor
  print ">>> main_run", args
  verbosity = args.verbosity
  


####################
#   PREPARE JOBS   #
####################

def preparejobs(args):
  """Help function to iterate over samples per given channel and era and prepare job config and list."""
  print ">>> preparejobs", args
  
  resubmit     = args.subcommand=='resubmit'
  eras         = args.eras
  channels     = args.channels
  tag          = args.tag
  dtypes       = args.dtypes
  filters      = args.samples
  vetoes       = args.vetoes
  checkdas     = args.checkdas
  checkqueue   = args.checkqueue
  nfilesperjob = args.nfilesperjob
  split_nfpj   = args.split_nfpj
  verbosity    = args.verbosity
  
  # LOOP over ERAS
  for era in eras:
    moddict = { } # save time by loading samples and get their files only once
    
    # CHANNEL over CHANNELS
    for channel in channels:
      print header("%s, %s"%(era,channel))
      
      # GET SAMPLES
      samples      = [ ]
      sampledict   = { }
      jobdirformat = CONFIG.jobdir # for job config & log files
      outdirformat = CONFIG.picodir if 'skim' in channel else CONFIG.outdir # for job output
      if resubmit:
        # TODO: allow user to resubmit given config file
        jobcfgs  = repkey(os.path.join(jobdirformat,"config/jobconfig_%s%s_try[0-9]*.json"),
                          ERA=era,SAMPLE='*',CHANNEL=channel,TAG=tag)
        if verbosity>=2:
          print ">>> %-12s = %s"%('cwd',os.getcwd())
          print ">>> %-12s = %s"%('jobcfgs',jobcfgs)
        samples = getsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      else:
        assert era in CONFIG.eras, "Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras)
        samplefile = ensurefile("samples",repkey(CONFIG.eras[era],CHANNEL=channel,TAG=tag))
        sampmodule = samplefile.replace('.py','').replace('/','.')
        if sampmodule not in moddict:
          moddict[sampmodule] = importlib.import_module(sampmodule) # save time by loading once
        if not hasattr(moddict[sampmodule],'samples'):
          LOG.throw(IOError,"Module '%s' must have a list of Sample objects called 'samples'!"%(sampmodule))
        samplelist = moddict[sampmodule].samples
        for sample in samplelist:
          if filters and not sample.match(filters,verbosity): continue
          if vetoes and sample.match(vetoes,verbosity): continue
          if sample.dtype not in dtypes: continue
          if sample.name in sampledict:
            LOG.throw(IOError,"Sample short names should be unique. Found two samples '%s'!\n\t%s\n\t%s"%(
                          sample.name,','.join(sampledict[sample.name].paths),','.join(sample.paths)))
          if 'skim' in channel and len(sample.paths)>=2:
            for subsample in sample.split():
              samples.append(subsample) # keep correspondence sample to one sample in DAS
          else:
            samples.append(sample)
          sampledict[sample.name] = sample
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(s.name for s in samples)
      
      # CHANNEL -> MODULE
      assert channel in CONFIG.channels, "Channel '%s' not found in the configuration file. Available: %s"%(channel,CONFIG.channels)
      module  = CONFIG.channels[channel]
      modpath = os.path.join("python/modules",module)
      #if not os.path.isfile(modpath):
      #  LOG.throw(IOError,"Module '%s' for channel '%s' does not exist: '%s'"%(module,channel,modpath))
      if verbosity>=1:
        print '-'*80
        print ">>> %-12s = %s"%('channel',channel)
        print ">>> %-12s = %s"%('module',module)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %s"%('dtypes',dtypes)
        print '-'*80
      
      # PROCESSOR
      if 'skim' in channel:
        processor = "skimjob.py"
      else:
        processor = "test.py"
      procpath  = os.path.join("python/processors",processor)
      if not os.path.isfile(procpath):
        LOG.throw(IOError,"Processor '%s' does not exist in '%s'..."%(processor,procpath))
      processor = os.path.abspath(procpath)
      
      # SAMPLE over SAMPLES
      found = False
      for sample in samples:
        if sample.channels and channel not in sample.channels: continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # DIRECTORIES
        subtry        = sample.subtry+1 if resubmit else 1
        jobids        = sample.jobcfg.get('jobids',[ ])
        jobtag        = '_%s%s_try%d'%(channel,tag,subtry)
        jobname       = sample.name+jobtag.rstrip('_try1')
        nfilesperjob_ = sample.nfilesperjob if sample.nfilesperjob>0 else nfilesperjob
        if split_nfpj>1:
          nfilesperjob_ = min(1,nfilesperjob_/split_nfpj)
        outdir        = ensuredir(repkey(outdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                                      DAS=sample.paths[0].strip('/'),GROUP=sample.group))
        jobdir        = ensuredir(repkey(jobdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                                      DAS=sample.paths[0].strip('/'),GROUP=sample.group))
        cfgdir        = ensuredir(jobdir,"config")
        logdir        = ensuredir(jobdir,"log")
        cfgname       = "%s/jobconfig%s.json"%(cfgdir,jobtag)
        joblist       = '%s/jobarglist%s.txt'%(cfgdir,jobtag)
        if verbosity==1:
          print ">>> %-12s = %s"%('cfgname',cfgname)
          print ">>> %-12s = %s"%('joblist',joblist)
        elif verbosity>=2:
          print '-'*80
          print ">>> Preparing job %ssubmission for '%s'"%("re" if resubmit else "",sample.name)
          print ">>> %-12s = %s"%('module',module)
          print ">>> %-12s = %s"%('processor',processor)
          print ">>> %-12s = %s"%('jobname',jobname)
          print ">>> %-12s = %s"%('jobtag',jobtag)
          print ">>> %-12s = %s"%('outdir',outdir)
          print ">>> %-12s = %s"%('cfgdir',cfgdir)
          print ">>> %-12s = %s"%('logdir',logdir)
          print ">>> %-12s = %s"%('cfgname',cfgname)
          print ">>> %-12s = %s"%('joblist',joblist)
          print ">>> %-12s = %s"%('try',subtry)
          print ">>> %-12s = %s"%('jobids',jobids)
        
        # CHECK CONFIG
        if os.path.isfile(cfgname):
          # TODO: check for running jobs
          LOG.warning("Job configuration '%s' already exists! Beware of conflicting job output!"%(cfgname))
        
        # GET FILES
        nevents = 0
        if resubmit: # resubmission
          infiles, chunkdict = checkjobs(sample,outdir=outdir,channel=channel,tag=tag,jobs=checkqueue,das=checkdas,verb=verbosity)
          nevents = sample.jobcfg['nevents'] # updated in checkjobs
        else: # first-time submission
          infiles   = sample.getfiles(verb=verbosity)
          if checkdas:
            nevents = sample.getnevents()
          chunkdict = { }
        if args.testrun:
          infiles = infiles[:2]
        if verbosity==1:
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
        elif verbosity>=2:
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
          print ">>> %-12s = [ "%('infiles')
          for file in infiles:
            print ">>>   "+file
          print ">>> ]"
          print ">>> %-12s = %s"%('nevents',nevents)
        
        # CHUNKS
        infiles.sort() # to have consistent order with resubmission
        chunks    = [ ] # chunk indices
        fchunks   = chunkify(infiles,nfilesperjob_) # file chunks
        nfiles    = len(infiles)
        nchunks   = len(fchunks)
        if verbosity>=1:
          print ">>> %-12s = %s"%('nchunks',nchunks)
        if verbosity>=2:
          print '-'*80
        
        # WRITE JOB LIST with arguments per job
        if args.verbosity>=1:
          print ">>> Creating job list %s..."%(joblist)
        with open(joblist,'w') as listfile:
          ichunk = 0
          for fchunk in fchunks:
            while ichunk in chunkdict:
              ichunk += 1 # allows for different nfilesperjob on resubmission
              continue
            jobfiles = ' '.join(fchunk) # list of input files
            filetag  = "%s_%d"%(tag,ichunk)
            if 'skim' in channel:
              jobcmd   = "%s --copydir %s -t %s --jec-sys -i %s"%(processor,outdir,filetag,jobfiles)
            else:
              jobcmd   = "%s -o %s -t %s -i %s"%(processor,outdir,filetag,jobfiles)
            if args.verbosity>=1:
              print jobcmd
            listfile.write(jobcmd+'\n')
            chunkdict[ichunk] = fchunk
            chunks.append(ichunk)
        
        # JSON CONFIG
        jobcfg = OrderedDict([
          ('time',str(datetime.now())),
          ('group',sample.group), ('paths',sample.paths), ('name',sample.name), ('nevents',nevents),
          ('channel',channel),    ('module',module),
          ('jobname',jobname),    ('jobtag',jobtag),      ('tag',tag),
          ('try',subtry),         ('jobids',jobids),
          ('outdir',outdir),      ('jobdir',jobdir),      ('cfgdir',cfgdir),    ('logdir',logdir),
          ('cfgname',cfgname),    ('joblist',joblist),
          ('nfiles',nfiles),      ('files',infiles),      ('nfilesperjob',nfilesperjob_), #('nchunks',nchunks),
          ('nchunks',nchunks),    ('chunks',chunks),      ('chunkdict',chunkdict),
        ])
        
        # YIELD
        yield jobcfg
        if args.testrun: break # only run one sample
      
      if not found:
        print ">>> Did not find any samples."
        if verbosity>=1:
          print ">>> %-8s = %s"%('filters',filters)
          print ">>> %-8s = %s"%('vetoes',vetoes)
    


############
#   HELP   #
############

def getsamples(jobcfgnames,filter=[ ],veto=[ ],dtype=[ ],verb=0):
  """Help function to get samples from output directory.
  Return list of Sample objects."""
  filters = filter if isinstance(filter,list) else [filter]
  vetoes  = veto   if isinstance(veto,list)   else [veto]
  dtypes  = dtype  if isinstance(dtype,list)  else [dtype]
  jobcfgs = glob.glob(jobcfgnames)
  samples = [ ]
  if verb>=2:
    print ">>> getsamples: Found job config:"
  for cfgname in sorted(jobcfgs):
    if verb>=2:
      print ">>>   %s"%(cfgname)
    sample = Sample.loadJSON(cfgname)
    if filters and not sample.match(filters,verb): continue
    if vetoes and sample.match(vetoes,verb): continue
    if sample.dtype not in dtypes: continue
    for i, osample in enumerate(samples):
      if sample.name!=osample.name: continue
      if sample.paths!=osample.paths: continue
      if sample.channels[0] not in osample.channels: continue
      if sample.subtry>osample.subtry: # ensure last job (re)submission
        samples[samples.index(osample)] = sample # replace
      break
    else: # if no break
      samples.append(sample)
  return samples
  


##################
#   CHECK JOBS   #
##################

def checkjobs(sample,**kwargs):
  """Help function to check jobs status: success, pending, failed or missing.
  Return list of files to be resubmitted, and a dictionary between chunk index and input files."""
  outdir      = kwargs.get('outdir',  None)
  channel     = kwargs.get('channel', None)
  tag         = kwargs.get('tag',     None)
  jobs        = kwargs.get('jobs',    True)
  checkdas    = kwargs.get('das',     True)
  verbosity   = kwargs.get('verb',       0)
  oldjobcfg   = sample.jobcfg
  oldcfgname  = oldjobcfg['config']
  chunkdict   = oldjobcfg['chunkdict'] # filenames
  jobids      = oldjobcfg['jobids']
  if outdir==None:
    outdir    = oldjobcfg['outdir']
  if channel==None:
    channel   = oldjobcfg['channel']
  if tag==None:
    tag       = oldjobcfg['tag']
  noldchunks  = len(chunkdict) # = number of jobs
  goodchunks  = [ ] # good job output
  pendchunks  = [ ] # pending or running jobs
  badchunks   = [ ] # corrupted job output
  misschunks  = [ ] # missing job output
  
  # NUMBER OF EVENTS
  nprocevents = 0   # total number of processed events
  ndasevents  = oldjobcfg['nevents'] # total number of available events
  if checkdas and oldjobcfg['nevents']==0:
    ndasevents = sample.getnevents()
    oldjobcfg['nevents'] = ndasevents
  
  # CHECK PENDING JOBS
  if jobs:
    batch       = getbatch(CONFIG,verb=verbosity)
    pendjobs    = batch.jobs(jobids,verb=verbosity-1)
    flagexp     = re.compile(r"-t \w*(\d+)")
    for job in pendjobs:
      if verbosity>=3:
        print ">>> Found job %s, jobid=%s, taskid=%s, status=%s, args=%s"%(job,job.jobid,job.taskid,job.getstatus(),job.args)
      if job.getstatus() in ['q','r']:
        jobarg = str(job.args)
        matches = flagexp.findall(jobarg)
        if not matches: continue
        ichunk = int(matches[0])
        assert ichunk in chunkdict, ("Found an impossible chunk %d for job %s.%s! "%(ichunk,job.jobid,job.taskid)+
                                     "Possible overcounting!")
        pendchunks.append(ichunk)
  
  # CHECK OUTPUT FILES
  # TODO: check file with Storage object
  fpattern = "%s/*_%s%s_[0-9]*.root"%(outdir,channel,tag)
  chunkexp = re.compile(r".*%s%s_(\d+)\.root"%(channel,tag))
  if verbosity>=2:
    print ">>> %-12s = %s"%('ndasevents',ndasevents)
    print ">>> %-12s = %r"%('fpattern',fpattern)
    print ">>> %-12s = %r"%('chunkexp',chunkexp.pattern)
  for fname in glob.glob(fpattern):
    if verbosity>=2:
      print ">>>   Checking job output '%s'..."%(fname)
    
    # GET CHUNK
    match = chunkexp.search(fname)
    if match:
      ichunk = int(match.group(1))
      assert ichunk in chunkdict, ("Found an impossible chunk %d for file %s!"%(ichunk,fname)+
                                   "Possible overcounting or conflicting job output file format!")
      if ichunk in pendchunks: continue
    else:
      LOG.warning("Did not recognize output file '%s'!"%(fname))
      continue
    
    # CHECK for CORRUPTION
    file = TFile.Open(fname,'READ')
    if file and not file.IsZombie():
      if file.GetListOfKeys().Contains('tree') and file.GetListOfKeys().Contains('cutflow'):
        nprocevents += file.Get('cutflow').GetBinContent(1)
        goodchunks.append(ichunk)
        continue
      if file.GetListOfKeys().Contains('Events'):
        nprocevents += file.Get('Events').GetEntries()
        goodchunks.append(ichunk)
        continue
    badchunks.append(ichunk)
    # TODO: remove file from outdir?
  if verbosity>=2: # TODO: set to 2
    print ">>> %-12s = %s"%('nprocevents',nprocevents)
  
  # GET FILES for RESUBMISSION + sanity checks
  resubfiles = [ ]
  for ichunk in chunkdict.keys():
    count = goodchunks.count(ichunk)+pendchunks.count(ichunk)+badchunks.count(ichunk)
    assert count in [0,1], ("Found %d times chunk '%d' (good=%d, pending=%d, bad=%d). "%(
                            ichunk,count,goodchunks.count(ichunk),pendchunks.count(ichunk),badchunks.count(ichunk))+
                            "Possible overcounting or conflicting job output file format!")
    if count==0: # missing chunk
      misschunks.append(ichunk)
    elif ichunk not in badchunks: # good or pending chunk
      continue
    fchunk = chunkdict[ichunk]
    for fname in fchunk:
      assert fname not in resubfiles, ("Found file for chunk '%d' more than once: %s "%(ichunk,fname)+
                                       "Possible overcounting or conflicting job output file format!")
    resubfiles.extend(chunkdict[ichunk]) # add files for resubmission if missing of bad chunk
    chunkdict.pop(ichunk) # only save good chunks
  goodchunks.sort()
  pendchunks.sort()
  badchunks.sort()
  misschunks.sort()
  
  # PRINT
  def printJobs(jobden,label,text,col,show=False):
   if jobden:
     ratio = color("%4d/%d"%(len(jobden),noldchunks),col,bold=False)
     label = color(label,col,bold=True)
     jlist = (": "+', '.join(str(j) for j in jobden)) if show else ""
     print ">>> %s %s - %s%s"%(ratio,label,text,jlist)
   #else:
   #  print ">>> %2d/%d %s - %s"%(len(jobden),len(jobs),label,text)
  rtext = ""
  if ndasevents>0:
    ratio = 100.0*nprocevents/ndasevents
    rcol  = 'green' if ratio>90. else 'yellow' if ratio>80. else 'red'
    rtext = ": "+color("%d/%d (%d%%)"%(nprocevents,ndasevents,ratio),rcol,bold=True)
  printJobs(goodchunks,'SUCCES', "Chunks with output in outdir"+rtext,'green')
  printJobs(pendchunks,'PEND',"Chunks with pending or running jobs",'white',True)
  printJobs(badchunks, 'FAIL', "Chunks with corrupted output in outdir",'red',True)
  printJobs(misschunks,'MISS',"Chunks with no output in outdir",'red',True)
  
  return resubfiles, chunkdict
  


##################
#   (RE)SUBMIT   #
##################

def main_submit(args):
  """Submit or resubmit jobs to the batch system."""
  print ">>> main_submit", args
  
  verbosity = args.verbosity
  force     = args.force #or True
  dryrun    = args.dryrun #or True
  batch     = getbatch(CONFIG,verb=verbosity+1)
  
  for jobcfg in preparejobs(args):
    cfgname = jobcfg['cfgname']
    jobdir  = jobcfg['jobdir']
    outdir  = jobcfg['outdir']
    joblist = jobcfg['joblist']
    jobname = jobcfg['jobname']
    nchunks = jobcfg['nchunks']
    if nchunks<=0:
      print ">>>   Nothing to resubmit!"
      continue
    if batch.system=='HTCondor':
      script  = "python/batch/submit_HTCondor.sub"
      appcmds = ["initialdir=%s"%(jobdir),
                 "mylogfile='log/%s.$(ClusterId).$(ProcId).log'"%(jobname)]
      queue   = "arg from %s"%(joblist)
      option  = "" #-dry-run dryrun.log"
      jobid   = batch.submit(script,name=jobname,opt=option,app=appcmds,queue=queue,dry=dryrun) # TODO: get jobid
    else:
      LOG.throw(NotImplementedError,"Submission for batch system '%s' has not been implemented (yet)..."%(batch.system))
    
    ## SUBMIT
    #if args.force:
    #  jobid = batch.submit(*jargs,**jkwargs)
    #else:
    #  while True:
    #    submit = raw_input(">>> Do you also want to submit %d jobs to the batch system? [y/n] "%(nchunks))
    #    if any(s in submit.lower() for s in ['quit','exit']):
    #      exit(0)
    #    elif 'force' in submit.lower():
    #      submit = 'y'
    #      args.force = True
    #    if 'y' in submit.lower():
    #      jobid = batch.submit(*jargs,**jkwargs)
    #      break
    #    elif 'n' in submit.lower():
    #      print "Not submitting."
    #      break
    #    else:
    #      print "'%s' is not a valid answer, please choose y/n."%submit
    #print
    
    # WRITE JOBCONFIG
    jobcfg['jobids'].append(jobid)
    if verbosity>=1:
      print ">>> Creating config file '%s'..."%(cfgname)
    with open(cfgname,'w') as file:
      json.dump(jobcfg,file,indent=2)
  


#####################
#   STATUS & HADD   #
#####################

def main_status(args):
  """Check status of jobs (succesful/pending/failed/missing), or hadd job output."""
  print ">>> main_status", args
  
  # SETTING
  eras           = args.eras
  channels       = args.channels
  tag            = args.tag
  checkdas       = args.checkdas
  checkqueue     = args.checkqueue
  dtypes         = args.dtypes
  filters        = args.samples
  vetoes         = args.vetoes
  force          = args.force
  hadd           = args.subcommand=='hadd'
  cleanup        = args.cleanup if hadd else False
  dryrun         = args.dryrun
  verbosity      = args.verbosity
  outdirformat   = CONFIG.outdir
  jobdirformat   = CONFIG.jobdir
  storedirformat = CONFIG.picodir
  
  # LOOP over ERAS
  for era in eras:
    
    # CHANNEL over CHANNELS
    for channel in channels:
      print header("%s, %s"%(era,channel))
      
      # GET SAMPLES
      jobcfgs = repkey(os.path.join(jobdirformat,"config/jobconfig_$CHANNEL$TAG_try[0-9]*.json"),
                        ERA=era,SAMPLE='*',GROUP='*',CHANNEL=channel,TAG=tag)
      if verbosity>=2:
        print ">>> %-8s = %s"%('cwd',os.getcwd())
        print ">>> %-8s = %s"%('jobcfgs',jobcfgs)
      samples = getsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(s.name for s in samples)
      if hadd and 'skim' in channel:
        LOG.warning("Hadding into one file not available for skimming...")
        continue
      
      # SAMPLE over SAMPLES
      found = False
      for sample in samples:
        if sample.channels and channel not in sample.channels: continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # HADD
        if hadd:
          jobdir   = sample.jobcfg['jobdir']
          outdir   = sample.jobcfg['outdir']
          storedir = ensuredir(repkey(storedirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                                     DAS=sample.paths[0].strip('/'),GROUP=sample.group))
          outfile  = os.path.join(storedir,'%s_%s%s.root'%(sample.name,channel,tag))
          infiles  = os.path.join(outdir,'*_%s%s_[0-9]*.root'%(channel,tag))
          cfgfiles = os.path.join(sample.jobcfg['cfgdir'],'job*_%s%s_try[0-9]*.*'%(channel,tag))
          logfiles = os.path.join(sample.jobcfg['logdir'],'*_%s%s_try[0-9]*.*.*.txt'%(channel,tag))
          if verbosity>=1:
            print ">>> Hadd'ing job output for '%s'"%(sample.name)
            print ">>> %-8s = %s"%('jobdir',jobdir)
            print ">>> %-8s = %s"%('outdir',outdir)
            print ">>> %-8s = %s"%('storedir',storedir)
            print ">>> %-8s = %s"%('infiles',infiles)
            print ">>> %-8s = %s"%('outfile',outfile)
          resubfiles, chunkdict = checkjobs(sample,outdir=outdir,channel=channel,tag=tag,das=checkdas,jobs=checkqueue,verb=verbosity)
          if len(resubfiles)>0 and not force:
            LOG.warning("Cannot hadd job output because %d chunks need to be resubmitted..."%(len(resubfiles))+
                        "Please use -f or --force to hadd anyway.")
            continue
          haddcmd = 'hadd -f %s %s'%(outfile,infiles)
          haddout = execute(haddcmd,dry=dryrun,verb=max(1,verbosity))
          
          # CLEAN UP
          if cleanup:
            rmfiles = ""
            for files in [infiles,cfgfiles,logfiles]:
              if len(glob.glob(rmfiles))>0:
                rmfiles += ' '+files
            if rmfiles:
              rmcmd = "rm %s"%(rmfiles)
              rmout = execute(rmcmd,dry=dryrun,verb=verbosity)
          print
        
        # ONLY CHECK STATUS
        else:
          outdir = ensuredir(repkey(outdirformat,ERA=era,SAMPLE=sample.name,CHANNEL=channel,TAG=tag))
          if verbosity>=1:
            print ">>> Checking job status for '%s'"%(sample.name) 
            print ">>> %-6s = %s"%('outdir',outdir)
          checkjobs(sample,outdir=outdir,channel=channel,tag=tag,das=checkdas,jobs=checkqueue,verb=verbosity)
      
      if not found:
        print ">>> Did not find any samples."
        if verbosity>=1:
          print ">>> %-8s = %s"%('filters',filters)
          print ">>> %-8s = %s"%('vetoes',vetoes)
          print ">>> %-8s = %s"%('dtypes',dtypes)
  


############
#   MAIN   #
############

if __name__ == "__main__":
  
  # COMMON
  parser = ArgumentParser(prog='run.py')
  parser_cmn = ArgumentParser(add_help=False)
  parser_cmn.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                                help="set verbosity" )
  parser_job = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_lnk = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_job.add_argument('-f','--force',       dest='force', action='store_true',
                                                help='force overwrite')
  parser_job.add_argument('-d','--dry',         dest='dryrun', action='store_true',
                                                help='dry run for debugging purposes')
  parser_job.add_argument('--dtype',            dest='dtypes', choices=GLOB._dtypes, default=GLOB._dtypes, nargs='+',
                                                help='data type')
  parser_job.add_argument('-t','--tag',         dest='tag', default="",
                                                help='tag for output')
  parser_job.add_argument('-c','--channel',     dest='channels', choices=CONFIG.channels.keys(), default=[ ], nargs='+',
                                                help='channel')
  parser_job.add_argument('-y','-e','--era',    dest='eras', choices=CONFIG.eras.keys(), default=[ ], nargs='+',
                                                help='year or era')
  parser_job.add_argument('-s', '--sample',     dest='samples', type=str, nargs='+', default=[ ], action='store',
                          metavar='PATTERN',    help="filter these samples; glob patterns (wildcards * and ?) are allowed." )
  parser_job.add_argument('-x', '--veto',       dest='vetoes', nargs='+', default=[ ], action='store',
                          metavar='PATTERN',    help="exclude/veto this sample" )
  parser_job.add_argument('-D','--das',         dest='checkdas', default=False, action='store_true',
                                                help="check DAS for number of events" )
  parser_job.add_argument('--no-jobs',          dest='checkqueue', default=True, action='store_false',
                                                help="do not check job status (runs faster)" ) # speed up if batch is slow
  parser_chk = ArgumentParser(add_help=False,parents=[parser_job])
  #parser_job.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
  #                                              help='extra options for the batch system')
  parser_job.add_argument('--filesperjob',      dest='nfilesperjob', type=int, default=CONFIG.nfilesperjob,
                                                help='number of files per job')
  parser_job.add_argument('--split',            dest='split_nfpj',type=int, nargs='?', const=2, default=1, action='store',
                          metavar='N',          help="divide default number of files per job" )
  
  # SUBCOMMANDS
  subparsers = parser.add_subparsers(title="sub-commands",dest='subcommand',help="sub-command help")
  parser_set = subparsers.add_parser('set',      parents=[parser_cmn], help='set given variable in the configuration file')
  parser_ins = subparsers.add_parser('install',  parents=[parser_cmn], help='install')
  parser_chl = subparsers.add_parser('channel',  parents=[parser_lnk], help='link a channel to a module in the configuration file')
  parser_era = subparsers.add_parser('era',      parents=[parser_lnk], help='link an era to a sample list in the configuration file')
  parser_run = subparsers.add_parser('run',      parents=[parser_job], help='run local post processor')
  parser_sub = subparsers.add_parser('submit',   parents=[parser_job], help='submit post-processing jobs')
  parser_res = subparsers.add_parser('resubmit', parents=[parser_job], help='resubmit failed post-processing jobs')
  parser_sts = subparsers.add_parser('status',   parents=[parser_chk], help='status of post-processing jobs')
  parser_hdd = subparsers.add_parser('hadd',     parents=[parser_chk], help='hadd post-processing job output')
  parser_set.add_argument('variable',           help='variable to change in the config file')
  parser_set.add_argument('value',              help='value for given value')
  parser_chl.add_argument('key',                metavar='channel', help='channel key name')
  parser_chl.add_argument('value',              metavar='module',  help='module linked to by given channel')
  parser_era.add_argument('key',                metavar='era',     help='era key name')
  parser_era.add_argument('value',              metavar='samples', help='samplelist linked to by given era')
  parser_ins.add_argument('type',               choices=['standalone','cmmsw'], #default=None,
                                                help='type of installation: standalone or compiled in CMSSW')
  parser_hdd.add_argument('--keep',             dest='cleanup', default=True, action='store_false',
                                                help="do not remove job output after hadd'ing" )
  
  # ABBREVIATIONS
  args = sys.argv[1:]
  if args:
    subcmds = [ 
      'install','set','channel','era',
      'run','submit','resubmit','status','hadd',
    ]
    for subcmd in subcmds:
      if args[0] in subcmd[:len(args[0])]: # match abbreviation
        args[0] = subcmd
        break
  args = parser.parse_args(args)
  args.testrun = True
  if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_':
    args.tag = '_'+args.tag
  
  # SUBCOMMAND MAINs
  os.chdir(CONFIG.basedir)
  if args.subcommand=='install':
    main_install(args)
  elif args.subcommand=='set':
    main_set(args)
  elif args.subcommand in ['channel','era']:
    main_link(args)
  elif args.subcommand=='run':
    main_set(args)
  elif args.subcommand in ['submit','resubmit']:
    main_submit(args)
  elif args.subcommand in ['status','hadd']:
    main_status(args)
  else:
    print ">>> subcommand '%s' not implemented!"%(args.subcommand)
  
  print ">>> Done!"
  
