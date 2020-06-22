#! /bin/bash
# dasgoclient -query="dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017RECOSIMstep_12Apr2018_v1-DeepTauv2p1_TauPOG-v1/USER instance=prod/phys03"

MCSAMPLES="
  DY*JetsToLL_M-10to50_TuneC*_13TeV-madgraphMLM-pythia8
  DY*JetsToLL_M-50_TuneC*_13TeV-madgraphMLM-pythia8
  W*JetsToLNu_TuneC*madgraph*
  TT_TuneCUETP8M2T4_13TeV-powheg-pythia8
  TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8
  TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8
  TTToHadronic_TuneCP5_13TeV-powheg-pythia8
  ST_tW_*top_5f_inclusiveDecays_TuneC*
  ST_t-channel_*top_4f_InclusiveDecays_TuneC*
  WZ_TuneC*
  WW_TuneC*
  ZZ_TuneC*
"
DATASETS="SingleMuon SingleElectron EGamma Tau"
MCYEARS="Summer16 Fall17 Autumn18"
DATAYEARS="2016 2017 2018" # Run2018D"
MCCAMP='NanoAODv6'
DATACAMP='25Oct2019'
YEAR=0
NFILES=2

while getopts e:d:m:n:y: option; do case "${option}" in
  d) DATASETS=${OPTARG//,/ };;
  e) DATAYEARS=${OPTARG//,/ };; # eras
  m) MCSAMPLES=${OPTARG//,/ };;
  n) NFILES=${OPTARG};;
  y) YEAR=${OPTARG};;
esac; done

# MC
for dataset in $MCSAMPLES; do
  for year in $MCYEARS; do
    [[ $YEAR -gt 0 ]] && [[ $year != *$YEAR ]] && continue
    [[ $dataset = "TT_TuneC"* ]] && [[ $year != *16 ]] && continue
    [[ $dataset = "TTTo"*"_TuneCP5"* ]] && [[ $year = *16 ]] && continue
    pattern="/$dataset/RunII${year}*${MCCAMP}*/NANOAODSIM"
    echo
    echo -e "\e[1m\e[32m$pattern\e[0m"
    for daspath in `dasgoclient -query="dataset=$pattern"`; do
      echo "$daspath"
    done
  done
done

# DATA
for dataset in $DATASETS; do
  for year in $DATAYEARS; do
    [[ $YEAR -gt 0 ]] && [[ "$year"* != *"$YEAR"* ]] && continue
    [[ $dataset = "EGamma" ]] && [[ $year != 2018* ]] && continue
    [[ $dataset = "SingleElectron" ]] && [[ $year = 2018* ]] && continue
    pattern="/$dataset/Run$year*${DATACAMP}*/NANOAOD"
    echo
    echo -e "\e[1m\e[32m$pattern\e[0m"
    for daspath in `dasgoclient -query="dataset=$pattern"`; do
      echo "$daspath"
    done
  done
done

echo
