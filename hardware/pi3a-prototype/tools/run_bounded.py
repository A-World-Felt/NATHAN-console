"""Bound a task-owned native subprocess; terminate only that child on timeout."""
from pathlib import Path
import argparse, json, os, subprocess, time
ROOT=Path(__file__).resolve().parents[1]
def main():
    a=argparse.ArgumentParser();a.add_argument('--seconds',type=int,default=30);a.add_argument('--label',required=True);a.add_argument('command',nargs=argparse.REMAINDER);x=a.parse_args()
    out=ROOT/'validation/native-current';out.mkdir(exist_ok=True,parents=True)
    env=os.environ.copy();env['HF_HUB_OFFLINE']='1';env['PYTHONDONTWRITEBYTECODE']='1';env['KICAD_CONFIG_HOME']=str(out/'config')
    log=out/(x.label+'.log');start=time.monotonic();timed=False
    with log.open('w',encoding='utf-8') as f:
        proc=subprocess.Popen(x.command,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,env=env);print('Own process PID='+str(proc.pid),flush=True)
        try:proc.wait(timeout=x.seconds)
        except subprocess.TimeoutExpired:timed=True;proc.kill();proc.wait(timeout=10)
    result={'own_pid':proc.pid,'returncode':proc.returncode,'timeout':timed,'elapsed':round(time.monotonic()-start,2),'log':str(log.relative_to(ROOT)),'command':x.command}
    (out/(x.label+'-run.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));print(log.read_text(encoding='utf-8',errors='replace')[-8000:])
    if timed or proc.returncode:raise SystemExit(1)
if __name__=='__main__':main()
