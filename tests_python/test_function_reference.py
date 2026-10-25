"""Focused documentation-generator checks; no compiler or financial operations."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops.function_reference import (
    ReferenceError, build_reference, canonical_json, canonical_type, generate,
    import_compiler, load_json, merge_notes, render_markdown, sha, signature,
    _source,
)


class FunctionReferenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'src').mkdir()
        (self.root / 'docs').mkdir()
        self.source = self.root / 'src/Fixture.sol'
        self.source.write_bytes(b'pragma solidity 0.8.26; contract Fixture {}\n')
        self.abi = [
            {'type':'constructor','stateMutability':'nonpayable','inputs':[{'name':'owner','type':'address','internalType':'address'}]},
            {'type':'function','name':'safeTransferFrom','stateMutability':'nonpayable','inputs':[
                {'name':'from','type':'address'},{'name':'to','type':'address'},{'name':'tokenId','type':'uint256'}],'outputs':[]},
            {'type':'function','name':'safeTransferFrom','stateMutability':'nonpayable','inputs':[
                {'name':'from','type':'address'},{'name':'to','type':'address'},{'name':'tokenId','type':'uint256'},{'name':'data','type':'bytes'}],'outputs':[]},
            {'type':'function','name':'entries','stateMutability':'view','inputs':[{'name':'','type':'uint256'}], 'outputs':[
                {'name':'records','type':'tuple[][2]','internalType':'struct Fixture.Row[][2]','components':[
                    {'name':'owner','type':'address'},{'name':'amount','type':'uint256'}]}]},
            {'type':'receive','stateMutability':'payable'},
        ]
        settings = {'evmVersion':'cancun','optimizer':{'enabled':True,'runs':1},'outputSelection':{'*':{'*':['abi']}}}
        supplied = {'language':'Solidity','sources':{'src/Fixture.sol':{'content':self.source.read_text()}},'settings':settings}
        compiled = {'sources':{'src/Fixture.sol':{'id':0}},'contracts':{'src/Fixture.sol':{'Fixture':{'abi':self.abi,'evm':{
            'bytecode':{'object':'00'},'deployedBytecode':{'object':'00'}}}}}}
        sizes = {'settings':settings,'all_pass':True,'errors':[],
            'dependency_source_sha256':{},'build_input_sha256':{},
            'source_sha256':{'src/Fixture.sol':sha(self.source.read_bytes())},
            'compiler_content_sha256':{'src/Fixture.sol':sha(self.source.read_text().encode())},
            'gates':[{'path':'src/Fixture.sol','name':'Fixture','creation':1,'runtime':1,'creation_ok':True,'runtime_ok':True}]}
        self.paths = []
        for name,obj in [('input.json',supplied),('output.json',compiled),('sizes.json',sizes)]:
            path=self.root/name; path.write_text(json.dumps(obj),encoding='utf-8'); self.paths.append(path)
        self.base=import_compiler(self.root,*self.paths)
        self.notes={'schema':1,'contracts':{'Fixture':{'purpose':'Fixture ownership and ordered records.',
            'constructor':{'purpose':'Bind the fixture owner.','access':'Deployment only.','inputs':{'owner':'Initial fixture owner address.'}},
            'receive':{'purpose':'Receive explicitly authorized native settlement.','access':'Bound settlement caller.','value':'Exact native settlement only.'},
            'functions':{
                'safeTransferFrom(address,address,uint256)':{'purpose':'Safely transfer the NFT.','access':'Owner or approved operator.',
                    'inputs':{'from':'Current owner address.','to':'Receiving address.','tokenId':'Full NFT identifier.'}},
                'safeTransferFrom(address,address,uint256,bytes)':{'purpose':'Safely transfer the NFT with callback data.','access':'Owner or approved operator.',
                    'inputs':{'from':'Current owner address.','to':'Receiving address.','tokenId':'Full NFT identifier.','data':'Receiver callback payload.'}},
                'entries(uint256)':{'purpose':'Return the selected ordered record array.','access':'Read-only.','inputs':{'0':'Zero-based fixture record index.'}},
            }}}}

    def test_canonical_nested_tuple_arrays_and_overloads_are_exact(self):
        self.assertEqual(canonical_type(self.abi[3]['outputs'][0]), '(address,uint256)[][2]')
        self.assertEqual(signature(self.abi[1]),'safeTransferFrom(address,address,uint256)')
        self.assertNotEqual(signature(self.abi[1]),signature(self.abi[2]))
        nested={'type':'tuple[]','components':[{'type':'tuple[2]','components':[{'type':'uint'},{'type':'bytes32'}]}]}
        self.assertEqual(canonical_type(nested),'((uint256,bytes32)[2])[]')

    def test_invalid_tuple_and_scalar_shapes_are_not_documented_as_valid(self):
        for parameter in ({'type':'tuple[]'},{'type':'tuple[0]','components':[]},{'type':'uint7'},
                          {'type':'uint256[0]'},{'type':'address','components':[]}):
            with self.subTest(parameter=parameter),self.assertRaises(ReferenceError):
                canonical_type(parameter)

    def test_inherited_entries_positions_and_tuple_fields_are_preserved(self):
        result=build_reference(self.root,self.base,self.notes)
        self.assertEqual(result['counts'],{'contracts':1,'functions':3,'constructors':1,'receive_hooks':1,'fallback_hooks':0,'explanation_gaps':0,
                                        'unannotated_inputs':0,'unannotated_outputs':1})
        view=next(x for x in result['contracts'][0]['functions'] if x['name']=='entries')
        self.assertEqual(view['inputs'][0]['label'],'input0')
        self.assertEqual([x['name'] for x in view['outputs'][0]['components']],['owner','amount'])
        document=render_markdown(result)
        self.assertIn('records[][2].owner: address',document)
        self.assertIn('None in ABI.',document)
        self.assertIn('Exact native settlement only.',document)
        self.assertNotIn('transaction hash is returned',document)

    def test_source_drift_missing_or_new_source_fails_without_compiling(self):
        self.source.write_text(self.source.read_text()+'// changed\n')
        with self.assertRaisesRegex(ReferenceError,'source changed'):
            build_reference(self.root,self.base,self.notes)
        self.source.write_bytes(b'pragma solidity 0.8.26; contract Fixture {}\n')
        (self.root/'src/New.sol').write_text('pragma solidity 0.8.26;')
        with self.assertRaisesRegex(ReferenceError,'inventory changed'):
            build_reference(self.root,self.base,self.notes)

    def test_imported_dependency_drift_invalidates_existing_reference(self):
        dependency=self.root/'node_modules/example/Token.sol'
        dependency.parent.mkdir(parents=True)
        dependency.write_bytes(b'pragma solidity 0.8.26; interface Token {}\n')
        self.base['source_snapshot'].update(snapshot_schema=2,
            dependency_source_sha256={'node_modules/example/Token.sol':sha(dependency.read_bytes())},
            build_input_sha256={})
        build_reference(self.root,self.base,self.notes)
        dependency.write_bytes(dependency.read_bytes()+b'// changed inherited behavior\n')
        with self.assertRaisesRegex(ReferenceError,'Dependency source changed'):
            build_reference(self.root,self.base,self.notes)

    def test_dependency_lock_or_build_profile_drift_invalidates_reference(self):
        profile=self.root/'foundry.toml'
        profile.write_bytes(b'[profile.default]\nvia_ir=true\n')
        self.base['source_snapshot'].update(snapshot_schema=2,
            dependency_source_sha256={},build_input_sha256={'foundry.toml':sha(profile.read_bytes())})
        build_reference(self.root,self.base,self.notes)
        profile.write_bytes(b'[profile.default]\nvia_ir=false\n')
        with self.assertRaisesRegex(ReferenceError,'Build input changed'):
            build_reference(self.root,self.base,self.notes)

    def test_import_records_explicit_dependency_content_and_build_inputs(self):
        dependency=self.root/'node_modules/example/Token.sol'
        dependency.parent.mkdir(parents=True)
        dependency.write_bytes(b'pragma solidity 0.8.26; interface Token {}\n')
        profile=self.root/'foundry.toml';profile.write_bytes(b'[profile.default]\nvia_ir=true\n')
        supplied,compiled,sizes=[json.loads(p.read_text()) for p in self.paths]
        name='node_modules/example/Token.sol'
        supplied['sources'][name]={'content':dependency.read_text()}
        compiled['sources'][name]={'id':1}
        sizes['dependency_source_sha256'][name]=sha(dependency.read_bytes())
        sizes['compiler_content_sha256'][name]=sha(dependency.read_text().encode())
        sizes['build_input_sha256']['foundry.toml']=sha(profile.read_bytes())
        for path,obj in zip(self.paths,[supplied,compiled,sizes]):path.write_text(json.dumps(obj))
        imported=import_compiler(self.root,*self.paths)
        self.assertEqual(imported['source_snapshot']['snapshot_schema'],2)
        self.assertEqual(imported['source_snapshot']['dependency_source_sha256'],{name:sha(dependency.read_bytes())})
        self.assertEqual(imported['source_snapshot']['build_input_sha256'],{'foundry.toml':sha(profile.read_bytes())})
        build_reference(self.root,imported,self.notes)
        dependency.write_bytes(dependency.read_bytes()+b'// after compiler capture\n')
        with self.assertRaisesRegex(ReferenceError,'Compiler source content differs'):
            import_compiler(self.root,*self.paths)

    def test_import_rejects_implicit_or_omitted_compiler_dependency(self):
        compiled=json.loads(self.paths[1].read_text())
        compiled['sources']['node_modules/example/Uncaptured.sol']={'id':1}
        self.paths[1].write_text(json.dumps(compiled))
        with self.assertRaisesRegex(ReferenceError,'Compiler source inventory'):
            import_compiler(self.root,*self.paths)

    def test_dependency_paths_and_old_snapshot_cannot_bypass_binding(self):
        for name in ('/outside.sol','node_modules/../src/Fixture.sol','lib/../../outside.sol',
                     'node_modules\\example\\Token.sol','src/Fixture.sol'):
            with self.subTest(name=name):
                base=copy.deepcopy(self.base)
                base['source_snapshot']['dependency_source_sha256']={name:'0'*64}
                with self.assertRaises(ReferenceError):build_reference(self.root,base,self.notes)
        base=copy.deepcopy(self.base);base['source_snapshot'].pop('snapshot_schema')
        with self.assertRaisesRegex(ReferenceError,'Regenerate'):
            build_reference(self.root,base,self.notes)

    def test_missing_dependency_or_build_input_fails_closed(self):
        base=copy.deepcopy(self.base)
        base['source_snapshot']['dependency_source_sha256']={'node_modules/example/Missing.sol':'0'*64}
        with self.assertRaises(ReferenceError):build_reference(self.root,base,self.notes)
        base=copy.deepcopy(self.base);base['source_snapshot']['build_input_sha256']={'package-lock.json':'0'*64}
        with self.assertRaisesRegex(ReferenceError,'Build input'):
            build_reference(self.root,base,self.notes)

    def test_existing_build_file_cannot_be_omitted_from_snapshot(self):
        (self.root/'foundry.toml').write_bytes(b'[profile.default]\nvia_ir=true\n')
        with self.assertRaisesRegex(ReferenceError,'Build input inventory changed'):
            build_reference(self.root,self.base,self.notes)

    def test_size_gate_boolean_strings_cannot_qualify_compiler_import(self):
        original=json.loads(self.paths[2].read_text())
        for field in ('all_pass','creation_ok','runtime_ok'):
            with self.subTest(field=field):
                sizes=copy.deepcopy(original)
                if field=='all_pass':sizes[field]='false'
                else:sizes['gates'][0][field]='false'
                self.paths[2].write_text(json.dumps(sizes))
                with self.assertRaises(ReferenceError):import_compiler(self.root,*self.paths)

    def test_unreported_content_hash_or_invalid_saved_artifact_hash_is_rejected(self):
        sizes=json.loads(self.paths[2].read_text())
        sizes['compiler_content_sha256']['node_modules/example/Hidden.sol']='0'*64
        self.paths[2].write_text(json.dumps(sizes))
        with self.assertRaisesRegex(ReferenceError,'Compiler source inventory'):
            import_compiler(self.root,*self.paths)
        base=copy.deepcopy(self.base)
        base['source_snapshot']['compiler_output_sha256']='not-a-hash'
        with self.assertRaisesRegex(ReferenceError,'Invalid compiler artifact binding'):
            build_reference(self.root,base,self.notes)

    def test_source_root_resolution_cannot_escape_the_repository(self):
        # Model the resolution a junction/symlink returns; no host privilege or
        # real symlink is required. The external file genuinely exists.
        with tempfile.TemporaryDirectory() as other:
            outside=Path(other);(outside/'Fixture.sol').write_bytes(self.source.read_bytes())
            original=Path.resolve
            def resolved(path,*args,**kwargs):
                if path==self.root/'src':return outside
                if path==self.source:return outside/'Fixture.sol'
                return original(path,*args,**kwargs)
            with patch.object(Path,'resolve',new=resolved),self.assertRaises(ReferenceError):
                _source(self.root,'src/Fixture.sol')

    def test_deterministic_generation_and_check_detects_altered_document(self):
        notes=self.root/'docs/function-reference-notes.json'; notes.write_text(json.dumps(self.notes))
        output=self.root/'docs/function-reference.json'; document=self.root/'docs/CONTRACT_FUNCTIONS.md'
        generate(self.root,notes,output,document,base=self.base)
        first=output.read_bytes(),document.read_bytes()
        generate(self.root,notes,output,document,base=self.base)
        self.assertEqual(first,(output.read_bytes(),document.read_bytes()))
        generate(self.root,notes,output,document,check=True)
        document.write_text(document.read_text()+'Altered explanation.\n')
        with self.assertRaisesRegex(ReferenceError,'differs'):
            generate(self.root,notes,output,document,check=True)

    def test_unknown_or_missing_notes_are_explicit_and_not_invented(self):
        unknown=copy.deepcopy(self.notes)
        unknown['contracts']['Fixture']['functions']['withdraw(address)']={'purpose':'Not real.','access':'Not real.'}
        with self.assertRaisesRegex(ReferenceError,'unknown function'):
            build_reference(self.root,self.base,unknown)
        missing=copy.deepcopy(self.notes)
        del missing['contracts']['Fixture']['functions']['safeTransferFrom(address,address,uint256)']
        result=build_reference(self.root,self.base,missing)
        self.assertEqual(result['counts']['explanation_gaps'],2)
        self.assertIn('Not yet explained.',render_markdown(result))

    def test_check_rejects_missing_input_meaning_even_with_complete_function_notes(self):
        notes=copy.deepcopy(self.notes)
        del notes['contracts']['Fixture']['functions']['entries(uint256)']['inputs']
        path=self.root/'docs/function-reference-notes.json'; path.write_text(json.dumps(notes))
        output=self.root/'docs/function-reference.json'; document=self.root/'docs/CONTRACT_FUNCTIONS.md'
        counts=generate(self.root,path,output,document,base=self.base)
        self.assertEqual(counts['explanation_gaps'],0)
        self.assertEqual(counts['unannotated_inputs'],1)
        with self.assertRaisesRegex(ReferenceError,'incomplete.*1 missing top-level input'):
            generate(self.root,path,output,document,check=True)

    def test_removed_callable_and_duplicate_signatures_do_not_silently_pass(self):
        base=copy.deepcopy(self.base)
        base['abi_snapshot']['Fixture']['abi'].pop(1)
        with self.assertRaisesRegex(ReferenceError,'ABI snapshot changed'):
            build_reference(self.root,base,self.notes)
        base=copy.deepcopy(self.base)
        base['abi_snapshot']['Fixture']['abi'].append(copy.deepcopy(self.abi[1]))
        base['abi_snapshot']['Fixture']['abi_sha256']=sha(canonical_json(base['abi_snapshot']['Fixture']['abi']).encode())
        with self.assertRaisesRegex(ReferenceError,'Duplicate callable'):
            build_reference(self.root,base,self.notes)

    def test_compiler_content_settings_size_and_source_escape_are_checked(self):
        supplied=load_json(self.paths[0]); supplied['sources']['src/Fixture.sol']['content']+='// not compiled\n'
        self.paths[0].write_text(json.dumps(supplied))
        with self.assertRaisesRegex(ReferenceError,'source content differs'):
            import_compiler(self.root,*self.paths)
        supplied['sources']['src/Fixture.sol']['content']=self.source.read_text()
        supplied['settings']['evmVersion']='paris'; self.paths[0].write_text(json.dumps(supplied))
        with self.assertRaisesRegex(ReferenceError,'settings'):
            import_compiler(self.root,*self.paths)
        base=copy.deepcopy(self.base); base['abi_snapshot']['Fixture']['source']='src/../../outside.sol'
        with self.assertRaises(ReferenceError):build_reference(self.root,base,self.notes)

    def test_duplicate_json_nonfinite_unknown_parameter_notes_and_overlapping_notes_reject(self):
        bad=self.root/'bad.json'
        for data in ('{"a":1,"a":2}','{"a":NaN}'):
            bad.write_text(data)
            with self.assertRaises(ReferenceError):load_json(bad)
        unknown=copy.deepcopy(self.notes)
        unknown['contracts']['Fixture']['functions']['entries(uint256)']['inputs']={'not_an_input':'Wrong.'}
        with self.assertRaisesRegex(ReferenceError,'Unknown parameter'):
            build_reference(self.root,self.base,unknown)
        bad.write_text(json.dumps(self.notes))
        with self.assertRaisesRegex(ReferenceError,'overlap'):
            merge_notes([bad,bad])


if __name__=='__main__':
    unittest.main()
