# Author: Izaak Neutelings (May 2020)
import os, re, getpass
from TauFW.PicoProducer.tools.utils import execute
from TauFW.PicoProducer.batch.BatchSystem import BatchSystem


class SLURM(BatchSystem):
  # https://slurm.schedmd.com/sbatch.html
  
  def __init__(self,verb=False):
    super(SLURM,self).__init__(verb=verb)
    # http://pages.cs.wisc.edu/~adesmet/status.html
    self.statusdict = { 'q': ['PD'], 'r': ['R'], 'c': ['CD'], 'f': ['F','NF','CA'] }
    self.jobidrexp  = re.compile("Submitted batch job (\d+)")
    self.user       = getpass.getuser()
  
  def submit(self,script,**kwargs):
    """Submit a script with some optional parameters."""
    name      = kwargs.get('name',   None           )
    array     = kwargs.get('array',  None           )
    queue     = kwargs.get('queue',  None           ) # 'all.q','short.q','long.q'
    time      = kwargs.get('time',   None           )
    mem       = kwargs.get('mem',    None           )
    logdir    = kwargs.get('logdir', None           )
    logfile   = kwargs.get('log',    "%x.%A.%a"     ) # $JOBNAME.o$JOBID.$TASKID
    options   = kwargs.get('opt',    None           )
    dry       = kwargs.get('dry',    False          )
    verbosity = kwargs.get('verb',   self.verbosity )
    failflags = ["error"]
    jobids    = [ ]
    subcmd    = "sbatch"
    if name:
      subcmd += " -J %s"%(name)
    if array:
      if isinstance(array,int):
        subcmd += " -a 1-%s"%(array)
      else:
        subcmd += " -a %s"%(array)
    if queue:
      subcmd += " --partition %s"%(queue)
    if logfile:
      if logdir:
        logfile = os.path.join(logdir,logfile)
      subcmd += " -o %s"%(logfile)
    if time:
      subcmd += " --time='%s'"%(time) # e.g. "04:20:00"
    if mem:
      subcmd += " --mem=%sM"%(mem) # e.g. 5000
    if options:
      subcmd += " "+options
    subcmd += " "+script
    out  = self.execute(subcmd,dry=dry,verb=verbosity)
    fail = False
    for line in out.split(os.linesep):
      if any(f in line for f in failflags):
        fail = True
      matches = self.jobidrexp.findall(line)
      for match in matches:
        jobids.append(int(match))
    if fail:
      print ">>> Warning! Submission failed!"
      print out
    jobid = jobids[0] if len(jobids)==1 else jobids if len(jobids)>1 else 0
    return jobid
  
  def queue(self,job,**kwargs):
    """Get queue status."""
    # https://slurm.schedmd.com/squeue.html
    # squeue -u $USER -o '%.18i %.9P %.8j %.8u %.2t %.10M %.6D %16R %12p %10y'
    verbosity = kwargs.get('verb', self.verbosity )
    qcmd  = "squeue -u %s"%(self.user)
    return self.execute(qcmd,verb=verbosity)
  
  def status(self,job,**kwargs):
    """Check status of queued or running jobs."""
    verbosity = kwargs.get('verb', self.verbosity )
    jobid     = str(job.jobid)
    if job.taskid>=0:
      jobid  += '.%s'%job.taskid
    quecmd    = "squeue -j %s"%(jobid)
    return self.execute(quecmd,fatal=False,verb=verbosity)
  
  def jobs(self,jobids=[],**kwargs):
    """Get job status, return JobList object."""
    if not isinstance(jobids,list):
      jobids  = [jobids]
    verbosity = kwargs.get('verb', self.verbosity )
    quecmd    = "squeue -u %s"%(self.user)
    if jobids:
      quecmd += " -j "+','.join(str(j) for j in jobids)
    quecmd   += " --array -o '%10u %14F %14K %5t %o'" # user jobid taskid status args
    rows      = self.execute(quecmd,fatal=False,verb=verbosity)
    return self.parsejobs(rows)
  
