"""Publication import closure on inert bytes; never import inspected packages."""
import importlib.util
import builtins
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('publication_check',
    Path(__file__).resolve().parents[1]/'scripts/check-python-publication.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class PythonPublicationTests(unittest.TestCase):
    def test_direct_and_transitive_missing_modules_cannot_be_satisfied_by_local_files(self):
        sources = {'frontend_api/service.py':b'from frontend_api.portfolio_v6 import read_bucket',
            'frontend_api/portfolio_v6.py':b'from keeper.compound_policy import observe'}
        original_import = builtins.__import__
        def no_project_import(name, *args, **kwargs):
            if name.split('.')[0] in checker.PACKAGES:
                raise AssertionError('must not execute inspected packages')
            return original_import(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=no_project_import):
            errors = checker.check_sources(sources)
        self.assertEqual([dict(file='frontend_api/portfolio_v6.py',line=1,missing_module='keeper.compound_policy')],errors)
        sources.pop('frontend_api/portfolio_v6.py')
        self.assertEqual('frontend_api.portfolio_v6',checker.check_sources(sources)[0]['missing_module'])

    def test_complete_namespaces_relative_imports_and_external_libraries_are_accepted(self):
        sources = {'frontend_api/service.py':b'from .portfolio_v6 import read_bucket\nimport requests\n',
            'frontend_api/portfolio_v6.py':b'from keeper.compound_policy import observe',
            'keeper/compound_policy.py':b'def observe(): pass'}
        self.assertEqual([],checker.check_sources(sources))
        sources.pop('frontend_api/portfolio_v6.py')
        self.assertEqual('frontend_api.portfolio_v6',checker.check_sources(sources)[0]['missing_module'])

    def test_invalid_syntax_is_nonpass_and_no_inspected_code_is_executed(self):
        sources = {'keeper/monitor.py':b'raise Exception("never executed")',
            'frontend_api/broken.py':b'def not valid'}
        self.assertEqual([dict(file='frontend_api/broken.py',line=1,error='invalid_python_syntax')],checker.check_sources(sources))

    def test_package_member_import_requires_published_submodule_or_explicit_export(self):
        sources = {'keeper/monitor.py':b'from zzz_ops import production_v6, helper',
            'zzz_ops/__init__.py':b'def helper(): pass',
            'zzz_ops/production_v6.py':b'pass'}
        self.assertEqual([],checker.check_sources(sources))
        sources.pop('zzz_ops/production_v6.py')
        self.assertEqual('zzz_ops.production_v6',checker.check_sources(sources)[0]['missing_module'])

    def test_scripts_namespace_and_relative_imports_beyond_root_are_checked(self):
        sources = {'keeper/monitor.py':b'from scripts.local_reader import read',
            'frontend_api/service.py':b'from ..private import missing'}
        self.assertEqual([dict(file='frontend_api/service.py',line=1,error='relative_import_beyond_package'),
            dict(file='keeper/monitor.py',line=1,missing_module='scripts.local_reader')],checker.check_sources(sources))

    def test_git_index_reads_only_stage_zero_blob_bytes_not_worktree(self):
        raw=b'import frontend_api.missing\n';digest=b'a'*40
        transcript={('ls-files','--stage','-z','--',*checker.DIRECTORIES):b'100644 '+digest+b' 0\tkeeper/monitor.py\0',
            ('cat-file','--batch'):digest+b' blob '+str(len(raw)).encode()+b'\n'+raw+b'\n'}
        with patch.object(checker,'git',side_effect=lambda *args,input=None: transcript[args]):
            identity,sources=checker.read_sources(index=True)
        self.assertEqual('index',identity);self.assertEqual({'keeper/monitor.py':raw},sources)
        self.assertEqual('frontend_api.missing',checker.check_sources(sources)[0]['missing_module'])

    def test_conflicted_index_and_wrong_git_blob_identity_fail_closed(self):
        for mode in ('unmerged','wrong_blob'):
            def git(*args,input=None):
                if args[0]=='ls-files':return b'100644 '+b'a'*40+(b' 2' if mode=='unmerged' else b' 0')+b'\tkeeper/monitor.py\0'
                return b'b'*40+b' blob 0\n\n'
            with self.subTest(mode=mode),patch.object(checker,'git',side_effect=git),self.assertRaises(ValueError):
                checker.read_sources(index=True)


if __name__ == '__main__':
    unittest.main()
