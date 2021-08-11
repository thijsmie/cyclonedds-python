from itertools import product
from random import Random, randint
from string import ascii_uppercase,  ascii_lowercase


def _make_name(random: Random):
    consonants = "wrtpsdfgklzcvbnm"
    vowels = "euioa"
    bigrams = ["".join(p) for p in product(consonants, vowels)]
    trigrams = ["".join(p) for p in product(consonants, vowels, consonants)]
    return "".join(random.choices(bigrams, k=random.randint(1, 3)) + [random.choice(trigrams)]).capitalize()


def _make_field_type_nonest(random):
    return random.choice([
        "octet", "char", "short", "unsigned short", "long",
        "unsigned long", "long long", "unsigned long long", "boolean",
        "float", "double", "string"
    ])


def _make_field_type(random, collector, max_depth=3):
    if max_depth <= 0:
        return _make_field_type_nonest(random)

    v = random.random()

    if  max_depth > 0 and v < 0.08:
        name = _make_name(random)
        collector.append(_make_struct(random, collector, name, max_depth-1))
        return name

    if max_depth > 0 and v < 0.12:
        name = _make_name(random)
        collector.append(_make_union(random, collector, name, max_depth-1))
        return name

    if max_depth > 0 and v < 0.18:
        name = _make_name(random)
        collector.append(f"typedef {_make_field_type(random, collector, max_depth-1)} {name}[{random.randint(3, 20)}];\n")
        return name

    if max_depth > 0 and v < 0.22:
        name = _make_name(random)
        collector.append(f"typedef sequence<{_make_field_type(random, collector, max_depth-1)}> {name};\n")
        return name

    """ Need bounded sequence support for this:
    if max_depth > 0 and v < 0.26:
        name = _make_name(random)
        collector.append(f"typedef sequence<{_make_field_type(random, collector, max_depth-1)}, {random.randint(3, 20)}> {name};\n")
        return name
    """

    if max_depth > 0 and v < 0.28:
        name = _make_name(random)
        collector.append(f"typedef string<{random.randint(2, 20)}> {name};\n")
        return name

    return _make_field_type_nonest(random)


def _make_struct(random, collector, typename, max_depth=3):
    out = f"struct {typename} {{\n"

    for i in range(random.randint(2, 12)):
        key = "" if random.random() > 0.4 else "@key "
        out += f"\t{key}{_make_field_type(random, collector, max_depth-1)} {typename}{ascii_lowercase[i]};\n"

    out += "\n};\n"
    return out


def _make_union(random, collector, typename, max_depth=3):
    discriminator = random.choice([
        "octet", "long", "unsigned long", "long long",
        "unsigned long long", "short", "unsigned short"
    ])

    out = f"union {typename} switch ({discriminator}) {{\n"

    for i in range(random.randint(2, 12)):
        out += f"\tcase {i+1}:\n\t\t{_make_field_type(random, collector, 0)} {typename}{ascii_lowercase[i]};\n"

    if random.random() > 0.5:
        out += f"\tdefault:\n\t\t{_make_field_type(random, collector, 0)} {typename}_default;\n"

    out += "\n};\n"
    return out


def random_idl_types(seed=None, module=None, number=None):
    seed = seed if seed else randint(0, 1_000_000_000)
    random = Random(seed) if seed else Random()
    module = module if module else "py_c_compat"
    number = number if number else 1

    names = [_make_name(random) for i in range(number)]

    pre = f"""/*
 * Random datatype generation by fuzzy_idl_definition.py
 * Types: {', '.join(names)}
 * Seed: {seed}
 */

module {module} {{\n\n"""
    post = "\n};\n"

    collector = []
    for i in range(number):
        collector.append(_make_struct(random, collector, names[i]))

    return pre + "\n".join(collector) + post, names
