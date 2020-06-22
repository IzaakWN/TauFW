# Author: Izaak Neutelings (January 2019)
# Sources:
#   https://twiki.cern.ch/twiki/bin/view/CMS/BTagSFMethods
#   https://twiki.cern.ch/twiki/bin/view/CMSPublic/BTagCalibration
#   https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation#Recommendation_for_13_TeV_Data
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation94X
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
#   nanoAOD-tools/python/postprocessing/modules/btv/btagSFProducer.py
#   https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/modules/btv/btagSFProducer.py
import os
from array import array
import ROOT
#ROOT.gROOT.ProcessLine('.L ./BTagCalibrationStandalone.cpp+')
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.tools.file import ensureTFile
from TauFW.PicoProducer.tools.log import Logger
from ROOT import TH2F, BTagCalibration, BTagCalibrationReader
from ROOT.BTagEntry import OP_LOOSE, OP_MEDIUM, OP_TIGHT, OP_RESHAPING
from ROOT.BTagEntry import FLAV_B, FLAV_C, FLAV_UDSG
datadir = os.path.join(datadir,"btag")
LOG     = Logger('BTagTool',showname=True)


class BTagWPs:
  """Contain b tagging working points."""
  def __init__( self, tagger, year=2017 ):
    assert( year in [2016,2017,2018] ), "You must choose a year from: 2016, 2017, or 2018."
    if year==2016:
      if 'deep' in tagger.lower():
        self.loose    = 0.2217 # 0.2219 for 2016ReReco vs. 2016Legacy
        self.medium   = 0.6321 # 0.6324
        self.tight    = 0.8953 # 0.8958
      else:
        self.loose    = 0.5426 # for 80X ReReco
        self.medium   = 0.8484
        self.tight    = 0.9535
    elif year==2017:
      if 'deep' in tagger.lower():
        self.loose    = 0.1522 # for 94X
        self.medium   = 0.4941
        self.tight    = 0.8001
      else:
        self.loose    = 0.5803 # for 94X
        self.medium   = 0.8838
        self.tight    = 0.9693
    elif year==2018:
      if 'deep' in tagger.lower():
        self.loose    = 0.1241 # for 102X
        self.medium   = 0.4184
        self.tight    = 0.7527
      else:
        self.loose    = 0.5803 # for 94X
        self.medium   = 0.8838
        self.tight    = 0.9693
        

class BTagWeightTool:
  
  def __init__(self, tagger, wp='medium', channel='mutau', year=2017, maxeta=2.4, loadsys=False, type_bc='comb'):
    """Load b tag weights from CSV file."""
    
    assert(year in [2016,2017,2018]), "You must choose a year from: 2016, 2017, or 2018."
    assert(tagger in ['CSVv2','DeepCSV']), "BTagWeightTool: You must choose a tagger from: CSVv2, DeepCSV!"
    assert(wp in ['loose','medium','tight']), "BTagWeightTool: You must choose a WP from: loose, medium, tight!"
    #assert(sigma in ['central','up','down']), "BTagWeightTool: You must choose a WP from: central, up, down!"
    #assert(channel in ['mutau','eletau','tautau','mumu']), "BTagWeightTool: You must choose a channel from: mutau, eletau, tautau, mumu!"
    
    # FILE
    if year==2016:
      if 'deep' in tagger.lower():
        csvname = os.path.join(datadir,'DeepCSV_Moriond17_B_H.csv')
        effname = os.path.join(datadir,'DeepCSV_2016_Moriond17_eff.root')
      else:
        csvname = os.path.join(datadir,'CSVv2_Moriond17_B_H.csv')
        effname = os.path.join(datadir,'CSVv2_2016_Moriond17_eff.root')
    elif year==2017:
      if 'deep' in tagger.lower():
        csvname = os.path.join(datadir,'DeepCSV_94XSF_V3_B_F.csv')
        effname = os.path.join(datadir,'DeepCSV_2017_12Apr2017_eff.root')
      else:
        csvname = os.path.join(datadir,'CSVv2_94XSF_V2_B_F.csv')
        effname = os.path.join(datadir,'CSVv2_2017_12Apr2017_eff.root')
    elif year==2018:
      if 'deep' in tagger.lower():
        csvname = os.path.join(datadir,'DeepCSV_94XSF_V3_B_F.csv')
        effname = os.path.join(datadir,'DeepCSV_2018_Autumn18_eff.root')
      else:
        csvname = os.path.join(datadir,'CSVv2_94XSF_V2_B_F.csv')
        effname = os.path.join(datadir,'CSVv2_2018_Autumn18_eff.root')
    
    # TAGGING WP
    self.wpname = wp
    self.wp     = getattr(BTagWPs(tagger,year),wp)
    if 'deep' in tagger.lower():
      tagged = lambda j: j.btagDeepB>self.wp
    else:
      tagged = lambda j: j.btagCSVV2>self.wp
    
    # CSV READER
    print "Loading BTagWeightTool for %s (%s WP)..."%(tagger,wp) #,(", "+sigma) if sigma!='central' else ""
    readers        = { }
    op             = OP_LOOSE if wp=='loose' else OP_MEDIUM if wp=='medium' else OP_TIGHT if wp=='tight' else OP_RESHAPING
    type_udsg      = 'incl'
    type_bc        = type_bc # 'mujets' for QCD; 'comb' for QCD+TT
    calib          = BTagCalibration(tagger, csvname)
    readers['Nom'] = BTagCalibrationReader(op,'central')
    if loadsys:
      readers['Up']   = BTagCalibrationReader(op,'up')
      readers['Down'] = BTagCalibrationReader(op,'down')
    for reader in readers.values():
      reader.load(calib,FLAV_B,   type_bc)
      reader.load(calib,FLAV_C,   type_bc)
      reader.load(calib,FLAV_UDSG,type_udsg)
    
    # EFFICIENCIES
    hists      = { } # histograms to compute the b tagging efficiencies in MC
    effmaps    = { } # b tag efficiencies in MC to compute b tagging weight for an event
    efffile    = ensureTFile(effname)
    default    = False
    if not efffile:
      LOG.warning("File %s with efficiency histograms does not exist! Reverting to default efficiency histogram..."%(effname))
      default  = True
    for flavor in [0,4,5]:
      flavor   = flavorToString(flavor)
      histname = "%s_%s_%s"%(tagger,flavor,wp)
      effname  = "%s/eff_%s_%s_%s"%(channel,tagger,flavor,wp)
      hists[flavor]        = getEffMap(histname)        # numerator   = b tagged jets
      hists[flavor+'_all'] = getEffMap(histname+'_all') # denominator = all jets
      if efffile:
        effmaps[flavor]    = efffile.Get(effname)
        if not effmaps[flavor]:
          LOG.warning("Histogram '%s' does not exist in %s! Reverting to default efficiency histogram..."%(effname,efffile.GetName()))
          default          = True
          effmaps[flavor]  = getDefaultEffMap(effname,flavor,wp)
      else:
        effmaps[flavor]    = getDefaultEffMap(effname,flavor,wp)
      effmaps[flavor].SetDirectory(0)
    efffile.Close()
    
    if default:
      LOG.warning("Made use of default efficiency histograms! The b tag weights from this module should be regarded as placeholders only,\n"+\
                  "and should NOT be used for analyses. B (mis)tag efficiencies in MC are analysis dependent. Please create your own\n"+\
                  "efficiency histogram with data/btag/getBTagEfficiencies.py after running all MC samples with BTagWeightTool.")
    
    self.tagged  = tagged
    self.calib   = calib
    self.readers = readers
    self.loadsys = loadsys
    self.hists   = hists
    self.effmaps = effmaps
    self.maxeta  = maxeta
  
  def getWeight(self,jets,unc='Nom'):
    """Get b tagging event weight for a given set of jets."""
    weight = 1.
    for jet in jets:
      if abs(jet.eta)<self.maxeta:
        weight *= self.getSF(jet.pt,jet.eta,jet.partonFlavour,self.tagged(jet),unc=unc)
    return weight
  
  def getSF(self,pt,eta,flavor,tagged,unc='Nom'):
    """Get b tag SF for a single jet."""
    FLAV = flavorToFLAV(flavor)
    if   eta>=+2.4: eta = +2.399 # BTagCalibrationReader returns zero if |eta| > 2.4
    elif eta<=-2.4: eta = -2.399
    sf   = self.readers[unc].eval(FLAV,abs(eta),pt) #eval_auto_bounds
    if tagged:
      weight = sf
    else:
      eff = self.getEff(pt,eta,flavor)
      if eff==1:
        LOG.warning("BTagWeightTool.getSF: MC efficiency is 1 for pt=%s, eta=%s, flavor=%s, sf=%s"%(pt,eta,flavor,sf))
        return 1.
      else:
        weight = (1.-sf*eff)/(1.-eff)
    return weight
  
  def getEff(self,pt,eta,flavor):
    """Get b tag efficiency for a single jet in MC."""
    flavor = flavorToString(flavor)
    hist   = self.effmaps[flavor]
    xbin   = hist.GetXaxis().FindBin(pt)
    ybin   = hist.GetYaxis().FindBin(eta)
    if xbin==0: xbin = 1
    elif xbin>hist.GetXaxis().GetNbins(): xbin -= 1
    if ybin==0: ybin = 1
    elif ybin>hist.GetYaxis().GetNbins(): ybin -= 1
    eff    = hist.GetBinContent(xbin,ybin)
    ###if eff==1:
    ###  print "Warning! BTagWeightTool.getEff: MC efficiency is 1 for pt=%s, eta=%s, flavor=%s, sf=%s"%(pt,eta,flavor,sf)
    return eff
  
  def fillEffMaps(self,jets,usejec=False):
    """Fill histograms to make efficiency map for MC, split by true jet flavor,
    and jet pT and eta. Numerator = b tagged jets; denominator = all jets."""
    for jet in jets:
      jetpt  = jet.pt_nom if usejec else jet.pt
      flavor = flavorToString(jet.partonFlavour)
      if self.tagged(jet):
        self.hists[flavor].Fill(jetpt,jet.eta)
      self.hists[flavor+'_all'].Fill(jetpt,jet.eta)
  
  def setDir(self,directory,subdirname=None):
    """Set directory of histograms (efficiency map) before writing."""
    if subdirname:
      subdir = directory.Get(subdirname)
      if not subdir:
        subdir = directory.mkdir(subdirname)
      directory = subdir
    for histname, hist in self.hists.iteritems():
      hist.SetDirectory(directory)
  

def flavorToFLAV(flavor):
  """Help function to convert an integer flavor ID to a BTagEntry enum value."""
  return FLAV_B if abs(flavor)==5 else FLAV_C if abs(flavor) in [4,15] else FLAV_UDSG       
  

def flavorToString(flavor):
  """Help function to convert an integer flavor ID to a string value."""
  return 'b' if abs(flavor)==5 else 'c' if abs(flavor)==4 else 'udsg'
  

def getEffMap(histname):
  """Help function to create efficiency maps (TH2D) with uniform binning and layout.
  One method to rule them all."""
  ptbins  = array('d',[10,20,30,50,70,100,140,200,300,500,1000,1500])
  etabins = array('d',[-2.7,-1.5,0.0,1.5,2.7])
  bins    = (len(ptbins)-1,ptbins,len(etabins)-1,etabins)
  hist    = TH2F(histname,histname,*bins)
  hist.GetXaxis().SetTitle("Jet p_{T} [GeV]")
  hist.GetYaxis().SetTitle("Jet #eta")
  hist.SetDirectory(0)
  return hist
  

def getDefaultEffMap(histname,flavor,wp='medium'):
  """Create default efficiency histograms. WARNING! Do not use this for analysis! Use it as a placeholder,
  until you have made an efficiency map from MC for you analysis."""
  if   wp=='loose':  eff = 0.75 if flavor=='b' else 0.11 if flavor=='c' else 0.01
  elif wp=='medium': eff = 0.85 if flavor=='b' else 0.42 if flavor=='c' else 0.10
  else:              eff = 0.60 if flavor=='b' else 0.05 if flavor=='c' else 0.001
  histname = histname.split('/')[-1] + "_default"
  hist     = getEffMap(histname)
  for xbin in xrange(0,hist.GetXaxis().GetNbins()+2):
    for ybin in xrange(0,hist.GetYaxis().GetNbins()+2):
      hist.SetBinContent(xbin,ybin,eff)
  return hist
  
