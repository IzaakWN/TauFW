# PicoProducer

This setup runs the [post-processors](https://github.com/cms-nanoAOD/nanoAOD-tools) on nanoAOD.
There are two modes:
1. **Skimming**: Skim nanoAOD by removing [unneeded branches](https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/processors/keep_and_drop_skim.txt),
                 bad data events (using [data certification JSONs](data/json)),
                 add things like JetMET corrections. Output still has a nanoAOD format.
                 This step is optional, but allows you to run your analysis faster.
2. **Analysis**: Analyze nanoAOD events by pre-selecting events and objects and constructing variables.
                 The main analysis code is found in [`python/analysis/`](python/analysis).
                 The output is a custom tree format we will refer to as _pico_.

A central script called [`pico.py`](scripts/pico.py) allows you to run both modes of nanoAOD processing,
either locally or on a batch system.
You can link several skimming or analysis codes to _channels_.

<img src="../docs/PicoProducer_workflow.png" alt="TauFW PicoProducer workflow" max-width="800"/>


### Table of Contents  
* [Installation](#Installation)<br>
* [Configuration](#Configuration)<br>
  * [Skimming](#Skimming)
  * [Analysis](#Analysis)
  * [Sample list](#Sample-list)
* [Samples](#Samples)<br>
* [Local run](#Local-run)<br>
* [Batch submission](#Batch-submission)<br>
  * [Submission](#Submission)
  * [Resubmission](#Resubmission)
  * [Finalize](#Finalize)
* [Plug-ins](#Plug-ins)<br>
  * [Batch system](#Batch-system)
  * [Storage system](#Storage-system)
  * [Analysis module](#Analysis-module)

## Installation

You need to have CMSSW and [NanoAODTools](https://github.com/cms-nanoAOD/nanoAOD-tools) installed,
see the [README in the parent directory](../../../#taufw). Test the installation with
```
pico.py --help
```
If CMSSW is compiled correctly with `scram b`, then the `pico.py` script should have been
automatically copied from `scripts/` to `$CMSSW_BASE/bin/$SCRAM_ARCH`,
and should be available as a command via `$PATH`.

If you need to access DAS for getting file lists of nanoAOD samples,
make sure you have a GRID certificate installed, and a VOMS proxy setup
```
voms-proxy-init -voms cms -valid 200:0
```
or use the script
```
source utils/setupVOMS.sh
```


## Configuration

The user configuration is saved in [`config/config.json`](config/config.json). Check the contents with `cat`, or use
```
pico.py list
```
You can manually edit the file, or set some variable with
<pre>
pico.py set <i>&lt;variables&gt; &lt;value&gt;</i>
</pre>
For example:
```
pico.py set batch HTCondor
pico.py set jobdir 'output/$ERA/$CHANNEL/$SAMPLE'
```
The configurable variables include:
* `batch`: Batch system to use (e.g. `HTCondor`).
* `jobdir`: Directory to output job configuration and log files (e.g. `output/$ERA/$CHANNEL/$SAMPLE`).
* `outdir`: Directory to copy the output pico files from analysis jobs.
* `nanodir`: Directory to store the output nanoAOD files from skimming jobs (e.g. on EOS, T2, T3, ...).
* `picodir`: Directory to store the `hadd`'ed pico file from analysis job output (e.g. on EOS, T2, T3, ...).
* `nfilesperjob`: Default number of files per job. This can be overridden per sample (see below).
* `filelistdir`: Directory to save list of nanoAOD files to run on (e.g. `samples/files/$ERA/$SAMPLE.txt`).

Defaults are given in [`config/config.json`](config/config.json).
Note the directories can contain variables with `$` like
`$ERA`, `$CHANNEL`, `$CHANNEL`, `$TAG`, `$SAMPLE`, `$GROUP` and `$PATH`
to create a custom hierarchy and format.

Besides these variables, there are also dictionaries to link a channel short name to a skimming or analysis code,
or an era (year) to a list of samples.

### Skimming
Skimming of nanoAOD files is done by post-processor scripts saved in [`python/processors/`](python/processors).
An example is given by [`skimjob.py`](python/processors/skimjob.py).

You can link your skimming script to a custom channel short name
```
pico.py channel skim skimjob.py
```
This can be whatever string you want, but it should be unique, contain `skim` to differentiate from analysis channels,
and you should avoid characters that are not safe for filenames, including `_`, `-`, `:` and `/`.


### Analysis
This framework allows to implement many analysis modules called channels
(e.g. different final states like mutau or etau).
All analysis code should be saved in [`python/analysis/`](python/analysis), or a subdirectory.
A simple example of an analysis is given in [`ModuleMuTauSimple.py`](python/analysis/ModuleMuTauSimple.py),
and more detailed instructions are in [`python/analysis/README.md`](python/analysis).
The `pico.py` script runs all analysis modules with the post-processor [`picojob.py`](python/processors/picojob.py).

You can link any analysis module to a custom channel short name (e.g. `mutau`):
```
pico.py channel mutau ModuleMuTauSimple
```
The channel short name can be whatever string you like (e.g. `mt`, `mymutau`, `MuTau`, ...).
However, you should avoid characters that are not safe for filenames, including `_`, `-`,`:` and `/`,
and it should not contain `skim` (reserved for skimming).

### Sample list
To link an era to your favorite sample list in [`samples/`](samples/), do
```
pico.py era 2016 sample_2016.py
```


## Samples

The nanoAOD samples you like to process should be specified in python file in [`samples/`](samples).
Each era (year) should be linked to a sample list, as explained above.
The file must include a python list called `samples`, containing [`Sample`](python/storage/Sample.py) objects
(or those from the derived `MC` and `Data` classes). For example,
```
samples = [
  Sample('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext1-v1/NANOAODSIM",
    dtype='mc',store=None,url="root://cms-xrd-global.cern.ch/",
  )
]
```
The `Samples` class takes at least three arguments:
1. The first string is a user-chosen name to group samples together (e.g. `'DY'`, `'TT'`, `'VV'`, `'Data'`).
2. The second is a custom, unique short name for the sample  (e.g. `'DYJetsToLL_M-50'`, `'SingleMuon_Run2016C'`). 
3. The third and optionally additional arguments are the full DAS paths of the sample.
Multiple DAS paths for the same sample can be used to combine extensions.

Other optional keyword arguments are
* `dtype`: Data type like `'mc'`, `'data'` or `'embed'`. As a short cut you can use the subclasses `MC` and `Data`.
* `store`: Path where all nanoAOD files are stored (instead of being given by the DAS tool).
  Note that this path is used for both skimming and analysis jobs.
  This is useful if you have produced or skimmed your NanoAOD samples, and they are not available via DAS.
  The path may contain variables like `$PATH` for the full DAS path, `$GROUP` for the group, `$SAMPLE` for the sample short name.
* `url`: Redirector URL for XRootD protocol, e.g. `root://cms-xrd-global.cern.ch` for DAS.
* `files`: Either a list of nanoAOD files, OR a string to a text file with a list of nanoAOD files.
  This can speed things up if DAS is slow or unreliable,
  or you want to avoid retrieving the files from a local storage element on the fly each time.
  Note that this list is used for both skimming and analysis jobs.
* `nevents`: The total number of nanoAOD events, that you can optionally compare to the number of processed events (with the `--das` flag).
  By default, it will be obtained from DAS, but it can be set by the user to speed things up,
  or in case the sample is not available on DAS.
* `nfilesperjob`: Number filed per job. If the samples is split in many small files,
  you can choose a larger `nfilesperjob` to reduce the number of short jobs.
  This overrides the default `nfilesperjob` in the configuration.
* `blacklist`: A list of files that you do not want to run on. This is useful if some files are corrupted.

Note that a priori skimming and analysis channels use the same sample lists (and therefore the same nanoAOD files)
for the same era as specified in the configuration.
While skimming is an optional step, typically you first want to skim nanoAOD from existing files on the GRID (given by DAS)
and store them locally for faster and more reliable access.
To run on skimmed nanoAOD files, you need to change `store` for each skimmed sample to point to the storage location.

To get a file list for a sample in the sample list, you can use the `get files` subcommand.
If you include `--write`, the list will be written to a text file as defined by `filelistdir` in the [configuration](#Configuration):
```
pico.py get files -y 2016 -s DYJets --write
```


## Local run
A local run can be done as
<pre>
pico.py run -y <i>&lt;era&gt;</i> -c <i>&lt;channel&gt;</i>
</pre>
For example, to run the `mutau` channel on a `2016` sample, do
```
pico.py run -y 2016 -c mutau
```
By default, the output will be saved in a new directory called `ouput/`.
Because `mutau` is an analysis module, the output will be a root file that contains a tree called `'tree'`
with a custom format defined in [`ModuleMuTauSimple.py`](python/analysis/ModuleMuTauSimple.py).
If you run a skimming channel, which must have `skim` in the channel name, the output will be a nanoAOD file.

Automatically, the first file of the first sample in the era's list will be run, but you can
specify a sample that is available in the [sample list linked to the era](samples/samples_2016.py),
by passing the `-s` flag a pattern:
```
pico.py run -y 2016 -c mutau -s 'DYJets*M-50'
pico.py run -y 2016 -c mutau -s SingleMuon
```
Glob patterns like `*` or `?` wildcards are allowed.
Some modules allow extra options via keyword arguments. You can specify these using the `--opts` flag:
```
pico.py run -y 2016 -c mutau -s DYJets*M-50 --opts tes=1.1
```
For all options, see
```
pico.py run --help
```


## Batch submission

### Submission
Once the module run locally, everything is [configured](#Configuration) and
[your batch system is installed](#Plug-ins), you can submit with
```
pico.py submit -y 2016 -c mutau
```
This will create the the necessary output directories for job configuration (`jobdir`)
and output (`nanodir` for skimming, `outdir` for analysis).
A JSON file is created to keep track of the job input and output.

Again, you can specify a sample by passing a glob patterns to `-s`, or exclude patterns with `-x`.
To give the output files a specific tag, use `-t`.

For all options with submission, do
```
pico.py submit --help
```


### Status
Check the job status with
```
pico.py status -y 2016 -c mutau
```
This will check which jobs are still running, and if the output files exist and are not corrupted.
For skimming jobs, the nanoAOD output files should appear in `nanodir`, and they are checked for having an `Events` tree.
For analysis jobs, the pico output files should appear in `outdir`, and they are checked for having a tree called `tree`,
and a histogram called `cutflow`.
To compare how many events were processed compared to the total available events in DAS (or defined in `Sample`), use the `--das` flag:
```
pico.py status -y 2016 -c mutau --das
```

### Resubmission
If jobs failed, you can resubmit with
```
pico.py resubmit -y 2016 -c mutau
```
This will resubmit files that are missing or corrupted (unless they are associated with a running job).
In case the jobs take too long, you can specify a smaller number of files per job with `--filesperjob` on the fly,
or use `--split` to split the default number.


### Finalize
ROOT files from analysis output can be `hadd`'ed into one large pico file:
```
pico.py hadd -y 2016 -c mutau
```
The output file will be stored in `picodir`.
This will not work for channels with `skim` in the name,
as it is preferred to keep skimmed nanoAOD files split for batch submission.


## Plug-ins

This framework might not work for your computing system... yet.
It was created with a modular design in mind, meaning that users can add their own
"plug-in" modules to make it work with their own batch system and storage system.
If you like to contribute, please make sure the changes run as expected,
push the changes to a fork and make a pull request.

### Batch system
To plug in your own batch system, make a subclass of [`BatchSystem`](python/batch/BatchSystem.py),
overriding the abstract methods (e.g. `submit`).
Your subclass has to be saved in separate python module in [`python/batch/`](python/batch),
and the module's filename should be the same as the class.
See for example [`HTCondor.py`](python/batch/HTCondor.py).
If you need extra (shell) scripts, leave them in `python/batch` as well.
Then you need to add your `submit` command to the `main_submit` function in
[`pico.py`](https://github.com/cms-tau-pog/TauFW/blob/9c3addaa1cd09cf4f866d279e4fa53a328f4997b/PicoProducer/scripts/pico.py#L973-L985).
```
def main_submit(args):
  ...
    elif batch.system=='SLURM':
      script  = "python/batch/submit_SLURM.sh %s"%(joblist)
      logfile = os.path.join(logdir,"%x.%A.%a")
      jobid   = batch.submit(script,name=jobname,log=logfile,dry=dryrun,...)
  ...
```

### Storage system
Similarly for a storage element, subclass [`StorageSystem`](python/storage/StorageSystem.py)
in [`python/storage/`](python/storage).
Currently, the code automatically assigns a path to a storage system, so you also need to 
edit `getstorage` in [`python/storage/utils.py`](python/storage/utils.py), e.g.
```
def getstorage(path,verb=0,ensure=False):
  ...
  elif path.startswith('/pnfs/psi.ch/'):
    from TauFW.PicoProducer.storage.T3_PSI import T3_PSI
    storage = T3_PSI(path,ensure=ensure,verb=verb)
  ...
  return storage
```
If you want, you can also add the path of your storage element to `getsedir` in the same file.
This help function automatically sets the default paths for new users, based on the host and user name.

### Analysis module
Detailed instructions to create an analysis module are provided [in the README](python/analysis/).

If you want to share your analysis module (e.g. for TauPOG measurements),
please make a new directory in [`python/analysis`](python/analysis),
where you save your analysis modules with a [`Module`](https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/eventloop.py)
subclass. For example, reusing the full examples:
```
cd python/analysis
mkdir MuTauFakeRate
cp TreeProducerMuTau.py MuTauFakeRate/TreeProducerMuTau.py
cp ModuleMuTau.py MuTauFakeRate/ModuleMuTau.py
```
Rename the module class to the filename (in this example `ModuleMuTau` stays the same) and
edit the the pre-selection and tree format in these modules to your liking.
Test run as
```
pico.py channel mutau python/analysis/MuTauFakeRate/ModuleMuTau.py
pico.py run -c mutau -y 2018
```
