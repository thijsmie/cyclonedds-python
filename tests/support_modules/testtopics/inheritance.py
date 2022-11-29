from dataclasses import dataclass

import cyclonedds.idl as idl
import cyclonedds.idl.annotations as annotate
import cyclonedds.idl.types as types


@dataclass
@annotate.final
@annotate.autoid("sequential")
class InheritanceTestParent(idl.IdlStruct, typename="module_test.parent"):
    var: types.char


@dataclass
@annotate.final
@annotate.autoid("sequential")
class InheritanceTestChild(InheritanceTestParent, typename="module_test.child"):
    var2: types.char

