"""New offline controls for compiler-advisory applicability screens, not EVM tests."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('compiler_advisory_analysis',Path(__file__).with_name('analyse.py'))
analysis=importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class ApplicabilityControls(unittest.TestCase):
    def test_cycle_detection_distinguishes_mutual_self_and_dag(self):
        graph={1:{2},2:{3},3:{1},4:{4},5:{6},6:set()}
        self.assertEqual({tuple(x) for x in analysis.cycles(graph)},{(1,2,3),(4,)})

    def test_array_recursive_struct_is_detected(self):
        types={1:{},2:{}}
        a={'nodeType':'ArrayTypeName','length':None,'baseType':{'nodeType':'UserDefinedTypeName','referencedDeclaration':2}}
        b={'nodeType':'ArrayTypeName','length':None,'baseType':{'nodeType':'UserDefinedTypeName','pathNode':{'referencedDeclaration':1}}}
        graph={1:{x for x,_ in analysis.struct_refs(a,types)},2:{x for x,_ in analysis.struct_refs(b,types)}}
        self.assertEqual(analysis.cycles(graph),[[1,2]])
        self.assertEqual(analysis.struct_refs(a,types),[(2,1)])

    def test_mapping_only_recursive_member_is_not_array_trigger(self):
        mapping={'nodeType':'Mapping','valueType':{'nodeType':'UserDefinedTypeName','referencedDeclaration':1}}
        self.assertEqual(analysis.struct_refs(mapping,{1:{}}),[])

    def test_super_dispatch_does_not_create_override_recursion(self):
        expr={'nodeType':'MemberAccess','referencedDeclaration':1,'expression':{'name':'super'}}
        self.assertEqual(analysis.internal_targets(expr,{1:{},2:{}},lambda ref:{1,2}),{1})

    def test_explicit_base_dispatch_does_not_create_override_recursion(self):
        expr={'nodeType':'MemberAccess','referencedDeclaration':1,'expression':{'typeDescriptions':{'typeIdentifier':'t_type$_t_contract$_ERC721_$1_$'}}}
        self.assertEqual(analysis.internal_targets(expr,{1:{},2:{}},lambda ref:{1,2}),{1})

    def test_virtual_identifier_dispatch_includes_override(self):
        expr={'nodeType':'Identifier','referencedDeclaration':1}
        self.assertEqual(analysis.internal_targets(expr,{1:{},2:{}},lambda ref:{1,2}),{1,2})

    def test_named_error_require_trigger_and_nontrigger(self):
        def call(callee,names):return {'nodeType':'FunctionCall','expression':{'name':callee},'arguments':[{'nodeType':'Literal'},{'nodeType':'FunctionCall','names':names}]}
        self.assertTrue(analysis.named_error_require(call('require',['b','a'])))
        self.assertFalse(analysis.named_error_require(call('require',[])))
        self.assertFalse(analysis.named_error_require(call('revert',['b','a'])))


if __name__=='__main__':unittest.main(verbosity=2)
