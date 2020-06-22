# Author: Izaak Neutelings (May 2020)
import os, sys
import traceback
import importlib
from math import sqrt, sin, cos, pi
from itertools import combinations
from ROOT import TH1D, TLorentzVector
from TauFW.PicoProducer import basedir
from TauFW.PicoProducer.tools.file import ensurefile
from TauFW.PicoProducer.tools.log import Logger
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
LOG = Logger('Analysis')


def ensuremodule(modname):
  """Check if module exists and has class of same name."""
  # TODO: absolute path
  modfile  = ensurefile(basedir,"python/analysis/%s.py"%(modname.replace('.','/')))
  modpath  = "TauFW.PicoProducer.analysis.%s"%(modname) #modfile.replace('.py','').replace('/','.')
  modclass = modname.split('.')[-1]
  try:
    module = importlib.import_module(modpath)
  except Exception as err:
    print traceback.format_exc()
    LOG.throw(ImportError,"Importing module '%s' failed. Please check %s! cwd=%r"%(modpath,modfile,os.getcwd()))
  if not hasattr(module,modclass):
    LOG.throw(IOError,"Module '%s' in %s does not have a module named '%s'!"%(module,modfile,modname))
  return module
  

def getmodule(modname):
  """Get give module from python module in python/analysis of the same name."""
  module   = ensuremodule(modname)
  modclass = modname.split('.')[-1]
  return getattr(module,modclass)
  

def hasbit(value,bit):
  """Check if i'th bit is set to 1, i.e. binary of 2^i,
  from the right to the left, starting from position i=0."""
  # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#GenPart
  # Gen status flags, stored bitwise, are:
  #    0: isPrompt,                          8: fromHardProcess,
  #    1: isDecayedLeptonHadron,             9: isHardProcessTauDecayProduct,
  #    2: isTauDecayProduct,                10: isDirectHardProcessTauDecayProduct,
  #    3: isPromptTauDecayProduct,          11: fromHardProcessBeforeFSR,
  #    4: isDirectTauDecayProduct,          12: isFirstCopy,
  #    5: isDirectPromptTauDecayProduct,    13: isLastCopy,
  #    6: isDirectHadronDecayProduct,       14: isLastCopyBeforeFSR
  #    7: isHardProcess,
  ###return bin(value)[-bit-1]=='1'
  ###return format(value,'b').zfill(bit+1)[-bit-1]=='1'
  return (value & (1 << bit))>0
  

def dumpgenpart(part,genparts=None,event=None):
  """Print information on gen particle. If collection is given, also print mother's PDG ID."""
  info = ">>>  i=%2s, PID=%3s, status=%2s, mother=%2s"%(part._index,part.pdgId,part.status,part.genPartIdxMother)
  if part.genPartIdxMother>=0:
    if genparts: 
      moth  = genparts[part.genPartIdxMother].pdgId
      info += " (%s)"%(moth)
    elif event:
      moth  = event.GenPart_pdgId[part.genPartIdxMother]
      info += " (%s)"%(moth)
  print info
  

def deltaR(eta1, phi1, eta2, phi2):
  """Compute DeltaR."""
  deta = eta1 - eta2
  dphi = deltaPhi(phi1, phi2)
  return sqrt( deta*deta + dphi*dphi )
  

def deltaPhi(phi1, phi2):
  """Computes DeltaPhi, handling periodic limit conditions."""
  res = phi1 - phi2
  while res>pi:
    res -= 2*pi
  while res<-pi:
    res += 2*pi
  return res
  

def getmet(year,var=""):
  """Return year-dependent MET recipe."""
  branch  = 'METFixEE2017' if year==2017 else 'MET'
  pt      = '%s_pt'%(branch)
  phi     = '%s_phi'%(branch)
  if var:
    pt   += '_'+var
    phi  += '_'+var
  funcstr = "func = lambda e: TLorentzVector(e.%s*cos(e.%s),e.%s*sin(e.%s),0,e.%s)"%(pt,phi,pt,phi,pt)
  #print funcstr
  exec funcstr #in locals()
  return func
  

def correctmet(met,dp):
  """Correct the MET by removing a four-vector, ensuring the MET has no z component or mass component.""" 
  met -= dp
  met.SetPxPyPzE(met.Px(),met.Py(),0,sqrt(met.Px()**2+met.Py()**2))
  return met
  

def getmetfilters(year,isData):
  """Return a method to check if an event passes the recommended MET filters."""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETOptionalFiltersRun2
  if year in [2017,2018]:
    if isData:
      return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_eeBadScFilter and e.Flag_ecalBadCalibFilterV2
    else:
      return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_ecalBadCalibFilterV2 # eeBadScFilter "not suggested"
  else:
    if isData:
      return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_eeBadScFilter
    else:
      return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter # eeBadScFilter "not suggested"
  

def loosestIso(tau):
  """Return a method to check whether event passes the VLoose working
  point of all available tau IDs. (For tau ID measurement.)"""
  return tau.idDeepTau2017v2p1VSjet>1 # VVLoose
  #ord(e.Tau_idMVAnewDM2017v2[i])>0 or ord(e.Tau_idMVAoldDM2017v2[i])>0
  #ord(e.Tau_idMVAoldDM[i])>0 or ord(e.Tau_idMVAoldDM2017v1[i])>0
  

def idIso(tau):
  """Compute WPs of cut-based tau isolation."""
  raw = tau.rawIso
  if tau.photonsOutsideSignalCone/tau.pt<0.10:
    return 0 if raw>4.5 else 1 if raw>3.5 else 3 if raw>2.5 else 7 if raw>1.5 else 15 if raw>0.8 else 31 # VVLoose, VLoose, Loose, Medium, Tight
  return 0 if raw>4.5 else 1 if raw>3.5 else 3 # VVLoose, VLoose
  

def getLeptonVetoes(event, electrons, muons, taus, channel):
  """Check if event has extra electrons or muons. (HTT definitions.)"""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorkingLegacyRun2#Common_lepton_vetoes
  
  extramuon_veto = False
  extraelec_veto = False
  dilepton_veto  = False
  
  # EXTRA MUON VETO
  looseMuons = [ ]
  for muon in Collection(event,'Muon'):
    if muon.pt<10: continue
    if abs(muon.eta)>2.4: continue
    if abs(muon.dz)>0.2: continue
    if abs(muon.dxy)>0.045: continue
    if muon.pfRelIso04_all>0.3: continue
    if any(muon.DeltaR(tau)<0.4 for tau in taus): continue
    if muon.mediumId and all(m._index!=muon._index for m in muons):
      extramuon_veto = True
    if muon.pt>15 and muon.isPFcand and muon.isGlobal and muon.isTracker:
      looseMuons.append(muon)
  
  # EXTRA ELECTRON VETO
  looseElectrons = [ ]
  for electron in Collection(event,'Electron'):
    if electron.pt<10: continue
    if abs(electron.eta)>2.5: continue
    if abs(electron.dz)>0.2: continue
    if abs(electron.dxy)>0.045: continue
    if electron.pfRelIso03_all>0.3: continue
    if any(electron.DeltaR(tau)<0.4 for tau in taus): continue
    if all(e._index!=electron._index for e in electrons): continue
    if electron.convVeto==1 and electron.lostHits<=1 and electron.mvaFall17V2Iso_WP90:
      extraelec_veto = True
    if electron.pt>15 and electron.cutBased>0 and electron.mvaFall17V2Iso_WPL:
      looseElectrons.append(electron)
  
  # DILEPTON VETO
  if channel=='mutau':
    for muon1, muon2 in combinations(looseMuons,2):
      if muon1.charge*muon2.charge<0 and muon1.DeltaR(muon2)>0.15:
        dilepton_veto = True
        break
  elif channel=='eletau':
    for electron1, electron2 in combinations(looseElectrons,2):
      if electron1.charge*electron2.charge<0 and electron1.DeltaR(electron2)>0.20:
        dilepton_veto = True
        break
  
  return extramuon_veto, extraelec_veto, dilepton_veto
  

class LeptonPair:
  """Container class to pair and order tau decay candidates."""
  def __init__(self, obj1, iso1, obj2, iso2):
    self.obj1 = obj1
    self.obj2 = obj2
    self.pt1  = obj1.pt
    self.pt2  = obj2.pt
    self.iso1 = iso1
    self.iso2 = iso2
    self.pair = [obj1,obj2]
  
  def __gt__(self, opair):
    """Order dilepton pairs according to the pT of both objects first, then in isolation."""
    if   self.pt1  != opair.pt1:  return self.pt1  > opair.pt1  # greater = higher pT
    elif self.pt2  != opair.pt2:  return self.pt2  > opair.pt2  # greater = higher pT
    elif self.iso1 != opair.iso1: return self.iso1 < opair.iso1 # greater = smaller isolation
    elif self.iso2 != opair.iso2: return self.iso2 < opair.iso2 # greater = smaller isolation
    return True
  
class LeptonTauPair(LeptonPair):
  def __gt__(self, opair):
    """Override for tau isolation."""
    if   self.pt1  != opair.pt1:  return self.pt1  > opair.pt1  # greater = higher pT
    elif self.pt2  != opair.pt2:  return self.pt2  > opair.pt2  # greater = higher pT
    elif self.iso1 != opair.iso1: return self.iso1 < opair.iso1 # greater = smaller lepton isolation
    elif self.iso2 != opair.iso2: return self.iso2 > opair.iso2 # greater = larger tau isolation
    return True
  
class DiTauPair(LeptonPair):
  def __gt__(self, opair):
    """Override for tau isolation."""
    if   self.pt1  != opair.pt1:  return self.pt1  > opair.pt1  # greater = higher pT
    elif self.pt2  != opair.pt2:  return self.pt2  > opair.pt2  # greater = higher pT
    elif self.iso1 != opair.iso1: return self.iso1 > opair.iso1 # greater = larger tau isolation
    elif self.iso2 != opair.iso2: return self.iso2 > opair.iso2 # greater = larger tau isolation
    return True
  

class Cutflow(object):
  """Container class for cutflow."""
  
  def __init__(self, histname, ncuts, **kwargs):
    self.hist    = TH1D('cutflow','cutflow',ncuts,0,ncuts)
    self.hist.GetXaxis().SetLabelSize(0.041)
    self.nextidx = 0
    self.cuts    = { }
  
  def addcut(self, name, title, index=None):
    if index==None:
      index = self.nextidx
      self.nextidx += 1
    #assert not hasattr(self,name), "%s already has attribute '%s'!"%(self,name)
    #setattr(self,name,index)
    bin = 1+index
    self.hist.GetXaxis().SetBinLabel(bin,title)
    self.cuts[name] = index
  
  def fill(self, cut, *args):
    assert cut in self.cuts, "Did not find cut '%s'! Choose from %s"%(cut,self.cuts)
    index = self.cuts[cut]
    self.hist.Fill(index,*args)
  