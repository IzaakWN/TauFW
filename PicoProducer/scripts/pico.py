#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
import os, sys, re, glob, json
from datetime import datetime
from collections import OrderedDict
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.common.tools.file import ensuredir, ensurefile, ensureinit, getline
from TauFW.common.tools.utils import execute, chunkify, repkey
from TauFW.common.tools.log import Logger, color, bold
from TauFW.PicoProducer.analysis.utils import getmodule, ensuremodule
from TauFW.PicoProducer.batch.utils import getbatch, getcfgsamples
from TauFW.PicoProducer.storage.utils import getstorage, getsamples
from argparse import ArgumentParser
os.chdir(GLOB.basedir)
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
  if args.verbosity>=1:
    print ">>> main_install", args
  verbosity = args.verbosity
  


###########
#   LIST   #
###########

def main_list(args):
  """List contents of configuration for those lazy to do 'cat config/config.json'."""
  if args.verbosity>=1:
    print ">>> main_list", args
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  print ">>> Configuration %s:"%(cfgname)
  for variable, value in CONFIG.iteritems():
    variable = "'"+color(variable)+"'"
    if isinstance(value,dict):
      print ">>>  %s:"%(variable)
      for key, item in value.iteritems():
        if isinstance(item,basestring): item = str(item)
        print ">>>    %-12r -> %r"%(str(key),str(item))
    else:
      if isinstance(value,basestring): value = str(value)
      print ">>>  %-24s = %r"%(variable,value)
  


###########
#   GET   #
###########

def main_get(args):
  """Get information of given variable in configuration or samples."""
  if args.verbosity>=1:
    print ">>> main_get", args
  variable  = args.variable
  eras      = args.eras
  channels  = args.channels or [""]
  dtypes    = args.dtypes
  filters   = args.samples
  vetoes    = args.vetoes
  checkdas  = args.checkdas
  writedir  = args.write # write sample file list to text file
  tag       = args.tag
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
    print ">>> %-14s = %s"%('variable',variable)
    print ">>> %-14s = %s"%('eras',eras)
    print ">>> %-14s = %s"%('channels',channels)
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  # LIST SAMPLES
  if variable=='samples':
    if not eras:
      LOG.warning("Please specify an era to get a sample for.")
    for era in eras:
      for channel in channels:
        if channel:
          print ">>> Getting file list for era %r, channel %r"%(era,channel)
        else:
          print ">>> Getting file list for era %r"%(era)
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,verb=verbosity)
        if not samples:
          LOG.warning("No samples found for era %r."%(era))
        for sample in samples:
          print ">>> %s"%(bold(sample.name))
          for path in sample.paths:
            print ">>>   %s"%(path)
  
  # LIST SAMPLE FILES
  elif variable=='files':
    
    # LOOP over ERAS & CHANNELS
    if not eras:
      LOG.warning("Please specify an era to get a sample for.")
    for era in eras:
      for channel in channels:
        if channel:
          print ">>> Getting file list for era %r, channel %r"%(era,channel)
        else:
          print ">>> Getting file list for era %r"%(era)
        
        # VERBOSE
        if verbosity>=1:
          print ">>> %-12s = %r"%('channel',channel)
        
        # GET SAMPLES
        LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,verb=verbosity)
        
        # LOOP over SAMPLES
        for sample in samples:
          print ">>> %s"%(bold(sample.name))
          for path in sample.paths:
            print ">>> %s"%(bold(path))
            infiles = sample.getfiles(url=False,verb=verbosity+1)
            if checkdas:
              ndasevents = sample.getnevents(verb=verbosity+1)
              print ">>> %-12s = %s"%('ndasevents',ndasevents)
            print ">>> %-12s = %r"%('url',sample.url)
            print ">>> %-12s = %r"%('postfix',sample.postfix)
            print ">>> %-12s = %s"%('nfiles',len(infiles))
            print ">>> %-12s = [ "%('infiles')
            for file in infiles:
              print ">>>   %r"%file
            print ">>> ]"
            if writedir:
              flistname = repkey(writedir,ERA=era,GROUP=sample.group,SAMPLE=sample.name,TAG=tag)
              print ">>> Write list to %r..."%(flistname)
              ensuredir(os.path.dirname(flistname))
              with open(flistname,'w+') as flist:
                for infile in infiles:
                  flist.write(infile+'\n')
  
  # CONFIGURATION
  else:
    if variable in CONFIG:
      print ">>> Configuration of %r: %s"%(variable,color(CONFIG[variable]))
    else:
      print ">>> Did not find %r in the configuration"%(variable)
  


###########
#   SET   #
###########

def main_set(args):
  """Set variables in the config file."""
  if args.verbosity>=1:
    print ">>> main_set", args
  variable  = args.variable
  key       = args.key # 'channel' or 'era'
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if key: # redirect 'channel' and 'era' keys to main_link
    args.subcommand = variable
    return main_link(args)
  elif variable in ['channel','era']:
      LOG.throw(IOError,"Variable '%s' is reserved for dictionaries!"%(variable))
  if verbosity>=1:
    print '-'*80
  print ">>> Setting variable '%s' to '%s' config"%(variable,value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  if variable=='all':
    if 'default' in value:
      GLOB.setdefaultconfig(verb=verb)
    else:
      LOG.warning("Did not recognize value '%s'. Did you mean 'default'?"%(value))
  else:
    CONFIG[variable] = value
    CONFIG.write()
  


############
#   LINK   #
############

def main_link(args):
  """Link channels or eras in the config file."""
  if args.verbosity>=1:
    print ">>> main_link", args
  variable  = args.subcommand
  varkey    = variable+'s'
  key       = args.key
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
  print ">>> Linking %s '%s' to '%s' in the configuration..."%(variable,key,value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('key',key)
    print ">>> %-14s = %s"%('value',value)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  # SANITY CHECKS
  if varkey not in CONFIG:
    CONFIG[varkey] = { }
  LOG.insist(isinstance(CONFIG[varkey],dict),"%s in %s has to be a dictionary"%(varkey,cfgname))
  oldval = value
  for char in '/\,:;!?\'"':
    if char in key:
      LOG.throw(IOError,"Given key '%s', but keys cannot contain any of these characters: %s"%(key,char))
  if varkey=='channels':
    if 'skim' in key.lower(): #or 'test' in key:
      parts  = value.split(' ')
      script = os.path.basename(parts[0]) # separate script from options
      ensurefile("python/processors",script)
      value  = ' '.join([script]+parts[1:])
    else:
      if 'python/analysis/' in value: # useful for tab completion
        value = value.split('python/analysis/')[-1].replace('/','.')
      value = value.rstrip('.py')
      path  = os.path.join('python/analysis/','/'.join(value.split('.')[:-1]))
      print path
      ensureinit(path,by="pico.py")
      ensuremodule(value)
  elif varkey=='eras':
    if 'samples/' in value: # useful for tab completion
      value = ''.join(value.split('samples/')[1:])
    path = os.path.join("samples",repkey(value,ERA='*',CHANNEL='*',TAG='*'))
    LOG.insist(glob.glob(path),"Did not find any sample lists '%s'"%(path))
    ensureinit(os.path.dirname(path),by="pico.py")
  if value!=oldval:
    print ">>> Converted '%s' to '%s'"%(oldval,value)
  
  CONFIG[varkey][key] = value
  CONFIG.write()
  


##############
#   REMOVE   #
##############

def main_rm(args):
  """Remove variable from the config file."""
  if args.verbosity>=1:
    print ">>> main_rm", args
  variable  = args.variable
  key       = args.key # 'channel' or 'era'
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
  if key:
    print ">>> Removing %s '%s' from the configuration..."%(variable,key)
  else:
    print ">>> Removing variable '%s' from the configuration..."%(variable)
  if verbosity>=1:
    print ">>> %-14s = %s"%('variable',variable)
    print ">>> %-14s = %s"%('key',key)
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  if key: # redirect 'channel' and 'era' keys to main_link
    variable = variable+'s'
    if variable in CONFIG:
      CONFIG[variable].pop(key)
      CONFIG.write()
    else:
      print ">>> Variable '%s' not in the configuration. Nothing to remove..."%(variable)
  else:
    if variable in CONFIG:
      CONFIG.pop(variable)
      CONFIG.write()
    else:
      print ">>> Variable '%s' not in the configuration. Nothing to remove..."%(variable)
  


###########
#   RUN   #
###########

def main_run(args):
  """Run given module locally."""
  if args.verbosity>=1:
    print ">>> main_run", args
  eras      = args.eras
  channels  = args.channels
  tag       = args.tag
  outdir    = args.outdir
  dtypes    = args.dtypes
  filters   = args.samples
  vetoes    = args.vetoes
  force     = args.force
  extraopts = args.extraopts
  maxevts   = args.maxevts
  userfiles = args.infiles
  nfiles    = args.nfiles
  nsamples  = args.nsamples
  dryrun    = args.dryrun
  verbosity = args.verbosity
  
  # LOOP over ERAS
  if not eras:
    print ">>> Please specify a valid era (-y)."
  if not channels:
    print ">>> Please specify a valid channel (-c)."
  for era in eras:
    moddict = { } # save time by loading samples and get their files only once
    
    # LOOP over CHANNELS
    for channel in channels:
      LOG.header("%s, %s"%(era,channel))
      
      # CHANNEL -> MODULE
      skim = 'skim' in channel.lower()
      LOG.insist(channel in CONFIG.channels,"Channel '%s' not found in the configuration file. Available: %s"%(channel,CONFIG.channels))
      module = CONFIG.channels[channel]
      if not skim: # channel!='test' and
        ensuremodule(module)
      outdir = ensuredir(outdir.lstrip('/'))
      
      # PROCESSOR
      procopts_  = "" # extra options for processor
      if skim:
        parts     = module.split(' ')
        processor = parts[0]
        procopts_ = ' '.join(parts[1:])
      ###elif channel=='test':
      ###  processor = module
      else:
        processor = "picojob.py"
      processor   = os.path.join("python/processors",processor)
      if not os.path.isfile(processor):
        LOG.throw(IOError,"Processor '%s' does not exist in '%s'..."%(processor,procpath))
      #processor = os.path.abspath(procpath)
      
      # VERBOSE
      if verbosity>=1:
        print '-'*80
        print ">>> Running %r"%(channel)
        print ">>> %-12s = %r"%('channel',channel)
        print ">>> %-12s = %r"%('module',module)
        print ">>> %-12s = %r"%('processor',processor)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %r"%('dtypes',dtypes)
        print ">>> %-12s = %r"%('outdir',outdir)
      
      # GET SAMPLES
      if not userfiles and (filters or vetoes or dtypes):
        LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
        samples = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters,veto=vetoes,moddict=moddict,verb=verbosity)
        if nsamples>0:
          samples = samples[:nsamples]
        if not samples:
          print ">>> Did not find any samples."
      else:
        samples = [None]
      if verbosity>=2:
        print ">>> %-12s = %r"%('samples',samples)
      if verbosity>=1:
        print '-'*80
      
      # LOOP over SAMPLES
      for sample in samples:
        if sample:
          print ">>> %s"%(bold(sample.name))
          if verbosity>=1:
            for path in sample.paths:
              print ">>> %s"%(bold(path))
        
        # SETTINGS
        filetag    = tag
        dtype      = None
        extraopts_ = extraopts[:]
        if sample:
          filetag += '_%s_%s'%(era,sample.name)
          if sample.extraopts:
            extraopts_.extend(sample.extraopts)
        if verbosity>=1:
          print ">>> %-12s = %s"%('sample',sample)
          print ">>> %-12s = %r"%('filetag',filetag) # postfix
          print ">>> %-12s = %s"%('extraopts',extraopts_)
        
        # GET FILES
        infiles = [ ]
        if userfiles:
          infiles = userfiles[:]
        elif sample:
          nevents = 0
          infiles = sample.getfiles(verb=verbosity)
          dtype   = sample.dtype
          if nfiles>0:
            infiles = infiles[:nfiles]
          if verbosity==1:
            print ">>> %-12s = %r"%('dtype',dtype)
            print ">>> %-12s = %s"%('nfiles',len(infiles))
            print ">>> %-12s = [ "%('infiles')
            for file in infiles:
              print ">>>   %r"%file
            print ">>> ]"
        if verbosity==1:
          print '-'*80
        
        # RUN
        runcmd = processor
        if procopts_:
          runcmd += " %s"%(procopts_)
        if skim:
          runcmd += " -y %s -o %s"%(era,outdir)
        ###elif 'test' in channel:
        ###  runcmd += " -o %s"%(outdir)
        else: # analysis
          runcmd += " -y %s -c %s -M %s -o %s"%(era,channel,module,outdir)
        if dtype:
          runcmd += " -d %r"%(dtype)
        if filetag:
          runcmd += " -t %r"%(filetag) # postfix
        if maxevts:
          runcmd += " -m %s"%(maxevts)
        if infiles:
          runcmd += " -i %s"%(' '.join(infiles))
        if extraopts_:
          runcmd += " --opt '%s'"%("' '".join(extraopts_))
        #elif nfiles:
        #  runcmd += " --nfiles %s"%(nfiles)
        print ">>> Executing: "+bold(runcmd)
        if not dryrun:
          #execute(runcmd,dry=dryrun,verb=verbosity+1) # real-time print out does not work well with python script 
          os.system(runcmd)
        print
      


####################
#   PREPARE JOBS   #
####################

def preparejobs(args):
  """Help function for (re)submission to iterate over samples per given channel and era
  and prepare job config and list."""
  if args.verbosity>=1:
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
  extraopts    = args.extraopts
  prefetch     = args.prefetch
  nfilesperjob = args.nfilesperjob
  split_nfpj   = args.split_nfpj
  testrun      = args.testrun
  verbosity    = args.verbosity
  jobs         = [ ]
  
  # LOOP over ERAS
  for era in eras:
    moddict = { } # save time by loading samples and get their file list only once
    
    # LOOP over CHANNELS
    for channel in channels:
      LOG.header("%s, %s"%(era,channel))
      
      # CHANNEL -> MODULE
      skim = 'skim' in channel.lower()
      LOG.insist(channel in CONFIG.channels,"Channel '%s' not found in the configuration file. Available: %s"%(channel,CONFIG.channels))
      module = CONFIG.channels[channel]
      if not skim: #channel!='test'
        ensuremodule(module)
      if verbosity>=1:
        print '-'*80
        print ">>> %-12s = %r"%('channel',channel)
        print ">>> %-12s = %r"%('module',module)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %r"%('dtypes',dtypes)
      
      # PROCESSOR
      procopts_ = ""
      if skim:
        parts     = module.split(' ')
        processor = parts[0]
        procopts_ = ' '.join(parts[1:])
      ###elif channel=='test':
      ###  processor = module
      else:
        processor = "picojob.py"
      procpath  = os.path.join("python/processors",processor)
      if not os.path.isfile(procpath):
        LOG.throw(IOError,"Processor '%s' does not exist in '%s'..."%(processor,procpath))
      processor = os.path.abspath(procpath)
      if verbosity>=1:
        print ">>> %-12s = %r"%('processor',processor)
        print '-'*80
      
      # GET SAMPLES
      jobdirformat = CONFIG.jobdir # for job config & log files
      outdirformat = CONFIG.nanodir if skim else CONFIG.outdir # for job output
      if resubmit:
        # TODO: allow user to resubmit given config file
        jobcfgs  = repkey(os.path.join(jobdirformat,"config/jobconfig_$SAMPLE$TAG_try[0-9]*.json"),
                          ERA=era,SAMPLE='*',CHANNEL=channel,TAG=tag)
        if verbosity>=2:
          print ">>> %-12s = %s"%('cwd',os.getcwd())
          print ">>> %-12s = %s"%('jobcfgs',jobcfgs)
        samples = getcfgsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      else:
        LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
        samples = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters,veto=vetoes,moddict=moddict,verb=verbosity)
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(repr(s.name) for s in samples)
      if testrun:
        samples = samples[:2] # only run two samples
      
      # SAMPLE over SAMPLES
      found = False
      for sample in samples:
        if sample.channels and channel not in sample.channels: continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # DIRECTORIES
        subtry     = sample.subtry+1 if resubmit else 1
        jobids     = sample.jobcfg.get('jobids',[ ])
        dtype      = sample.dtype
        postfix    = "_%s%s"%(channel,tag)
        jobtag     = '%s_try%d'%(postfix,subtry)
        jobname    = sample.name+jobtag.rstrip('try1').rstrip('_')
        extraopts_ = extraopts[:]
        if sample.extraopts:
          extraopts_.extend(sample.extraopts)
        nfilesperjob_ = sample.nfilesperjob if sample.nfilesperjob>0 else nfilesperjob
        if split_nfpj>1:
          nfilesperjob_ = min(1,nfilesperjob_/split_nfpj)
        outdir     = repkey(outdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                         DAS=sample.paths[0].strip('/'),GROUP=sample.group)
        jobdir     = ensuredir(repkey(jobdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                                   DAS=sample.paths[0].strip('/'),GROUP=sample.group))
        cfgdir     = ensuredir(jobdir,"config")
        logdir     = ensuredir(jobdir,"log")
        cfgname    = "%s/jobconfig%s.json"%(cfgdir,jobtag)
        joblist    = '%s/jobarglist%s.txt'%(cfgdir,jobtag)
        if verbosity==1:
          print ">>> %-12s = %s"%('cfgname',cfgname)
          print ">>> %-12s = %s"%('joblist',joblist)
        elif verbosity>=2:
          print '-'*80
          print ">>> Preparing job %ssubmission for '%s'"%("re" if resubmit else "",sample.name)
          print ">>> %-12s = %r"%('processor',processor)
          print ">>> %-12s = %r"%('dtype',dtype)
          print ">>> %-12s = %r"%('jobname',jobname)
          print ">>> %-12s = %r"%('jobtag',jobtag)
          print ">>> %-12s = %r"%('postfix',postfix)
          print ">>> %-12s = %r"%('outdir',outdir)
          print ">>> %-12s = %r"%('extraopts',extraopts_)
          print ">>> %-12s = %r"%('cfgdir',cfgdir)
          print ">>> %-12s = %r"%('logdir',logdir)
          print ">>> %-12s = %r"%('cfgname',cfgname)
          print ">>> %-12s = %r"%('joblist',joblist)
          print ">>> %-12s = %s"%('try',subtry)
          print ">>> %-12s = %r"%('jobids',jobids)
        
        # CHECKS
        if os.path.isfile(cfgname):
          # TODO: check for running jobs
          LOG.warning("Job configuration %r already exists and will be overwritten! "%(cfgname)+
                      "Beware of conflicting job output!")
        if not resubmit:
          cfgpattern = re.sub(r"(?<=try)\d+(?=.json$)",r"*",cfgname)
          cfgnames   = [f for f in glob.glob(cfgpattern) if not f.endswith("_try1.json")]
          if cfgnames:
            LOG.warning("Job configurations for resubmission already exists! This can cause conflicting job output!"+
              "If you are sure you want to submit from scratch, please remove these files:\n>>>   "+"\n>>>   ".join(cfgnames))
        storage = getstorage(outdir,verb=verbosity,ensure=True)
        
        # GET FILES
        nevents = 0
        if resubmit: # resubmission
          if checkqueue==0 and not jobs: # check jobs only once
            batch = getbatch(CONFIG,verb=verbosity)
            jobs  = batch.jobs(verb=verbosity-1)
          infiles, chunkdict = checkchuncks(sample,outdir=outdir,channel=channel,tag=tag,jobs=jobs,
                                         checkqueue=checkqueue,das=checkdas,verb=verbosity)
          nevents = sample.jobcfg['nevents'] # updated in checkchuncks
        else: # first-time submission
          infiles   = sample.getfiles(verb=verbosity-1)
          if checkdas:
            nevents = sample.getnevents()
          chunkdict = { }
        if testrun:
          infiles = infiles[:2] # only run two files per sample
        if verbosity==1:
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
        elif verbosity>=2:
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
          print ">>> %-12s = [ "%('infiles')
          for file in infiles:
            print ">>>   %r"%file
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
        if fchunks:
          with open(joblist,'w') as listfile:
            ichunk = 0
            for fchunk in fchunks:
              while ichunk in chunkdict:
                ichunk  += 1 # allows for different nfilesperjob on resubmission
                continue
              jobfiles   = ' '.join(fchunk) # list of input files
              filetag    = postfix
              if not skim:
                filetag += "_%d"%(ichunk)
              jobcmd     = processor
              if procopts_:
                jobcmd  += " %s"%(procopts_)
              if skim:
                jobcmd  += " -y %s -d '%s' --copydir %s -t %s"%(era,dtype,outdir,filetag)
              ###elif channel=='test':
              ###  jobcmd += " -o %s -t %s -i %s"%(outdir,filetag)
              else:
                jobcmd  += " -y %s -d %r -c %s -M %s --copydir %s -t %s"%(era,dtype,channel,module,outdir,filetag)
              if prefetch:
                jobcmd  += " -p"
              if testrun:
                jobcmd  += " -m %d"%(testrun) # process a limited amount of events
              if extraopts_:
                jobcmd  += " --opt '%s'"%("' '".join(extraopts_))
              jobcmd    += " -i %s"%(jobfiles) # add last
              if args.verbosity>=1:
                print jobcmd
              listfile.write(jobcmd+'\n')
              chunkdict[ichunk] = fchunk
              chunks.append(ichunk)
        
        # JSON CONFIG
        jobcfg = OrderedDict([
          ('time',str(datetime.now())),
          ('group',sample.group), ('paths',sample.paths), ('name',sample.name), ('nevents',nevents),
          ('dtype',dtype),        ('channel',channel),    ('module',module),    ('extraopts',extraopts_),
          ('jobname',jobname),    ('jobtag',jobtag),      ('tag',tag),          ('postfix',postfix),
          ('try',subtry),         ('jobids',jobids),
          ('outdir',outdir),      ('jobdir',jobdir),      ('cfgdir',cfgdir),    ('logdir',logdir),
          ('cfgname',cfgname),    ('joblist',joblist),
          ('nfiles',nfiles),      ('files',infiles),      ('nfilesperjob',nfilesperjob_), #('nchunks',nchunks),
          ('nchunks',nchunks),    ('chunks',chunks),      ('chunkdict',chunkdict),
        ])
        
        # YIELD
        yield jobcfg
        print
      
      if not found:
        print ">>> Did not find any samples."
        if verbosity>=1:
          print ">>> %-8s = %s"%('filters',filters)
          print ">>> %-8s = %s"%('vetoes',vetoes)
    


##################
#   CHECK JOBS   #
##################

def checkchuncks(sample,**kwargs):
  """Help function to check jobs status: success, pending, failed or missing.
  Return list of files to be resubmitted, and a dictionary between chunk index and input files."""
  outdir       = kwargs.get('outdir',      None)
  channel      = kwargs.get('channel',     None)
  tag          = kwargs.get('tag',         None)
  checkqueue   = kwargs.get('checkqueue', False)
  pendjobs     = kwargs.get('jobs',         [ ])
  checkdas     = kwargs.get('das',         True)
  verbosity    = kwargs.get('verb',           0)
  oldjobcfg    = sample.jobcfg
  oldcfgname   = oldjobcfg['config']
  chunkdict    = oldjobcfg['chunkdict'] # filenames
  jobids       = oldjobcfg['jobids']
  joblist      = oldjobcfg['joblist']
  postfix      = oldjobcfg['postfix']
  nfilesperjob = oldjobcfg['nfilesperjob']
  if outdir==None:
    outdir     = oldjobcfg['outdir']
  storage      = getstorage(outdir,ensure=True)
  if channel==None:
    channel    = oldjobcfg['channel']
  if tag==None:
    tag        = oldjobcfg['tag']
  noldchunks   = len(chunkdict) # = number of jobs
  goodchunks   = [ ] # good job output
  pendchunks   = [ ] # pending or running jobs
  badchunks    = [ ] # corrupted job output
  misschunks   = [ ] # missing job output
  resubfiles   = [ ] # files to resubmit (if bad or missing)
  
  # NUMBER OF EVENTS
  nprocevents = 0   # total number of processed events
  ndasevents  = oldjobcfg['nevents'] # total number of available events
  if checkdas and oldjobcfg['nevents']==0:
    ndasevents = sample.getnevents()
    oldjobcfg['nevents'] = ndasevents
  if verbosity>=2:
    print ">>> %-12s = %s"%('ndasevents',ndasevents)
  if verbosity>=3:
    print ">>> %-12s = %s"%('chunkdict',chunkdict)
  
  # CHECK PENDING JOBS
  if checkqueue<0 or pendjobs:
    batch = getbatch(CONFIG,verb=verbosity)
    if checkqueue!=1 or not pendjobs:
      pendjobs = batch.jobs(jobids,verb=verbosity-1) # get refreshed job list
    else:
      pendjobs = [j for j in pendjobs if j.jobid in jobids] # get new job list with right job id
  
  ###########################################################################
  # CHECK SKIMMED OUTPUT: nanoAOD format, one or more output files per job
  if 'skim' in channel.lower(): # and nfilesperjob>1:
    flagexp  = re.compile(r"-i (.+\.root)") #r"-i ((?:(?<! -).)+\.root[, ])"
    fpattern = "*%s.root"%(postfix)
    chunkexp = re.compile(r".+%s\.root"%(postfix))
    if verbosity>=2:
      print ">>> %-12s = %r"%('flagexp',flagexp.pattern)
      print ">>> %-12s = %r"%('fpattern',fpattern)
      print ">>> %-12s = %r"%('chunkexp',chunkexp.pattern)
      print ">>> %-12s = %s"%('checkqueue',checkqueue)
      print ">>> %-12s = %s"%('pendjobs',pendjobs)
      print ">>> %-12s = %s"%('jobids',jobids)
    
    # CHECK PENDING JOBS
    pendfiles = [ ]
    for job in pendjobs:
      if verbosity>=3:
        print ">>> Found job %r, status=%r, args=%r"%(job,job.getstatus(),job.args.rstrip())
      if job.getstatus() in ['q','r']:
        if CONFIG.batch=='HTCondor':
          jobarg  = str(job.args)
          matches = flagexp.findall(jobarg)
        else:
          jobarg  = getline(joblist,job.taskid-1)
          matches = flagexp.findall(jobarg)
        if verbosity>=3:
          print ">>> matches = ",matches
        if not matches:
          continue
        infiles = [ ]
        for file in matches[0].split():
          if not file.endswith('.root'):
            break
          infiles.append(file)
        LOG.insist(infiles,"Did not find any root files in %r, matches=%r"%(jobarg,matches))
        ichunk = -1
        for i in chunkdict:
          if all(f in chunkdict[i] for f in infiles):
            ichunk = i
            break
        LOG.insist(ichunk>=0,
                   "Did not find to which the input files of jobids %s belong! "%(jobids)+
                   "\nichunk=%s,\ninfiles=%s,\nchunkdict=%s"%(ichunk,infiles,chunkdict))
        LOG.insist(len(chunkdict[i])==len(infiles),
                   "Mismatch between input files of jobids %s and chunkdict! "%(jobids)+
                   "\nichunk=%s,\ninfiles=%s,\nchunkdict[%s]=%s"%(ichunk,infiles,ichunk,chunkdict[ichunk]))
        pendchunks.append(ichunk)
    
    # CHECK OUTPUT FILES
    badfiles  = [ ]
    goodfiles = [ ]
    fnames    = storage.getfiles(filter=fpattern,verb=verbosity-1)
    if verbosity>=2:
      print ">>> %-12s = %s"%('pendchunks',pendchunks)
      print ">>> %-12s = %s"%('fnames',fnames)
    for fname in fnames:
      if verbosity>=2:
        print ">>>   Checking job output '%s'..."%(fname)
      infile = os.path.basename(fname.replace(postfix+".root",".root")) # reconstruct input file
      nevents = isvalid(fname) # check for corruption
      ichunk = -1
      fmatch = None
      for i in chunkdict:
        if fmatch:
          break
        for chunkfile in chunkdict[i]:
          if infile in chunkfile: # find chunk input file belongs to
            ichunk = i
            fmatch = chunkfile
            break
      if ichunk<0:
        if verbosity>=2:
          print ">>>   => No match..."
        #LOG.warning("Did not recognize output file '%s'!"%(fname))
        continue
      if ichunk in pendchunks:
        if verbosity>=2:
          print ">>>   => Pending..."
        continue
      if nevents<0:
        if verbosity>=2:
          print ">>>   => Bad nevents=%s..."%(nevents)
        badfiles.append(fmatch)
      else:
        if verbosity>=2:
          print ">>>   => Good, nevents=%s"%(nevents)
        nprocevents += nevents
        goodfiles.append(fmatch)
    
    # GET FILES for RESUBMISSION + sanity checks
    for ichunk in chunkdict.keys():
      if ichunk in pendchunks:
        continue
      chunkfiles = chunkdict[ichunk]
      if all(f in goodfiles for f in chunkfiles): # all files succesful
        goodchunks.append(ichunk)
        continue
      bad = False # count each chunk only once: bad, else missing
      for fname in chunkfiles:
        LOG.insist(fname not in resubfiles,"Found file for chunk '%d' more than once: %s "%(ichunk,fname)+
                                           "Possible overcounting or conflicting job output file format!")
        if fname in badfiles:
          bad = True
          resubfiles.append(fname)
        elif fname not in goodfiles:
          resubfiles.append(fname)
      if bad:
        badchunks.append(ichunk)
      else:
        misschunks.append(ichunk)
      chunkdict.pop(ichunk)
  
  ###########################################################################
  # CHECK ANALYSIS OUTPUT: custom tree format, one output file per job, numbered post-fix
  else:
    flagexp  = re.compile(r"-t \w*_(\d+)")
    fpattern = "*%s_[0-9]*.root"%(postfix)
    chunkexp = re.compile(r".+%s_(\d+)\.root"%(postfix))
    if verbosity>=2:
      print ">>> %-12s = %r"%('flagexp',flagexp.pattern)
      print ">>> %-12s = %r"%('fpattern',fpattern)
      print ">>> %-12s = %r"%('chunkexp',chunkexp.pattern)
      print ">>> %-12s = %s"%('checkqueue',checkqueue)
      print ">>> %-12s = %s"%('pendjobs',pendjobs)
      print ">>> %-12s = %s"%('jobids',jobids)
    
    # CHECK PENDING JOBS
    for job in pendjobs:
      if verbosity>=3:
        print ">>> Found job %r, status=%r, args=%r"%(job,job.getstatus(),job.args.rstrip())
      if job.getstatus() in ['q','r']:
        if CONFIG.batch=='HTCondor':
          jobarg  = str(job.args)
          matches = flagexp.findall(jobarg)
        else:
          jobarg  = getline(joblist,job.taskid-1)
          matches = flagexp.findall(jobarg)
        if verbosity>=3:
          print ">>> jobarg = %r"%(jobarg)
          print ">>> matches = %s"%(matches)
        if not matches:
          continue
        ichunk = int(matches[0])
        LOG.insist(ichunk in chunkdict,"Found an impossible chunk %d for job %s.%s! "%(ichunk,job.jobid,job.taskid)+
                                       "Possible overcounting!")
        pendchunks.append(ichunk)
    
    # CHECK OUTPUT FILES
    fnames = storage.getfiles(filter=fpattern,verb=verbosity-1)
    if verbosity>=2:
      print ">>> %-12s = %s"%('pendchunks',pendchunks)
      print ">>> %-12s = %s"%('fnames',fnames)
    for fname in fnames:
      if verbosity>=2:
        print ">>>   Checking job output '%s'..."%(fname)
      match = chunkexp.search(fname)
      if match:
        ichunk = int(match.group(1))
        LOG.insist(ichunk in chunkdict,"Found an impossible chunk %d for file %s!"%(ichunk,fname)+
                                       "Possible overcounting or conflicting job output file format!")
        if ichunk in pendchunks:
          continue
      else:
        #LOG.warning("Did not recognize output file '%s'!"%(fname))
        continue
      nevents = isvalid(fname) # check for corruption
      if nevents<0:
        if verbosity>=2:
          print ">>>   => Bad, nevents=%s"%(nevents)
        badchunks.append(ichunk)
        # TODO: remove file from outdir?
      else:
        if verbosity>=2:
          print ">>>   => Good, nevents=%s"%(nevents)
        nprocevents += nevents
        goodchunks.append(ichunk)
    
    # GET FILES for RESUBMISSION + sanity checks
    if verbosity>=2:
      print ">>> %-12s = %s"%('nprocevents',nprocevents)
    for ichunk in chunkdict.keys():
      count = goodchunks.count(ichunk)+pendchunks.count(ichunk)+badchunks.count(ichunk)
      LOG.insist(count in [0,1],"Found %d times chunk '%d' (good=%d, pending=%d, bad=%d). "%(
                                count,ichunk,goodchunks.count(ichunk),pendchunks.count(ichunk),badchunks.count(ichunk))+
                                "Possible overcounting or conflicting job output file format!")
      if count==0: # missing chunk
        misschunks.append(ichunk)
      elif ichunk not in badchunks: # good or pending chunk
        continue
      fchunk = chunkdict[ichunk]
      for fname in fchunk:
        LOG.insist(fname not in resubfiles,"Found file for chunk '%d' more than once: %s "%(ichunk,fname)+
                                           "Possible overcounting or conflicting job output file format!")
      resubfiles.extend(chunkdict[ichunk])
      chunkdict.pop(ichunk) # only save good chunks
  
  ###########################################################################
  
  goodchunks.sort()
  pendchunks.sort()
  badchunks.sort()
  misschunks.sort()
  
  # PRINT
  def printchunks(jobden,label,text,col,show=False):
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
  printchunks(goodchunks,'SUCCESS', "Chunks with output in outdir"+rtext,'green')
  printchunks(pendchunks,'PEND',"Chunks with pending or running jobs",'white',True)
  printchunks(badchunks, 'FAIL', "Chunks with corrupted output in outdir",'red',True)
  printchunks(misschunks,'MISS',"Chunks with no output in outdir",'red',True)
  
  return resubfiles, chunkdict
  
def isvalid(fname):
  """Check if a given file is valid, or corrupt."""
  nevts = -1
  file  = TFile.Open(fname,'READ')
  if file and not file.IsZombie():
    if file.GetListOfKeys().Contains('tree') and file.GetListOfKeys().Contains('cutflow'):
      nevts = file.Get('cutflow').GetBinContent(1)
      if nevts<=0:
        LOG.warning("Cutflow of file %r has nevts=%s<=0..."%(fname,nevts))
    if file.GetListOfKeys().Contains('Events'):
      nevts = file.Get('Events').GetEntries()
      if nevts<=0:
        LOG.warning("'Events' tree of file %r has nevts=%s<=0..."%(fname,nevts))
  return nevts
  


##################
#   (RE)SUBMIT   #
##################

def main_submit(args):
  """Submit or resubmit jobs to the batch system."""
  if args.verbosity>=1:
    print ">>> main_submit", args
  
  verbosity = args.verbosity
  resubmit  = args.subcommand=='resubmit'
  force     = args.force #or True
  dryrun    = args.dryrun #or True
  testrun   = args.testrun #or True
  queue     = args.queue
  batchopts = args.batchopts
  batch     = getbatch(CONFIG,verb=verbosity+1)
  
  for jobcfg in preparejobs(args):
    jobid   = None
    cfgname = jobcfg['cfgname']
    jobdir  = jobcfg['jobdir']
    logdir  = jobcfg['logdir']
    outdir  = jobcfg['outdir']
    joblist = jobcfg['joblist']
    jobname = jobcfg['jobname']
    nchunks = jobcfg['nchunks']
    jkwargs = { # key-word arguments for batch.submit
      'name': jobname, 'queue':queue, 'opt': batchopts, 'dry': dryrun
    }
    if nchunks<=0:
      print ">>>   Nothing to %ssubmit!"%('re' if resubmit else '')
      continue
    if batch.system=='HTCondor':
      # use specific settings for KIT condor
      if 'etp' in GLOB._host:
        script = "python/batch/submit_HTCondor_KIT.sub"
      else:
        script = "python/batch/submit_HTCondor.sub"
      appcmds = ["initialdir=%s"%(jobdir),
                 "mylogfile='log/%s.$(ClusterId).$(ProcId).log'"%(jobname)]
      if testrun and not queue:
        queue = "espresso"
      qcmd    = "arg from %s"%(joblist)
      jkwargs.update({'queue':queue, 'app': appcmds, 'qcmd': qcmd })
      #jobid   = batch.submit(script,name=jobname,app=appcmds,qcmd=qcmd,opt=batchopts,queue=queue,dry=dryrun)
    elif batch.system=='SLURM':
      script  = "python/batch/submit_SLURM.sh %s"%(joblist)
      logfile = os.path.join(logdir,"%x.%A.%a") # $JOBNAME.o$JOBID.$TASKID
      jkwargs.update({'log': logfile, 'array': nchunks })
      #jobid   = batch.submit(script,name=jobname,log=logfile,array=nchunks,opt=batchopts,queue=queue,dry=dryrun)
    #elif batch.system=='SGE':
    #elif batch.system=='CRAB':
    else:
      LOG.throw(NotImplementedError,"Submission for batch system '%s' has not been implemented (yet)..."%(batch.system))
    
    # SUBMIT
    if args.prompt: # ask before submitting
      while True:
        submit = raw_input(">>> Do you want to submit %d jobs to the batch system? [y/n] "%(nchunks))
        if any(s in submit.lower() for s in ['q','exit']):
          print ">>> Quitting..."
          exit(0)
        elif any(s in submit.lower() for s in ['f','all']):
          print ">>> Force submission..."
          submit = 'y'
          args.prompt = False # stop asking for next samples
        if 'y' in submit.lower():
          jobid = batch.submit(script,**jkwargs)
          break
        elif 'n' in submit.lower():
          print ">>> Not submitting."
          break
        else:
          print ">>> '%s' is not a valid answer, please choose y/n."%submit
    else:
      jobid = batch.submit(script,**jkwargs)
    
    # WRITE JOBCONFIG
    if jobid!=None:
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
  if args.verbosity>=1:
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
  cmdverb        = max(1,verbosity)
  outdirformat   = CONFIG.outdir
  jobdirformat   = CONFIG.jobdir
  storedirformat = CONFIG.picodir
  jobs           = [ ]
  
  # LOOP over ERAS
  for era in eras:
    
    # LOOP over CHANNELS
    for channel in channels:
      LOG.header("%s, %s"%(era,channel))
      
      # GET SAMPLES
      jobcfgs = repkey(os.path.join(jobdirformat,"config/jobconfig_$CHANNEL$TAG_try[0-9]*.json"),
                       ERA=era,SAMPLE='*',GROUP='*',CHANNEL=channel,TAG=tag)
      if verbosity>=1:
        print ">>> %-12s = %s"%('cwd',os.getcwd())
        print ">>> %-12s = %s"%('jobcfgs',jobcfgs)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %s"%('dtypes',dtypes)
      samples = getcfgsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(repr(s.name) for s in samples)
      if hadd and 'skim' in channel.lower():
        LOG.warning("Hadding into one file not available for skimming...")
        print
        continue
      
      # SAMPLE over SAMPLES
      found = False
      for sample in samples:
        if sample.channels and channel not in sample.channels: continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # CHECK JOBS ONLY ONCE
        if checkqueue==1 and not jobs:
          batch = getbatch(CONFIG,verb=verbosity)
          jobs  = batch.jobs(verb=verbosity-1)
        
        # HADD
        if hadd:
          jobdir   = sample.jobcfg['jobdir']
          outdir   = sample.jobcfg['outdir']
          postfix  = sample.jobcfg['postfix']
          storedir = repkey(storedirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                           DAS=sample.paths[0].strip('/'),GROUP=sample.group)
          storage  = getstorage(storedir,ensure=True,verb=verbosity)
          outfile  = '%s_%s%s.root'%(sample.name,channel,tag)
          infiles  = os.path.join(outdir,'*%s_[0-9]*.root'%(postfix))
          cfgfiles = os.path.join(sample.jobcfg['cfgdir'],'job*%s_try[0-9]*.*'%(postfix))
          logfiles = os.path.join(sample.jobcfg['logdir'],'*%s_try[0-9]*.*.*.log'%(postfix))
          if verbosity>=1:
            print ">>> Hadd'ing job output for '%s'"%(sample.name)
            print ">>> %-12s = %r"%('jobdir',jobdir)
            print ">>> %-12s = %r"%('outdir',outdir)
            print ">>> %-12s = %r"%('storedir',storedir)
            print ">>> %-12s = %s"%('infiles',infiles)
            print ">>> %-12s = %r"%('outfile',outfile)
          resubfiles, chunkdict = checkchuncks(sample,channel=channel,tag=tag,jobs=jobs,
                                               checkqueue=checkqueue,das=checkdas,verb=verbosity)
          if len(resubfiles)>0 and not force:
            LOG.warning("Cannot hadd job output because %d chunks need to be resubmitted..."%(len(resubfiles))+
                        "Please use -f or --force to hadd anyway.\n")
            continue
          #haddcmd = 'hadd -f %s %s'%(outfile,infiles)
          #haddout = execute(haddcmd,dry=dryrun,verb=max(1,verbosity))
          haddout = storage.hadd(infiles,outfile,dry=dryrun,verb=cmdverb)
          #os.system(haddcmd)
          
          # CLEAN UP
          # TODO: check if hadd was succesful with isvalid
          if cleanup:
            rmfiles   = ""
            rmfileset = [infiles,cfgfiles,logfiles]
            for files in rmfileset:
              if len(glob.glob(files))>0:
                rmfiles += ' '+files
            if verbosity>=2:
              print ">>> %-12s = %s"%('rmfileset',rmfileset)
              print ">>> %-12s = %s"%('rmfiles',rmfiles)
            if rmfiles:
              rmcmd = "rm %s"%(rmfiles)
              rmout = execute(rmcmd,dry=dryrun,verb=cmdverb)
        
        # ONLY CHECK STATUS
        else:
          jobdir   = sample.jobcfg['jobdir']
          outdir   = sample.jobcfg['outdir']
          logdir   = sample.jobcfg['logdir']
          if verbosity>=1:
            print ">>> Checking job status for '%s'"%(sample.name)
            print ">>> %-12s = %r"%('jobdir',jobdir)
            print ">>> %-12s = %r"%('outdir',outdir)
            print ">>> %-12s = %r"%('logdir',logdir)
          checkchuncks(sample,channel=channel,tag=tag,jobs=jobs,
                       checkqueue=checkqueue,das=checkdas,verb=verbosity)
        
        print
      
      if not found:
        print ">>> Did not find any samples."
        print
  


############
#   MAIN   #
############

if __name__ == "__main__":
  
  # COMMON
  description = "Central script to process nanoAOD for skimming or analysis."
  parser = ArgumentParser(prog='pico.py',description=description,epilog="Good luck!")
  parser_cmn = ArgumentParser(add_help=False)
  parser_cmn.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                                help="set verbosity" )
  parser_sam = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_lnk = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_sam.add_argument('-c','--channel',     dest='channels', choices=CONFIG.channels.keys(), default=[ ], nargs='+',
                                                help='skimming or analysis channel to run')
  parser_sam.add_argument('-y','-e','--era',    dest='eras', choices=CONFIG.eras.keys(), default=[ ], nargs='+',
                                                help='year or era to specify the sample list')
  parser_sam.add_argument('-s', '--sample',     dest='samples', type=str, nargs='+', default=[ ], action='store',
                          metavar='PATTERN',    help="filter these samples; glob patterns like '*' and '?' wildcards are allowed" )
  parser_sam.add_argument('-x', '--veto',       dest='vetoes', nargs='+', default=[ ], action='store',
                          metavar='PATTERN',    help="exclude/veto these samples; glob patterns are allowed" )
  parser_sam.add_argument('--dtype',            dest='dtypes', choices=GLOB._dtypes, default=GLOB._dtypes, nargs='+',
                                                help='filter these data type(s)')
  parser_sam.add_argument('-D','--das',         dest='checkdas', default=False, action='store_true',
                                                help="check DAS for total number of events" )
  parser_sam.add_argument('-t','--tag',         dest='tag', default="",
                                                help='tag for output file name')
  parser_sam.add_argument('-f','--force',       dest='force', action='store_true',
                                                help='force overwrite')
  parser_sam.add_argument('-d','--dry',         dest='dryrun', action='store_true',
                                                help='dry run: prepare job without submitting for debugging purposes')
  parser_sam.add_argument('-E', '--opts',       dest='extraopts', type=str, nargs='+', default=[ ],
                          metavar='KEY=VALUE',  help="extra options for the skim or analysis module, "
                                                     "passed as list of 'KEY=VALUE', separated by spaces")
  parser_job = ArgumentParser(add_help=False,parents=[parser_sam])
  parser_job.add_argument('-p','--prefetch',    dest='prefetch', default=False, action='store_true',
                                                help="copy remote file during job to increase processing speed and ensure stability" )
  parser_job.add_argument('-T','--test',        dest='testrun', type=int, nargs='?', const=10000, default=0, action='store',
                                                help='run a test with limited nummer of jobs, default=%(default)d' )
  parser_job.add_argument('--getjobs',          dest='checkqueue', type=int, nargs='?', const=1, default=-1, action='store',
                          metavar='N',          help="check job status: 0 (no check), 1 (check once), -1 (check every job)" ) # speed up if batch is slow
  parser_chk = ArgumentParser(add_help=False,parents=[parser_job])
  parser_job.add_argument('-q','--queue',       dest='queue', default=None,
                                                help='queue of batch system')
  parser_job.add_argument('-P','--prompt',      dest='prompt', action='store_true',
                                                help='ask user permission before submitting a sample')
  parser_job.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
                                                help='extra options for the batch system')
  parser_job.add_argument('-n','--filesperjob', dest='nfilesperjob', type=int, default=CONFIG.nfilesperjob,
                                                help='number of files per job, default=%(default)d')
  parser_job.add_argument('--split',            dest='split_nfpj', type=int, nargs='?', const=2, default=1, action='store',
                          metavar='N',          help="divide default number of files per job, default=%(const)d" )
  
  # SUBCOMMANDS
  subparsers = parser.add_subparsers(title="sub-commands",dest='subcommand',help="sub-command help")
  help_ins = "install"
  help_lst = "list configuration"
  help_get = "get information from configuration or samples"
  help_set = "set given variable in the configuration file"
  help_rmv = "remove given variable from the configuration file"
  help_chl = "link a channel to a module in the configuration file"
  help_era = "link an era to a sample list in the configuration file"
  help_run = "run nanoAOD processor locally"
  help_sub = "submit processing jobs"
  help_res = "resubmit failed processing jobs"
  help_sts = "status of processing jobs"
  help_hdd = "hadd processing job output"
  parser_ins = subparsers.add_parser('install',  parents=[parser_cmn], help=help_ins, description=help_ins)
  parser_lst = subparsers.add_parser('list',     parents=[parser_cmn], help=help_lst, description=help_lst)
  parser_get = subparsers.add_parser('get',      parents=[parser_sam], help=help_get, description=help_get)
  parser_set = subparsers.add_parser('set',      parents=[parser_cmn], help=help_set, description=help_set)
  parser_rmv = subparsers.add_parser('rm',       parents=[parser_cmn], help=help_rmv, description=help_rmv)
  parser_chl = subparsers.add_parser('channel',  parents=[parser_lnk], help=help_chl, description=help_chl)
  parser_era = subparsers.add_parser('era',      parents=[parser_lnk], help=help_era, description=help_era)
  parser_run = subparsers.add_parser('run',      parents=[parser_sam], help=help_run, description=help_run)
  parser_sub = subparsers.add_parser('submit',   parents=[parser_job], help=help_sub, description=help_sub)
  parser_res = subparsers.add_parser('resubmit', parents=[parser_job], help=help_res, description=help_res)
  parser_sts = subparsers.add_parser('status',   parents=[parser_chk], help=help_sts, description=help_sts)
  parser_hdd = subparsers.add_parser('hadd',     parents=[parser_chk], help=help_hdd, description=help_hdd)
  #parser_get.add_argument('variable',           help='variable to change in the config file')
  parser_get.add_argument('variable',           help='variable to get information on')
  parser_set.add_argument('variable',           help='variable to change in the config file')
  parser_set.add_argument('key',                help='channel or era key name', nargs='?', default=None)
  parser_set.add_argument('value',              help='value for given value')
  parser_rmv.add_argument('variable',           help='variable to remove from the config file')
  parser_rmv.add_argument('key',                help='channel or era key name to remove', nargs='?', default=None)
  parser_chl.add_argument('key',                metavar='channel', help='channel key name')
  parser_chl.add_argument('value',              metavar='module',  help='module linked to by given channel')
  parser_era.add_argument('key',                metavar='era',     help='era key name')
  parser_era.add_argument('value',              metavar='samples', help='samplelist linked to by given era')
  parser_ins.add_argument('type',               choices=['standalone','cmmsw'], #default=None,
                                                help='type of installation: standalone or compiled in CMSSW')
  #parser_hdd.add_argument('--keep',             dest='cleanup', default=True, action='store_false',
  #                                              help="do not remove job output after hadd'ing" )
  parser_hdd.add_argument('-r','--clean',       dest='cleanup', default=False, action='store_true',
                                                help="remove job output after hadd'ing" )
  parser_run.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
                                                help='maximum number of events (per file) to process')
  parser_run.add_argument('-n','--nfiles',      dest='nfiles', type=int, default=1,
                                                help="maximum number of input files to process (per sample), default=%(default)d")
  parser_run.add_argument('-S', '--nsamples',   dest='nsamples', type=int, default=1,
                                                help="number of samples to run, default=%(default)d")
  parser_run.add_argument('-i', '--input',      dest='infiles', nargs='+', default=[ ],
                                                help="input files (nanoAOD)")
  parser_run.add_argument('-o', '--outdir',     dest='outdir', type=str, default='output',
                                                help="output directory, default=%(default)r")
  parser_get.add_argument('-w','--write',       dest='write', type=str, nargs='?', const=str(CONFIG.filelistdir), default="", action='store',
                          metavar='FILE',       help="write file list, default=%(const)r" )
  
  # SUBCOMMAND ABBREVIATIONS
  args = sys.argv[1:]
  if args:
    subcmds = [ # fix order for abbreviations
      'channel','era',
      'run','submit','resubmit','status','hadd',
      'install','list','set','rm'
    ]
    for subcmd in subcmds:
      if args[0] in subcmd[:len(args[0])]: # match abbreviation
        args[0] = subcmd
        break
  args = parser.parse_args(args)
  if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_':
    args.tag = '_'+args.tag
  
  # SUBCOMMAND MAINs
  os.chdir(CONFIG.basedir)
  if args.subcommand=='install':
    main_install(args)
  if args.subcommand=='list':
    main_list(args)
  elif args.subcommand=='get':
    main_get(args)
  elif args.subcommand=='set':
    main_set(args)
  elif args.subcommand in ['channel','era']:
    main_link(args)
  elif args.subcommand=='rm':
    main_rm(args)
  elif args.subcommand=='run':
    main_run(args)
  elif args.subcommand in ['submit','resubmit']:
    main_submit(args)
  elif args.subcommand in ['status','hadd']:
    main_status(args)
  else:
    print ">>> subcommand '%s' not implemented!"%(args.subcommand)
  
  print ">>> Done!"
  

