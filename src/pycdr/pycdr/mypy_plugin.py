from mypy.plugin import Plugin, AnalyzeTypeContext
from mypy.types import RawExpressionType
from mypy.typeanal import make_optional_type


class PyCDRMyPyPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str):
        if fullname.startswith("pycdr.types"):
            if fullname == "pycdr.types.array":
                return strip_length_array_type
            elif fullname == "pycdr.types.sequence":
                return strip_length_sequence_type
            elif fullname == "pycdr.types.bound_str":
                return bounded_str_to_str
            elif fullname == "pycdr.types.default":
                return union_default_type
            elif fullname == "pycdr.types.case":
                return union_case_type
        return None

    def get_class_decorator_hook(self, fullname: str):
        from mypy.plugins import dataclasses

        if fullname == "pycdr.cdr":
            return dataclasses.dataclass_class_maker_callback


def plugin(version: str):
    return PyCDRMyPyPlugin


def strip_length_array_type(ctx: AnalyzeTypeContext):
    if len(ctx.type.args) != 2 or not isinstance(ctx.type.args[1], RawExpressionType) or \
            ctx.type.args[1].base_type_name != "builtins.int":
        ctx.api.fail("pycdr.typing.array requires two arguments, a subtype and a fixed size.", ctx.context)
    return ctx.api.named_type('typing.Sequence', [ctx.api.analyze_type(ctx.type.args[0])])


def strip_length_sequence_type(ctx: AnalyzeTypeContext):
    if len(ctx.type.args) not in [1, 2]:
        ctx.api.fail("pycdr.typing.sequence requires a subtype and an optional max size.", ctx.context)
    elif len(ctx.type.args) == 2 and (not isinstance(ctx.type.args[1], RawExpressionType) or \
            ctx.type.args[1].base_type_name != "builtins.int"):
        ctx.api.fail("pycdr.typing.sequence max size should be an integer.", ctx.context)

    return ctx.api.named_type('typing.Sequence', [ctx.api.analyze_type(ctx.type.args[0])])


def bounded_str_to_str(ctx: AnalyzeTypeContext):
    if len(ctx.type.args) != 1 or not isinstance(ctx.type.args[0], RawExpressionType) or \
            ctx.type.args[0].base_type_name != "builtins.int":
        ctx.api.fail("pycdr.typing.bound_str requires one argument, a fixed size.", ctx.context)
    return ctx.api.named_type('builtins.str', [])


def union_default_type(ctx: AnalyzeTypeContext):
    if len(ctx.type.args) != 1:
        ctx.api.fail("pycdr.typing.default requires one argument, a type.", ctx.context)
    return make_optional_type(ctx.api.analyze_type(ctx.type.args[0]))


def union_case_type(ctx: AnalyzeTypeContext):
    if len(ctx.type.args) != 2:
        ctx.api.fail("pycdr.typing.case requires two arguments, a discriminator label and a type.", ctx.context)
    return make_optional_type(ctx.api.analyze_type(ctx.type.args[1]))
