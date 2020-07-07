# TauFW Plotter

### Table of Contents  
* [Installation](#Installation)<br>
* [Basic plots](#Basic-plots)<br>
  * [Histogram comparison](#Histogram-comparison)<br>
  * [Data-MC comparison](#Data-MC-comparison)<br>
  * [CMS style](#CMS-style)<br>
* [Variable](#Variable)<br>
* [Sample](#Sample)<br>
  * [Sample style](#Sample-style)<br>
* [Sample set](#Sample-set)<br>
* [Data-driven methods](#Data-driven-methods)<br>


## Installation
See [the README.md in the parent directory](../../../#TauFW).


## Basic plots

### Histogram comparison
Some classes are provided to facilitate making plots in CMS style.
If you have a list of histograms, `hists`, you want to compare with a ratio plot,
use the [`Plot`](python/plot/Plot.py) class, e.g.
```
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
CMSStyle.setCMSEra(2018)
plot = Plot("x",hists)
plot.draw(ratio=True,grid=True,logy=True)
plot.drawlegend()
plot.saveas("plot.png")
plots.close()
```

<p align="center" vertical-align: middle>
  <img src="../docs/testHists.png" alt="Gaussians with Plot class" width="420" hspace="20"/>
  <img src="../docs/testHists_ratio_logy.png" alt="Gaussians with Plot class and ratio plot" width="420"/>
</p>

### Data-MC comparison
If you want to make a data-MC comparison between a data histogram `datahist` and
a list of expected SM processes, `exphists`,
you can use the [`Stack`](python/plot/Stack.py) class, with something like
```
from TauFW.Plotter.plot.Stack import Stack, CMSStyle
CMSStyle.setCMSEra(2018)
plot = Stack("p_{T} [GeV]",datahist,exphists)
plot.draw(ratio=True,logy=False)
plot.drawlegend(pos='right')
plot.drawtext("#mu#tau_{h} baseline")
plot.saveas("stack.png")
plot.saveas("stack.pdf")
plots.close()
```

More examples of usage of `Plot` and `Stack` are provided in [`test/`](test/), run as
```
test/plotHists.py -v2
test/plotStacks.py -v2
```

<p align="center">
  <img src="../docs/testStacks_m_vis_ratio.png" alt="Data-MC with Stack class" width="420" hspace="20"/>
  <img src="../docs/testStacks_njets_ratio_logy.png" alt="Data-MC comparison with Stack class" width="420"/>
</p>


### CMS style
[`CMSStyle.py`](python/plot/CMSStyle.py) provides tools to make a plot have the CMS style.
The luminosity and center-of-mass energy are automatically set for a given year,
```
CMSStyle.setCMSEra(2018)
```
but can be manually set as
```
CMSStyle.setCMSEra(2018,lumi=59.7,cme=13,extra="Preliminary")
```


## Variable
A [`Variable`](python/plot/Variable.py) class is provided to contain variable name (e.g. `pt_1`),
title (e.g. `Leading p_{T} [GeV]`) and the binning (`nbins,xmin,xmax` or a list of bins edges), for example:
```
from TauFW.Plotter.plot.Variable import Variable
variables = [
  Variable('pt_1',  "p_{T} [GeV]",   40, 0,200),
  Variable('m_vis', "m_{vis} [GeV]", [0,20,40,50,60,65,70,75,80,85,90,100,120,150]),
  Variable('njets', "Number of jets", 8, 0,  8),
]
```
A `Variable` object can contain a lot of information, passed as key-word arguments that are
useful when making plots (e.g. `ymin`, `ymax`, `logx`, `logy`, `ymargin`, ...)
or selection strings (e.g. `cut`, `blind`, `weight`, ...).
It also has several handy functions that provide shortcuts for common routines.
For example, `Variable.gethist` can create a histogram for you:
```
hist = var.gethist()
```
and `Variable.drawcmd` can parse a draw command for [`TTree::Draw`](https://root.cern.ch/doc/master/classTTree.html#a73450649dc6e54b5b94516c468523e45):
```
var  = Variable('pt_1',40,0,200)
hist = var.gethist('hist') # returns a TH1D
dcmd = var.drawcmd('hist') # returns a string, e.g. "pt_1 >> hist"
tree.Draw(dcmd)            # loops over tree events and fills the histogram 'hist'
```
It can also be used to initialize a `Plot` or `Stack` object, e.g.
```
var  = Variable('pt_1',40,0,200,logy=True,ymargin=1.4)
plot = Plot(var,hists)
```
Examples are provided in [`test/testVariables.py`](test/testVariables.py).


## Sample
A [`Sample`](python/sample/Sample.py) class is provided to contain a sample' information,
like title (for legends), filename, cross section, normalization, etc.
To initialize, you need to pass a unique name, a title (for legends) and a filename:
```
sample = Sample("TT,"t#bar{t}","TT_mutau.root",831.76)
```
The fourth argument can be a float that will be used to compute the normalization to
the integrated luminosity times cross section. The total number of events will automatically
be taken from the [`'cutflow'` histogram](../PicoProducer/python/analysis/#Cutflow) if it exists,
otherwise pass it with `nevts` (total, raw number of MC events) or `sumw` (sum of generator weights).
```
sample = Sample("TT,"t#bar{t}","TT_mutau.root",831.76,nevts=76915549,lumi=59.7)
```
Instead of passing the integrated luminosity with `lumi` to `Sample`, you can set it globally
(in [`python/sample/utils.py`](python/sample/utils.py)) by passing the era like this:
```
from TauFW.Plotter.sample.utils as setera
setera(2018)
```
This will also immediately set the era for plots via `CMSStyle`. To set the era manually,
directly edit the dictionary `lumi_dict` in the `python/sample/utils.py`, or use
```
setera(2018,59.7)
```

`Sample` provides a useful method that can create and fill a histogram (`TH1D`) for some variable.
It can be called in several ways:
```
var  = Variable('m_vis',40,0,200)
hist = sample.gethist('m_vis',40,0,200,"pt_1>30 && pt_2>30")
hist = sample.gethist('m_vis',[0,40,50,60,70,90,100,120,200],"pt_1>30 && pt_2>30")
hist = sample.gethist(var,"pt_1>30 && pt_2>30")
```
To speed up things, it can create histograms in parallel with [`MultiDraw`](python/plot/MultiDraw.py):
```
hists = sample.gethist(vars,"pt_1>30 && pt_2>30")
```
where `vars` is a list of variables as above, and the returned `hists` is a list of `TH1D`s.
Similarly, `Sample.gethist2D` is available for 2D histograms (`TH2D`).

You can also split samples into different components (like real/misidentified or decay mode)
based on some cuts. e.g.
```
sample.split(('ZTT',"Real tau","genmatch_2==5"),
             ('ZJ', "Fake tau","genmatch_2!=5"))
hists = { }
for subsample in sample.splitsamples:
  hists[subsample] = subsample.gethist(vars,"pt_1>50")
```
Examples are provided in [`test/testSamples.py`](test/testSamples.py):
```
test/testSamples.py -v2
```

### Sample style
The color and title style is predefined by dictionaries in [`python/sample/SampleStyle.py`](python/sample/SampleStyle.py).
These dictionaries are used to automatically set the color for `Sample` object if none is passed.
You can change the colors to your preference as
```
from TauFW.Plotter.sample.SampleStyle as STYLE
STYLE.sample_colors['ZTT'] = kOrange-4
```

<p align="center">
  <img src="../docs/testStyle_legend.png" alt="Legend with common SM processes" width="220" hspace="10"/>
  <img src="../docs/testStyle_legend_split.png" alt="Legend with some processes split" width="220" hspace="10"/>
  <img src="../docs/testStyle_legend_DMs.png" alt="Legend with Z -> tautau split into decay modes" width="200"/>
</p>



## Sample set
The [`SampleSet`](python/sample/SampleSet.py) class helps to contain data and MC samples:
```
from TauFW.Plotter.sample.SampleSet import SampleSet
samples = SampleSet(datasample,expsamples)
samples.printtable()
```
It can create and fill histograms for you:
```
result = samples.gethists(var,selection)
print result.var                 # Variable
print result.data                # TH1D
print result.exp                 # list of TH1Ds
var, datahist, exphists = result # Variable, TH1D, list
```
Or with `MultiDraw` for many variables:
```
result = samples.gethists(vars,selection)
print result.vars                # list of Variable
print result.data                # dictionary of Variable object to TH1D
print result.exp                 # dictionary of Variable object to list of TH1Ds
for var, datahist, exphists in result:
  print var, datahist, exphists  # Variable, TH1D, list
```
Here, `result` is a [`HistSet`](python/sample/HistSet.py) object, which contains a list of `Variable` objects,
and dictionaries for data and MC histograms.

Alternatively, you can immediately prepare the histograms into a `Stack` plot:
```
stacks = samples.getstack(variables,selection)
for stack in stacks:
  stack.draw()
  stack.drawlegend()
  stack.saveas()
  stack.close()
```
Examples are provided in `test/testSamples.py`.

## Data-driven methods
[To be added: data-driven background methods like QCD.]

