# PicoProducer

This setup runs the [post-processors](https://github.com/cms-nanoAOD/nanoAOD-tools) on nanoAOD.
There are two modes:
1. **Skimming**: Skim nanoAOD by removing [unneeded branches](https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/processors/keep_and_drop_skim.txt),
                 bad data events (using [data certification JSONs](data/json)),
                 add things like JetMET corrections. Output still has a nanoAOD format.
2. **Analysis**: Analyze nanoAOD events by pre-selecting events and objects and constructing variables.
                 The main analysis code is found in [`python/analysis/`](python/analysis).
                 The output is a custom tree format we will refer to as _pico_.

#### Table of Contents  
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


## Installation

You need to have CMSSW and [NanoAODTools](https://github.com/cms-nanoAOD/nanoAOD-tools) installed, see the [README in the parent directory](../../../#taufw). Test the installation with
```
pico.py --help
```
To use DAS, make sure you have a GRID certificate installed, and a VOMS proxy setup
```
voms-proxy-init -voms cms -valid 200:0
```
or use the script
```
source utils/setupVOMS.sh
```


## Configuration

The user configuration is saved in [`config/config.json`](config/config.json).
You can manually edit the file, or set some variable with
<pre>
pico.py set <i>&lt;variables&gt; &lt;value&gt;</i>
</pre>
The configurable variables include
* `batch`: Batch system to use (e.g. `HTCondor`)
* `jobdir`: Directory to output job configuration and log files (e.g. `output/$ERA/$CHANNEL/$SAMPLE`)
* `outdir`: Directory to copy the output pico files from analysis jobs.
* `nanodir`: Directory to store the output nanoAOD files from skimming jobs (e.g. on EOS, T2, T3, ...).
* `picodir`: Directory to store the `hadd`'ed pico file from analysis job output (e.g. on EOS, T2, T3, ...).
* `nfilesperjob`: Default number of files per job. This can be overridden per sample (see below).
* `filelistdir`: Directory to save list of nanoAOD files to run on (e.g. `samples/files/$ERA/$SAMPLE.txt`).

Defaults are given in [`config/config.json`](config/config.json).
Note the directories can contain variables with `$` like
`$ERA`, `$CHANNEL`, `$CHANNEL`, `$TAG`, `$SAMPLE`, `$GROUP` and `$PATH`
to create a custom hierarchy and format.

### Skimming
Skimming of nanoAOD files is done by post-processor scripts saved in [`python/processors/`](python/processors).
An example is given by [`skimjob.py`](python/processors/skimjob.py).

You can link your skimming script to a custom channel short name
```
pico.py channel skim skimjob.py
```
This can be whatever string you want, but it should contain `skim` to differentiate from analysis channels,
and you should avoid characters that are not safe for filenames, including `-`, `:` and `/`.


### Analysis
This framework allows to implement many analysis modules called channels
(e.g. different final states like mutau or etau).
All analysis code should be saved in [`python/analysis/`](python/analysis), or a subdirectory.
An simple example of an analysis is given in [`ModuleMuTauSimple.py`](python/analysis/ModuleMuTauSimple.py),
and more detailed instructions are in [`python/analysis/README.md`](python/analysis/README.md).
The `pico.py` script runs all analysis modules with the post-processor [`picojob.py`](python/processors/picojob.py).

You can link any analysis module to a custom channel short name (e.g. `mutau`):
```
pico.py channel mutau ModuleMuTauSimple
```
The channel short name can be whatever string you like (e.g. `mt`, `mymutau`, `MuTau`, ...).
However, you should avoid characters that are not safe for filenames, including `-`, `:` and `/`,
and it should not contain `skim` (reserved for skimming).

### Sample list
To link an era to your favorite sample list in [`samples/`](samples/), do
```
pico.py era 2016 sample_2016.py
```


## Samples

Specify the samples with a python file in [`samples/`](samples).
The file must include a python list called `samples`, containing `Sample` objects
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
1. The first string is a user-chosen name to group samples together (e.g. `'DY'`, `'TT'`, `'VV'`, `'Data'`, ...).
2. The second is a custom short name for the sample  (e.g. `'DYJetsToLL_M-50'`, `'SingleMuon_Run2016C'`). 
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
* `nfilesperjob`: Number filed per job. If the samples is split in many small files,
  you can choose a larger `nfilesperjob` to reduce the number of short jobs.
  This overrides the default `nfilesperjob` in the configuration.
* `blacklist`: A list of files that you do not want to run on. This is useful if some files are corrupted.

To get a file list for a sample in the sample list, you can use the `get files` subcommand.
If you include `--write`, the list will be written to a text file as defined by `filelistdir` in the [configuration](#Configuration):
```
pico.py get files -y 2016 -s DYJets --write
```


## Local run
A local run can be done as
```
pico.py run -y 2016 -c mutau
```
You can specify a sample that is available in [`samples/`](samples), by passing the `-s` flag a pattern.
```
pico.py run -y 2016 -c mutau -s 'DYJets*M-50'
pico.py run -y 2016 -c mutau -s SingleMuon
```
Glob patterns like `*` wildcards are allowed.
Some modules allow extra options via keyword arguments. You can specify these using the `--opts` flag:
```
pico.py run -y 2016 -c mutau -s DYJets*M-50 --opts tes=1.1
```


## Batch submission

### Submission
Once configured, submit with
```
pico.py submit -y 2016 -c mutau
```
This will create the the necessary output directories for job configuration (`jobdir`)
and output (`nanodir` for skimming, `outdir` for analysis).
A JSON file is created to keep track of the job input and output.

Again, you can specify a sample by a patterns to `-s`, or exclude patterns with `-x`.
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

To plug in your own batch system, make a subclass of [`BatchSystem`](python/batch/BatchSystem.py),
overriding the abstract methods (e.g. `submit`).
Your subclass has to be saved in separate python module in [`python/batch/`](python/batch),
and the module's filename should be the same as the class. See for example [`HTCondor.py`](python/batch/HTCondor.py).
Then you need to add your `submit` command to the `main_submit` function in [`pico.py`](https://github.com/cms-tau-pog/TauFW/blob/a5730daa5d0595f4baf15a606790d8e512cd2219/PicoProducer/scripts/pico.py#L885-L897).

Similarly for a storage element, subclass [`StorageSystem`](python/storage/StorageSystem.py) in [`python/storage/`](python/storage).

