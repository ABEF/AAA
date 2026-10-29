"""A complete verification claim requires the effective normal profile."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verification_profile',ROOT/'scripts/verify-normal-profile.py')
profile=importlib.util.module_from_spec(spec);spec.loader.exec_module(profile)


class VerificationProfileTests(unittest.TestCase):
    def config(self):
        c=json.loads((ROOT/'reports/current-pool-fork-20261026/profile-effective-config.json').read_bytes())['configuration']
        return {**c,'solc':'0.8.26','out':'out','cache_path':'cache','skip':[],
                'fs_permissions':[{'access':'write','path':'./deployments'}],
                **{k:None for k in ('match_test','no_match_test','match_contract','no_match_contract','match_path','no_match_path')},
                'fuzz':{'runs':1000},'invariant':{'runs':32,'depth':128,'fail_on_revert':True}}

    def inspect(self,c=None,version=None):
        c=self.config() if c is None else c;calls=[]
        def run(command,**kwargs):
            calls.append(command)
            text=version if version is not None else 'forge Version: 1.4.4 '+profile._policy.FORGE_COMMIT
            return subprocess.CompletedProcess(command,0,text if '--version' in command else json.dumps(c),'')
        with tempfile.TemporaryDirectory() as directory:
            executable=Path(directory)/'forge.exe';executable.write_bytes(b'controlled-tool-fixture')
            result=profile.inspect_profile(str(executable),{},run)
        return result,calls

    def test_reviewed_configuration_reads_only_version_and_config(self):
        result,calls=self.inspect()
        self.assertEqual(len(calls),2);self.assertIn('--version',calls[0]);self.assertIn('config',calls[1])
        self.assertFalse(result['build_or_tests_executed']);self.assertFalse(result['production_approved'])

    def test_compiler_size_optimizer_ffi_overrides_are_rejected(self):
        for key,value in [('solc','0.8.27'),('code_size_limit',999999),('optimizer_runs',200),('via_ir',False),('ffi',True)]:
            c=self.config();c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.inspect(c)

    def test_test_filters_skip_and_lowered_fuzz_invariants_are_rejected(self):
        changes=[('match_test','testOne'),('no_match_contract','Critical'),('skip',['ZZZVault.sol']),
                 ('fuzz',{'runs':1}),('invariant',{'runs':32,'depth':128,'fail_on_revert':False})]
        for key,value in changes:
            c=self.config();c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.inspect(c)

    def test_profile_override_rejects_before_any_process(self):
        with self.assertRaises(ValueError):profile.inspect_profile('forge',{'FOUNDRY_PROFILE':'other'},lambda *a,**k:self.fail('must not run'))

    def test_wrong_forge_identity_is_not_a_toolchain_approval(self):
        with self.assertRaises(ValueError):self.inspect(version='forge Version: 1.4.4 unrelated commit')

    def test_release_version_is_not_a_substring_match(self):
        for version in ('1.4.40','11.4.4','1.4.4-dev'):
            with self.subTest(version=version),self.assertRaises(ValueError):
                self.inspect(version='forge Version: '+version+' '+profile._policy.FORGE_COMMIT)

    def test_config_secrets_are_not_in_the_review(self):
        c=self.config();c.update(eth_rpc_url='https://invalid.example/private-fixture-secret',etherscan_api_key='private-fixture-key')
        result,_=self.inspect(c)
        self.assertNotIn('private-fixture',json.dumps(result))

    def test_cli_error_does_not_echo_provider_or_process_secrets(self):
        with patch.object(profile,'inspect_profile',side_effect=ValueError('private-fixture-secret')), \
             patch('sys.stderr',new_callable=io.StringIO) as stream:
            self.assertEqual(profile.main([]),1)
        self.assertIn('BLOCKED',stream.getvalue());self.assertNotIn('private-fixture',stream.getvalue())

    def test_known_safe_diagnostic_identifies_the_blocked_setting(self):
        with patch.object(profile,'inspect_profile',side_effect=ValueError('Normal fuzz settings differ')), \
             patch('sys.stderr',new_callable=io.StringIO) as stream:
            self.assertEqual(profile.main([]),1)
        self.assertEqual(stream.getvalue().strip(),'BLOCKED: Normal fuzz settings differ')

    def test_write_paths_and_remappings_cannot_redirect_normal_verification(self):
        for key,value in [('out','deployments'),('fs_permissions',[{'access':'read-write','path':'/'}]),
                          ('remappings',['@openzeppelin/contracts/=other/'])]:
            c=self.config();c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.inspect(c)


class VerificationWrapperTests(unittest.TestCase):
    def run_wrapper(self,flags=None,existing=False):
        bash=shutil.which('bash') or ('C:/Program Files/Git/bin/bash.exe' if Path('C:/Program Files/Git/bin/bash.exe').is_file() else None)
        if not bash:self.skipTest('Bash is not available for inert wrapper wiring')
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name)
        for folder in ('scripts','bin','node_modules/@openzeppelin/contracts','lib/forge-std','reports'):(root/folder).mkdir(parents=True,exist_ok=True)
        (root/'scripts/verify.sh').write_bytes((ROOT/'scripts/verify.sh').read_bytes())
        (root/'reports/forge-build.log').write_bytes(b'old build evidence')
        (root/'reports/python-tests.json').write_bytes(b'old Python evidence')
        if existing:(root/'reports/chosen').mkdir()
        python='''#!/usr/bin/env bash
set -eu
printf 'python %s\\n' "$*" >> calls
if [[ "$1" == scripts/verify-normal-profile.py ]]; then
  n=0; [[ ! -e profile-count ]] || read -r n < profile-count
  n=$((n+1)); printf '%s\\n' "$n" > profile-count
  [[ "${FAIL_PROFILE_AT:-0}" != "$n" ]] || exit 17
  if [[ "${CHANGE_PROFILE_AT:-0}" == "$n" ]]; then printf '{"profile":"changed"}\\n'; else printf '{"profile":"normal"}\\n'; fi
fi
'''
        forge='''#!/usr/bin/env bash
set -eu
printf 'forge %s\\n' "$*" >> calls
[[ "$1" != build || "${FAIL_BUILD:-0}" != 1 ]] || exit 23
printf 'inert forge fixture\\n'
'''
        for name,text in [('python3',python),('forge',forge)]:
            p=root/'bin'/name;p.write_text(text,encoding='utf-8',newline='\n');p.chmod(0o700)
        environment={k:os.environ[k] for k in ('PATH','SYSTEMROOT','WINDIR','TEMP','TMP','COMSPEC') if k in os.environ}
        environment.update(flags or {})
        if existing:environment['POPL_VERIFICATION_OUTPUT_DIR']='reports/chosen'
        result=subprocess.run([bash,'--noprofile','--norc','-c','export PATH="$PWD/bin:$PATH"; bash scripts/verify.sh'],
                              cwd=root,env=environment,capture_output=True,text=True,timeout=20)
        return root,result,(root/'calls').read_text() if (root/'calls').exists() else ''

    def test_success_uses_new_evidence_and_preserves_old_files(self):
        root,result,calls=self.run_wrapper()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((root/'reports/forge-build.log').read_bytes(),b'old build evidence')
        self.assertEqual((root/'reports/python-tests.json').read_bytes(),b'old Python evidence')
        folders=list((root/'reports').glob('verification.*'));self.assertEqual(len(folders),1)
        self.assertTrue((folders[0]/'forge-build.log').exists());self.assertTrue((folders[0]/'toolchain-after.json').exists())
        self.assertIn('scripts/run_python_tests.py --output reports/verification.',calls)
        self.assertIn('scripts/source_checks.py --output reports/verification.',calls)

    def test_profile_failure_stops_before_tests_build_or_evidence_directory(self):
        root,result,calls=self.run_wrapper({'FAIL_PROFILE_AT':'1'})
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('run_python_tests',calls);self.assertNotIn('forge build',calls)
        self.assertEqual(list((root/'reports').glob('verification.*')),[])

    def test_changed_profile_cannot_continue_to_build(self):
        _,result,calls=self.run_wrapper({'CHANGE_PROFILE_AT':'2'})
        self.assertNotEqual(result.returncode,0);self.assertNotIn('forge build',calls)
        self.assertNotIn('Local checks complete',result.stdout)

    def test_build_pipeline_failure_does_not_become_success(self):
        _,result,calls=self.run_wrapper({'FAIL_BUILD':'1'})
        self.assertNotEqual(result.returncode,0);self.assertNotIn('forge test',calls)
        self.assertNotIn('Local checks complete',result.stdout)

    def test_existing_evidence_directory_is_not_reused(self):
        _,result,calls=self.run_wrapper(existing=True)
        self.assertNotEqual(result.returncode,0);self.assertNotIn('run_python_tests',calls)
