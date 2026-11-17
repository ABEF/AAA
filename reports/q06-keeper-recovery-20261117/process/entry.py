"""Test-only exec dispatcher: restart reads the same isolated journal."""
from pathlib import Path
import os,sys

def main():
    base=Path(__file__).resolve().parent
    scenario,root=sys.argv[1],Path(sys.argv[2])
    choices={'rpc':('rpc-stall','rpc_stalled.json'),
             'signer':('signer-stall','signer_ready.json')}
    first,marker=choices[scenario]
    mode='serve' if (root/marker).exists() else first
    os.execv(sys.executable,[sys.executable,str(base/'worker.py'),'--root',str(root),'--mode',mode])
if __name__=='__main__':main()
