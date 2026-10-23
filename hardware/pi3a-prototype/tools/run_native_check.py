"""Bounded local native checks explicitly authorized for NATHAN.

Stops only the directly-created child on timeout. Does not suppress assertions.
No invocation of the historical bulk validator; one operation per run.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
KICAD=Path(os.environ.get('KICAD_BIN',r'C:\Program Files\KiCad\8.0\bin'))


def initialize_local_footprints(config):
    """Avoid the observed KiCad 8.0.2 first-run ERC crash in an empty profile.

    Use the distributed default, never a user's existing profile. This workaround
    does not establish the internal cause of the access violation.
    """
    target=config/'8.0'/'fp-lib-table'
    template=KICAD.parent/'share'/'kicad'/'template'/'fp-lib-table'
    copied=False
    if not target.exists():
        if not template.is_file():
            raise FileNotFoundError('KiCad 8 default footprint table unavailable: '+str(template))
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(template,target)
        copied=True
    return {'initialized_from_distribution':copied,
            'table_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('operation',choices=['load','drc','netlist','erc']);ap.add_argument('board',choices=['controls','base']);ap.add_argument('--config-dir',type=Path);args=ap.parse_args()
    out=ROOT/'validation'/'native-current';out.mkdir(parents=True,exist_ok=True)
    boardfile=ROOT/'electrical'/args.board/('nathan-'+args.board+'.kicad_pcb')
    sch=ROOT/'electrical'/args.board/('nathan-'+args.board+'.kicad_sch')
    if args.operation in ['load','drc']:
        code='import os,pcbnew; print("PID="+str(os.getpid())+" IMPORT_OK",flush=True); b=pcbnew.LoadBoard('+repr(str(boardfile))+'); print("LOAD_OK",flush=True); '
        if args.operation=='drc': code+='r=pcbnew.WriteDRCReport(b,'+repr(str(out/(args.board+'-drc.txt')))+',pcbnew.EDA_UNITS_MILLIMETRES,True); print("REPORT_GENERATED="+str(r),flush=True)'
        else: code+='print("FOOTPRINTS="+str(len(b.GetFootprints())),flush=True)'
        command=[str(KICAD/'python.exe'),'-u','-c',code]
    elif args.operation=='netlist':
        command=[str(KICAD/'kicad-cli.exe'),'sch','export','netlist','--format','kicadxml','--output',str(out/(args.board+'-native.net')),str(sch)]
    else:
        command=[str(KICAD/'kicad-cli.exe'),'sch','erc','--exit-code-violations','--output',str(out/(args.board+'-erc.rpt')),str(sch)]
    report_names={'drc':args.board+'-drc.txt','netlist':args.board+'-native.net','erc':args.board+'-erc.rpt'}
    report=out/report_names[args.operation] if args.operation in report_names else None
    previous_report=None
    if report and report.exists():
        history=out/'history';history.mkdir(exist_ok=True)
        previous_report=history/(report.name+'.'+str(time.time_ns()))
        report.rename(previous_report)
    config=(args.config_dir or out/'config').resolve()
    if not config.is_relative_to(ROOT): raise ValueError('Configuration directory must stay inside this design checkout')
    config.mkdir(parents=True,exist_ok=True)
    profile_initialization=initialize_local_footprints(config)
    env=os.environ.copy();env['HF_HUB_OFFLINE']='1';env['KICAD_CONFIG_HOME']=str(config)
    p=subprocess.Popen(command,cwd=str(ROOT),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    print('Own native check PID '+str(p.pid),flush=True);start=time.monotonic();timed=False
    try: stdout,stderr=p.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        timed=True;p.kill();stdout,stderr=p.communicate(timeout=5)
    result={'operation':args.operation,'board':args.board,'own_pid':p.pid,'returncode':p.returncode,'timeout_terminated_own_process':timed,'elapsed_seconds':round(time.monotonic()-start,2),'stdout':stdout,'stderr':stderr,'command':command,'note':'Exit success or report generation alone is not ERC/DRC pass.'}
    result['configuration_directory']=str(config.relative_to(ROOT))
    result['profile_initialization']=profile_initialization
    result['previous_report_archive']=str(previous_report.relative_to(ROOT)) if previous_report else None
    result['report_generated']=report.exists() if report else None
    result['report_sha256']=hashlib.sha256(report.read_bytes()).hexdigest() if report and report.exists() else None
    (out/(args.board+'-'+args.operation+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    if timed or p.returncode or (report and not report.exists()): raise SystemExit(1)


if __name__=='__main__':main()
