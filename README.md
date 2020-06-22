# TauFW

Framework for tau analysis using NanoAOD at CMS. Three main packages are
1. [`PicoProducer`](PicoProducer): Tools to process nanoAOD.
2. [`Plotter`](Plotter): Tools for analysis and plotting.
3. [`Fitter`](Fitter): Tools for measurements and fits in combine.

## Installation

First, install [`NanoAODTools`](https://github.com/cms-nanoAOD/nanoAOD-tools):
```
export SCRAM_ARCH=slc6_amd64_gcc700
cmsrel CMSSW_10_3_3
cd CMSSW_10_3_3/src
cmsenv
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b
```

Then, install `TauFW`:
```
cd $CMSSW_BASE/src/
git clone https://github.com/cms-tau-pog/TauFW TauFW
scram b
```