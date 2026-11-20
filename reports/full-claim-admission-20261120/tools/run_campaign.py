"""Run only the NEW native full-admission fixture and missing claim cases."""
from pathlib import Path
import argparse, importlib.util, json
from native_fixture import NativeF6Fixture, save

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 fixture=NativeF6Fixture(args.output);fixture.prepare()
 print(json.dumps({'phase':'prepared','output':str(fixture.output)}),flush=True)
 with fixture:
  fixture.export_state()
  print(json.dumps({'phase':'populated','nfts':32,'royalty_currencies':65}),flush=True)
  path=Path(__file__).with_name('campaign_checks.py')
  if path.is_file():
   spec=importlib.util.spec_from_file_location('full_native_campaign_checks',path);checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
   result=checks.run_qualification(fixture,fixture.output/'qualification')
   save(fixture.output/'CAMPAIGN_RESULT.json',result)
   print(json.dumps({'phase':'qualified','result_file':str(fixture.output/'CAMPAIGN_RESULT.json'),'production_approved':False}),flush=True)
  else:
   print(json.dumps({'phase':'fixture_exported','qualification_module_available':False}),flush=True)
if __name__=='__main__':main()
