#! /usr/bin/env python
# Author: Izaak Neutelings (January 2019)

import os, sys
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gROOT, gStyle, gPad, gDirectory, TFile, TTree, TH2F, TCanvas, TLegend, TLatex, kBlue, kRed, kOrange
gStyle.SetOptStat(False)
gROOT.SetBatch(True)

argv = sys.argv
description = '''This script extracts histograms from the analysis framework output run on MC samples to create b tag efficiencies.'''
parser = ArgumentParser(prog="pileup",description=description,epilog="Succes!")
parser.add_argument('-y', '--year',    dest='years', choices=[2016,2017,2018], type=int, nargs='+', default=[2017], action='store',
                                       help="year to run" )
parser.add_argument('-c', '--channel', dest='channels', choices=['eletau','mutau','tautau','elemu','mumu','eleele'], type=str, nargs='+', default=['mutau'], action='store',
                                       help="channels to run" )
parser.add_argument('-t', '--tagger',  dest='taggers', choices=['CSVv2','DeepCSV'], type=str, nargs='+', default=['DeepCSV'], action='store',
                                       help="tagger to run" )
parser.add_argument('-w', '--wp',      dest='wps', choices=['loose','medium','tight'], type=str, nargs='+', default=['medium'], action='store',
                                       help="working point to run" )
parser.add_argument('-p', '--plot',    dest="plot", default=False, action='store_true', 
                                       help="plot efficiencies" )
parser.add_argument('-v', '--verbose', dest="verbose", default=False, action='store_true', 
                                       help="print verbose" )
args = parser.parse_args()



def getBTagEfficiencies(tagger,wp,outfilename,samples,year,channel,plot=False):
    """Get pileup profile in MC by adding Pileup_nTrueInt histograms from a given list of samples."""
    print '>>> getBTagEfficiencies("%s")'%(outfilename)
    
    # PREPARE numerator and denominator histograms per flavor
    nhists  = { }
    hists   = { }
    histdir = 'btag'
    for flavor in ['b','c','udsg']:
      histname = '%s_%s_%s'%(tagger,flavor,wp)
      hists[histname] = None        # numerator
      hists[histname+'_all'] = None # denominator
    
    # ADD numerator and denominator histograms
    for filename in samples:
      print ">>>   %s"%(filename)
      file = TFile(filename,'READ')
      if not file or file.IsZombie():
        print ">>>   Warning! getBTagEfficiencies: Could not open %s. Ignoring..."%(filename)
        continue
      for histname in hists:
        histpath = "%s/%s"%(histdir,histname)
        hist = file.Get(histpath)
        if not hist:
          print ">>>   Warning! getBTagEfficiencies: Could not open histogram '%s' in %s. Ignoring..."%(histpath,filename)        
          dir = file.Get(histdir)
          if dir: dir.ls()
          continue
        if hists[histname]==None:
          hists[histname] = hist.Clone(histname)
          hists[histname].SetDirectory(0)
          nhists[histname] = 1
        else:
          hists[histname].Add(hist)
          nhists[histname] += 1
      file.Close()
    
    # CHECK
    if len(nhists)>0:
      print ">>>   added %d MC hists:"%(sum(nhists[n] for n in nhists))
      for histname, nhist in nhists.iteritems():
        print ">>>     %-26s%2d"%(histname+':',nhist)
    else:
      print ">>>   no histograms added !"
      return
    
    # DIVIDE and SAVE histograms
    print ">>>   writing to %s..."%(outfilename)
    file = TFile(outfilename,'UPDATE') #RECREATE
    ensureTDirectory(file,channel)
    for histname, hist in hists.iteritems():
      if 'all' in histname:
        continue
      histname_all = histname+'_all'
      histname_eff = 'eff_'+histname
      print ">>>     writing %s..."%(histname)
      print ">>>     writing %s..."%(histname_all)
      print ">>>     writing %s..."%(histname_eff)
      hist_all = hists[histname_all]
      hist_eff = hist.Clone(histname_eff)
      hist_eff.SetTitle(makeTitle(tagger,wp,histname_eff,channel,year))
      hist_eff.Divide(hist_all)
      hist.Write(histname,TH2F.kOverwrite)
      hist_all.Write(histname_all,TH2F.kOverwrite)
      hist_eff.Write(histname_eff,TH2F.kOverwrite)
      if plot:
        plot1D(histname_eff+"_vs_pt",hist,hist_all,year,channel,title=hist_eff.GetTitle(),log=True)
        plot2D(histname_eff,hist_eff,year,channel,log=True)
        plot2D(histname_eff,hist_eff,year,channel,log=False)
    file.Close()
    print ">>> "
  

def plot2D(histname,hist,year,channel,log=False):
    """Plot 2D efficiency."""
    dir    = ensureDirectory('plots/%d'%year)
    name   = "%s/%s_%s"%(dir,histname,channel)
    if log:
      name += "_log"
    xtitle = 'jet p_{T} [GeV]'
    ytitle = 'jet #eta'
    ztitle = 'b tag efficiencies' if '_b_' in histname else 'b mistag rate'
    xmin, xmax = 20, hist.GetXaxis().GetXmax()
    zmin, zmax = 5e-3 if log else 0.0, 1.0
    angle  = 22 if log else 77
    
    canvas = TCanvas('canvas','canvas',100,100,800,700)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.13 )
    canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.17 )
    canvas.SetTickx(0); canvas.SetTicky(0)
    canvas.SetGrid()
    gStyle.SetOptTitle(0) #FontSize(0.04)
    if log:
      canvas.SetLogx()
      canvas.SetLogz()
    canvas.cd()
    
    hist.GetXaxis().SetTitle(xtitle)
    hist.GetYaxis().SetTitle(ytitle)
    hist.GetZaxis().SetTitle(ztitle)
    hist.GetXaxis().SetLabelSize(0.048)
    hist.GetYaxis().SetLabelSize(0.048)
    hist.GetZaxis().SetLabelSize(0.048)
    hist.GetXaxis().SetTitleSize(0.058)
    hist.GetYaxis().SetTitleSize(0.058)
    hist.GetZaxis().SetTitleSize(0.056)
    hist.GetXaxis().SetTitleOffset(1.03)
    hist.GetYaxis().SetTitleOffset(1.04)
    hist.GetZaxis().SetTitleOffset(1.03)
    hist.GetXaxis().SetLabelOffset(-0.004 if log else 0.005)
    hist.GetZaxis().SetLabelOffset(-0.005 if log else 0.005)
    hist.GetXaxis().SetRangeUser(xmin,xmax)
    hist.SetMinimum(zmin)
    hist.SetMaximum(zmax)
    hist.Draw('COLZTEXT%d'%angle)
    
    gStyle.SetPaintTextFormat('.2f')
    hist.SetMarkerColor(kRed)
    hist.SetMarkerSize(1.8 if log else 1)
    #gPad.Update()
    #gPad.RedrawAxis()
    
    latex = TLatex()
    latex.SetTextSize(0.048)
    latex.SetTextAlign(23)
    latex.SetTextFont(42)
    latex.SetNDC(True)
    latex.DrawLatex(0.475,0.99,hist.GetTitle()) # to prevent typesetting issues
    
    canvas.SaveAs(name+'.pdf')
    canvas.SaveAs(name+'.png')
    canvas.Close()
    

def plot1D(histname,histnum2D,histden2D,year,channel,title="",log=False):
    """Plot efficiency."""
    dir      = ensureDirectory('plots/%d'%year)
    name     = "%s/%s_%s"%(dir,histname,channel)
    if log:
      name  += "_log"
    header   = ""
    xtitle   = 'jet p_{T} [GeV]'
    ytitle   = 'b tag efficiencies' if '_b_' in histname else 'b mistag rate'
    xmin, xmax = 20 if log else 10, histnum2D.GetXaxis().GetXmax()
    ymin, ymax = 5e-3 if log else 0.0, 2.0
    colors   = [kBlue, kRed, kOrange]
    x1, y1   = (0.27, 0.44) if '_b_' in histname else (0.55, 0.80)
    width, height = 0.3, 0.16
    x2, y2   = x1 + width, y1 - height
    hists    = createEff1D(histnum2D,histden2D)
    
    canvas = TCanvas('canvas','canvas',100,100,800,700)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.04 ); canvas.SetBottomMargin( 0.13 )
    canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.05 )
    canvas.SetTickx(0); canvas.SetTicky(0)
    canvas.SetGrid()
    gStyle.SetOptTitle(0)
    if log:
      canvas.SetLogx()
      canvas.SetLogy()
    canvas.cd()
    
    frame = hists[0]
    for i, hist in enumerate(hists):
      hist.SetLineColor(colors[i%len(colors)])
      hist.SetMarkerColor(colors[i%len(colors)])
      hist.SetLineWidth(2)
      hist.SetMarkerSize(2)
      hist.SetMarkerStyle(1)
      hist.Draw('PE0SAME')
    frame.GetXaxis().SetTitle(xtitle)
    frame.GetYaxis().SetTitle(ytitle)
    frame.GetXaxis().SetLabelSize(0.048)
    frame.GetYaxis().SetLabelSize(0.048)
    frame.GetXaxis().SetTitleSize(0.058)
    frame.GetYaxis().SetTitleSize(0.058)
    frame.GetXaxis().SetTitleOffset(1.03)
    frame.GetYaxis().SetTitleOffset(1.04)
    frame.GetXaxis().SetLabelOffset(-0.004 if log else 0.005)
    frame.GetXaxis().SetRangeUser(xmin,xmax)
    frame.SetMinimum(ymin)
    frame.SetMaximum(ymax)
    
    if title:    
      latex = TLatex()
      latex.SetTextSize(0.04)
      latex.SetTextAlign(13)
      latex.SetTextFont(62)
      latex.SetNDC(True)
      latex.DrawLatex(0.15,0.94,title)
    
    legend = TLegend(x1,y1,x2,y2)
    legend.SetTextSize(0.04)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)
    if header:
      legend.SetTextFont(62)
      legend.SetHeader(header)
    legend.SetTextFont(42)
    for hist in hists:
      legend.AddEntry(hist,hist.GetTitle(),'lep')
    legend.Draw()
    
    canvas.SaveAs(name+'.pdf')
    canvas.SaveAs(name+'.png')
    canvas.Close()
    

def createEff1D(histnum2D,histden2D):
  """Create 1D histogram of efficiency vs. pT for central and forward eta bins."""
  etabins = {
    "|#eta| < 2.5":       [(0,5)],
    "|#eta| < 1.5":       [(2,3)],
    "1.5 < |#eta| < 2.5": [(1,1),(4,4)],
  }
  hists = [ ]
  for etatitle, bins in etabins.iteritems():
    histnum  = None
    histden  = None
    for bin1, bin2 in bins:
      if histnum==None or histden==None:
        histnum  = histnum2D.ProjectionX("%s_%d"%(histnum2D.GetName(),bin1),bin1,bin2)
        histden  = histden2D.ProjectionX("%s_%d"%(histden2D.GetName(),bin1),bin1,bin2)
      else:
        histnum.Add(histnum2D.ProjectionX("%s_%d"%(histnum2D.GetName(),bin1),bin1,bin2))
        histden.Add(histden2D.ProjectionX("%s_%d"%(histden2D.GetName(),bin1),bin1,bin2))
    histnum.Sumw2()
    histnum.Divide(histden)
    histnum.SetTitle(etatitle)
    hists.append(histnum)
    gDirectory.Delete(histden.GetName())
    #for i in xrange(0,histnum.GetXaxis().GetNbins()+1):
    #  print i, histnum.GetBinContent(i)
  return hists
  

def makeTitle(tagger,wp,flavor,channel,year):
  flavor = flavor.replace('_',' ')
  if ' b ' in flavor:
    flavor = 'b quark'
  elif ' c ' in flavor:
    flavor = 'c quark'
  else:
    flavor = 'light-flavor'
  string = "%s, %s %s WP (%s, %d)"%(flavor,tagger,wp,channel.replace('tau',"#tau_{h}").replace('mu',"#mu").replace('ele',"e"),year)
  return string
  

def ensureTDirectory(file,dirname):
  dir = file.GetDirectory(dirname)
  if not dir:
    dir = file.mkdir(dirname)
    print ">>>   created directory %s in %s" % (dirname,file.GetName())
  dir.cd()
  return dir
  

def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
    os.makedirs(dirname)
    print '>>> made directory "%s"'%(dirname)
    if not os.path.exists(dirname):
      print '>>> failed to make directory "%s"'%(dirname)
  return dirname
  

def main():
    
    years    = args.years
    channels = args.channels
    
    
    for year in args.years:
      
      # SAMPLES: list of analysis framework output run on MC samples
      #          that is used to add together and compute the efficiency
      if year==2016:
        samples = [
          ( 'TT', "TT",                   ),
          ( 'DY', "DYJetsToLL_M-10to50",  ),
          ( 'DY', "DYJetsToLL_M-50_reg",  ),
          ( 'DY', "DY1JetsToLL_M-50",     ),
          ( 'DY', "DY2JetsToLL_M-50",     ),
          ( 'DY', "DY3JetsToLL_M-50",     ),
          ( 'WJ', "WJetsToLNu",           ),
          ( 'WJ', "W1JetsToLNu",          ),
          ( 'WJ', "W2JetsToLNu",          ),
          ( 'WJ', "W3JetsToLNu",          ),
          ( 'WJ', "W4JetsToLNu",          ),
          ( 'ST', "ST_tW_top",            ),
          ( 'ST', "ST_tW_antitop",        ),
          ( 'ST', "ST_t-channel_top",     ),
          ( 'ST', "ST_t-channel_antitop", ),
          #( 'ST', "ST_s-channel",         ),
          ( 'VV', "WW",                   ),
          ( 'VV', "WZ",                   ),
          ( 'VV', "ZZ",                   ),
        ]
      elif year==2017:
        samples = [ 
          ( 'TT', "TTTo2L2Nu",            ),
          ( 'TT', "TTToHadronic",         ),
          ( 'TT', "TTToSemiLeptonic",     ),
          ( 'DY', "DYJetsToLL_M-10to50",  ),
          ( 'DY', "DYJetsToLL_M-50",      ),
          ( 'DY', "DY1JetsToLL_M-50",     ),
          ( 'DY', "DY2JetsToLL_M-50",     ),
          ( 'DY', "DY3JetsToLL_M-50",     ),
          ( 'DY', "DY4JetsToLL_M-50",     ),
          ( 'WJ', "WJetsToLNu",           ),
          ( 'WJ', "W1JetsToLNu",          ),
          ( 'WJ', "W2JetsToLNu",          ),
          ( 'WJ', "W3JetsToLNu",          ),
          ( 'WJ', "W4JetsToLNu",          ),
          ( 'ST', "ST_tW_top",            ),
          ( 'ST', "ST_tW_antitop",        ),
          ( 'ST', "ST_t-channel_top",     ),
          ( 'ST', "ST_t-channel_antitop", ),
          #( 'ST', "ST_s-channel",         ),
          ( 'VV', "WW",                   ),
          ( 'VV', "WZ",                   ),
          ( 'VV', "ZZ",                   ),
        ]
      else:
        samples = [
          ( 'TT', "TTTo2L2Nu",            ),
          ( 'TT', "TTToHadronic",         ),
          ( 'TT', "TTToSemiLeptonic",     ),
          ( 'DY', "DYJetsToLL_M-10to50",  ),
          ( 'DY', "DYJetsToLL_M-50",      ),
          ( 'DY', "DY1JetsToLL_M-50",     ),
          ( 'DY', "DY2JetsToLL_M-50",     ),
          ( 'DY', "DY3JetsToLL_M-50",     ),
          ( 'DY', "DY4JetsToLL_M-50",     ),
          #( 'WJ', "WJetsToLNu",           ),
          ( 'WJ', "W1JetsToLNu",          ),
          ( 'WJ', "W2JetsToLNu",          ),
          ( 'WJ', "W3JetsToLNu",          ),
          ( 'WJ', "W4JetsToLNu",          ),
          ( 'ST', "ST_tW_top",            ),
          ( 'ST', "ST_tW_antitop",        ),
          ( 'ST', "ST_t-channel_top",     ),
          ( 'ST', "ST_t-channel_antitop", ),
          #( 'ST', "ST_s-channel",         ),
          ( 'VV', "WW",                   ),
          ( 'VV', "WZ",                   ),
          ( 'VV', "ZZ",                   ),
        ]
      
      # LQ
      if all(c not in args.channels for c in ['mumu','eleele']):
        samples += [
          ( 'LQ', "SLQ_pair_M600",        ),
          ( 'LQ', "SLQ_pair_M800",        ),
          ( 'LQ', "SLQ_pair_M1000",       ),
          ( 'LQ', "SLQ_pair_M1200",       ),
          ( 'LQ', "SLQ_pair_M1400",       ),
          ( 'LQ', "SLQ_pair_M1600",       ),
          ( 'LQ', "SLQ_pair_M2000",       ),
          ( 'LQ', "VLQ_pair_M500",        ),
          ( 'LQ', "VLQ_pair_M800",        ),
          ( 'LQ', "VLQ_pair_M1100",       ),
          ( 'LQ', "VLQ_pair_M1400",       ),
          ( 'LQ', "VLQ_pair_M1700",       ),
          ( 'LQ', "VLQ_pair_M2000",       ),
          ( 'LQ', "VLQ_pair_M2300",       ),
        ]
      
      # MC CAMPAIGN NAMES of each year 
      campaigns = { 2016: "Moriond17", 2017: "12Apr2017", 2018: "Autumn18" }
      
      # LOOP over channels
      for channel in args.channels:
        
        # SAMPLE FILE NAMES
        indir = "/scratch/ineuteli/analysis/LQ_%d"%(year)
        samplefilenames = ["%s/%s/%s_%s.root"%(indir,subdir,samplename,channel) for subdir, samplename in samples]
        
        # COMPUTE and SAVE b tag efficiencies
        for tagger in args.taggers:
          for wp in args.wps:
            outfilename = "%s_%d_%s_eff.root"%(tagger,year,campaigns[year])
            getBTagEfficiencies(tagger,wp,outfilename,samplefilenames,year,channel,plot=args.plot)
    


if __name__ == '__main__':
    print
    main()
    print ">>> done\n"
    

