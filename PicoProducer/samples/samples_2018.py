from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/user/i/ineuteli/samples/nano/$ERA/$PATH"
url      = None #"root://cms-xrd-global.cern.ch/"
filelist = None #"samples/files/2016/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY1JetsToLL_M-50',
   "/DY1JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
   store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY2JetsToLL_M-50',
   "/DY2JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
   store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY3JetsToLL_M-50',
   "/DY3JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
   store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY4JetsToLL_M-50',
   "/DY4JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
   store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  M('TT','TTToSemiLeptonic',
    "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20_ext3-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  M('TT','TTToHadronic',
    "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v3/NANOAODSIM",
    "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20_ext2-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2018A', "/SingleMuon/Run2018A-Nano25Oct2019-v1/NANOAOD",
   store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  D('Data','SingleMuon_Run2018B', "/SingleMuon/Run2018B-Nano25Oct2019-v1/NANOAOD",
    store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  D('Data','SingleMuon_Run2018C', "/SingleMuon/Run2018C-Nano25Oct2019-v1/NANOAOD",
   store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  D('Data','SingleMuon_Run2018D', "/SingleMuon/Run2018D-Nano25Oct2019_ver2-v1/NANOAOD",
   store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  
]