"""One-time fixture setup for the isolated, unfunded staging Anvil service.

Fixed loopback endpoint and chain 31337 only. Never supplies public-chain keys.
"""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from keeper.monitor import Keeper, error_context, signer_environment
from zzz_ops.abi import calldata, keccak256
from zzz_ops.state import atomic_json

BASE = Path('/opt/zzz-keeper-staging')
VAR = Path('/var/lib/zzz-keeper-staging')
URL = 'http://127.0.0.1:18545'


def main():
    if os.name!='posix' or os.getuid()==0:raise ValueError('Use the isolated unprivileged staging account')
    config_path = VAR/'keeper/config.json'
    if config_path.exists() or (VAR/'keeper/state.json').exists() or (VAR/'keys/keeper').exists():
        raise ValueError('Staging already initialized; preserve and recover it, never overwrite')
    spec=importlib.util.spec_from_file_location('rehearsal',BASE/'scripts/rehearse-keeper.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rpc=lambda method,params=None:module.rpc(URL,method,params)
    if rpc('eth_chainId')!='0x7a69' or 'anvil' not in rpc('web3_clientVersion').lower():
        raise ValueError('Only the local Anvil test chain is permitted')
    admin=rpc('eth_accounts')[0]
    def send(tx):
        tx_hash=rpc('eth_sendTransaction',[tx])
        receipt=module.wait_until(lambda:rpc('eth_getTransactionReceipt',[tx_hash]))
        if receipt['status']!='0x1':raise ValueError('Fixture setup transaction failed')
        return receipt
    artifact=json.loads((VAR/'build/out/KeeperVenue.sol/KeeperVenue.json').read_text())
    venue=send({'from':admin,'data':artifact['bytecode']['object'],'gas':'0x4c4b40'})['contractAddress'].lower()
    password=VAR/'keys/password';password.write_text(secrets.token_hex(32));password.chmod(0o600)
    cast=str(BASE/'bin/cast');env=signer_environment();env['CAST_PASSWORD']=password.read_text()
    result=subprocess.run([cast,'wallet','new',str(VAR/'keys'),'keeper'],env=env,capture_output=True,text=True,timeout=60)
    if result.returncode:raise ValueError('Encrypted fixture signer creation failed')
    key=VAR/'keys/keeper';key.chmod(0o600)
    result=subprocess.run([cast,'wallet','address','--keystore',str(key),'--password-file',str(password)],
        env=signer_environment(),capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('Cannot read fixture signer address')
    sender=result.stdout.strip().lower()
    rpc('anvil_setBalance',[sender,hex(10**20)])
    send({'from':admin,'to':venue,'data':calldata('authorize(address,bool)',sender,1),'gas':'0x7a120'})
    code=rpc('eth_getCode',[venue,'latest']);codehash='0x'+keccak256(bytes.fromhex(code[2:])).hex()
    roles=('access','vault','strategy','fees','compounder','buyback','pools')
    cfg={'chain_id':31337,'accounting_model':'shared-pools-v2','accounting_version':3,'fee_intake_version':1,
        'rpc_urls':[URL],'sender':sender,
        'contracts':{k:venue for k in roles},'code_hashes':{k:codehash for k in roles},
        'reviewed_for_live_use':True,'receipt_fee_policy':'included','cast_binary':cast,
        'keystore':str(key),'password_file':str(password),'confirmations':2,'interval_seconds':60,
        'max_gas_limit':500000,'max_gas_price_wei':10**11,'max_transaction_cost_wei':10**17,'max_daily_cost_wei':10**18,
        'state_path':str(VAR/'keeper/state.json'),'health_path':str(VAR/'keeper/health.json'),'lock_path':str(VAR/'keeper/keeper.lock'),
        'maintenance':{'compound':False,'harvest':True,'harvest_interval_seconds':14400},
        'staging_only':'Anvil fixture and disposable test ETH; never promote this configuration to a public chain'}
    atomic_json(config_path,cfg)
    Keeper(cfg).initialize_state()
    print(json.dumps({'initialized':True,'chain_id':31337,'sender':sender,'fixture':venue,'public_signing':False}))


if __name__=='__main__':
    try:main()
    except Exception as exc:print(json.dumps({'initialized':False,**error_context(exc)}));sys.exit(1)
