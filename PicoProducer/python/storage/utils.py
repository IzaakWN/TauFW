# Author: Izaak Neutelings (May 2020)
import os
import getpass, platform
import importlib
from TauFW.PicoProducer import basedir
from TauFW.common.tools.log import Logger
from TauFW.common.tools.file import ensurefile
from TauFW.common.tools.utils import repkey
LOG  = Logger('Storage')
host = platform.node()


def getsedir():
  """Guess the storage element path for a given user and host."""
  user  = getpass.getuser()
  sedir = ""
  if 'lxplus' in host:
    sedir = "/eos/user/%s/%s/"%(user[0],user)
  elif "t3" in host and "psi.ch" in host:
    sedir = "/pnfs/psi.ch/cms/trivcat/store/user/%s/"%(user)
  elif "etp" in host:
    sedir = "/store/user/{}/".format(user)
  return sedir
  

def gettmpdir():
  """Guess the temporary directory for a given user and host."""
  user  = getpass.getuser()
  sedir = ""
  if 'lxplus' in host:
    sedir = "/eos/user/%s/%s/"%(user[0],user)
  elif "t3" in host and "psi.ch" in host:
    sedir = basedir.rstrip('/')+'/' #output/$ERA/$CHANNEL/$SAMPLE/ #"/scratch/%s/"%(user)
  elif "etp" in host:
    sedir = "/tmp/{}/".format(user)
  return sedir
  

def getstorage(path,verb=0,ensure=False):
  """Guess the storage system based on the path."""
  if path.startswith('/eos/'):
    from TauFW.PicoProducer.storage.EOS import EOS
    storage = EOS(path,ensure=ensure,verb=verb)
  #elif path.startswith('/castor/'):
  #  storage = Castor(path,verb=verb)
  elif path.startswith('/pnfs/psi.ch/'):
    from TauFW.PicoProducer.storage.T3_PSI import T3_PSI
    storage = T3_PSI(path,ensure=ensure,verb=verb)
  elif path.startswith("/store/user") and "etp" in host:
    from TauFW.PicoProducer.storage.GridKA_NRG import GridKA_NRG
    storage = GridKA_NRG(path,ensure=ensure,verb=verb)
  #elif path.startswith('/pnfs/lcg.cscs.ch/'):
  #  storage = T2_PSI(path,verb=verb)
  #elif path.startswith('/pnfs/iihe/'):
  #  return T2_IIHE(path,verb=verb)
  else:
    from TauFW.PicoProducer.storage.StorageSystem import Local
    storage = Local(path,ensure=ensure,verb=verb)
  if verb>=2:
    print ">>> getstorage(%r), %r"%(path,storage)
  return storage
  

def getsamples(era,channel="",tag="",dtype=[],filter=[],veto=[],moddict={},verb=0):
  """Help function to get samples from a sample list and filter if needed."""
  import TauFW.PicoProducer.tools.config as GLOB
  CONFIG   = GLOB.getconfig(verb=verb)
  filters  = filter if not filter or isinstance(filter,list) else [filter]
  vetoes   = veto   if not veto   or isinstance(veto,list)   else [veto]
  dtypes   = dtype  if not dtype  or isinstance(dtype,list)  else [dtype]
  sampfile = ensurefile("samples",repkey(CONFIG.eras[era],ERA=era,CHANNEL=channel,TAG=tag))
  samppath = sampfile.replace('.py','').replace('/','.')
  if samppath not in moddict:
    moddict[samppath] = importlib.import_module(samppath) # save time by loading once
  if not hasattr(moddict[samppath],'samples'):
    LOG.throw(IOError,"Module '%s' must have a list of Sample objects called 'samples'!"%(samppath))
  samplelist = moddict[samppath].samples
  samples    = [ ]
  sampledict = { } # ensure for unique names
  for sample in samplelist:
    if filters and not sample.match(filters,verb): continue
    if vetoes and sample.match(vetoes,verb): continue
    if dtypes and sample.dtype not in dtypes: continue
    if channel and sample.channels and channel not in sample.channels: continue
    if sample.name in sampledict:
      LOG.throw(IOError,"Sample short names should be unique. Found two samples '%s'!\n\t%s\n\t%s"%(
                    sample.name,','.join(sampledict[sample.name].paths),','.join(sample.paths)))
    if 'skim' in channel and len(sample.paths)>=2:
      for subsample in sample.split():
        samples.append(subsample) # keep correspondence sample to one sample in DAS
    else:
      samples.append(sample)
    sampledict[sample.name] = sample
  return samples
  
