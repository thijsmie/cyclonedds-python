import sys
import pytest
from datetime import datetime

from support_modules.test_tools.fixtures import FuzzingConfig

from support_modules.fuzz_tools.rand_idl.context_containers import FullContext
from support_modules.fuzz_tools.rand_idl.creator import generate_random_types
from support_modules.fuzz_tools.utility.stream import Stream, FileStream

from support_modules.fuzz_tools.checks.typeobject import check_type_object_equivalence
from support_modules.fuzz_tools.checks.keys import check_py_c_key_equivalence, check_py_pyc_key_equivalence
from support_modules.fuzz_tools.checks.mutated import check_mutation_assignability, check_mutation_key, check_enforced_non_communication
from support_modules.fuzz_tools.checks.typebuilder import check_sertype_from_typeobj


@pytest.mark.fuzzing
def test_fuzzing_types(fuzzing_config: FuzzingConfig):
    module_name = "fuzzytypes"
    scope = generate_random_types(module_name, number=fuzzing_config.num_types, seed=fuzzing_config.type_seed)
    ctx = FullContext(scope)

    log = FileStream(sys.stdout)
    all_succeeded = True

    start_time = datetime.now()

    for i, typename in enumerate(ctx.topic_type_names):
        if i < fuzzing_config.skip_types:
            log << f"Not testing {typename} (skipped):" << log.endl
            continue

        if fuzzing_config.max_total_time > 0 and (datetime.now() - start_time) > fuzzing_config.max_total_time:
            log << f"Not testing {typename} (skipped due to runtime limit reached):" << log.endl
            continue

        typelog = Stream()
        success = True
        mut_success = True
        success &= check_type_object_equivalence(typelog, ctx, typename)
        success &= check_py_pyc_key_equivalence(typelog, ctx, typename, fuzzing_config.num_samples)
        success &= check_sertype_from_typeobj(typelog, ctx, typename)

        if success:
            # If python and pyc are not agreeing on keys then python and C is not so relevant.
            success = check_py_c_key_equivalence(typelog, ctx, typename, fuzzing_config.num_samples)

        if success:
            # If keys are not equal we won't bother with mutations.
            mut_success &= check_mutation_assignability(typelog, ctx, typename, fuzzing_config.num_samples)

        if success and mut_success:
            # If python doesn't agree with itself then C for sure won't
            mut_success &= check_mutation_key(typelog, ctx, typename, fuzzing_config.num_samples)

        if success and mut_success:
            mut_success &= check_enforced_non_communication(typelog, ctx, typename)

        log << f"Testing {typename}(index={i}, success={success and mut_success}):" << log.endl << log.indent << typelog

        if not success:
            narrow_ctx = ctx.narrow_context_of(typename)
            log << log.endl << "[IDL]:" << log.indent << log.endl
            log << narrow_ctx.idl_file << log.endl
            log << log.dedent
            if fuzzing_config.store_reproducers:
                zipf, zipb = narrow_ctx.reproducer(typename)
                zipf.writestr('reproducer/log.txt', typelog.string)
                zipf.close()
                with open(f"{typename}_reproducer.zip", "wb") as f:
                    f.write(zipb.getvalue())

        if fuzzing_config.mutation_failure_fatal:
            success &= mut_success

        all_succeeded &= success

        log << log.dedent

    assert all_succeeded
