import dataclasses
from compiler.ir import *
from compiler.ir_generator import IRFunction
from compiler.intrinsics import *

argument_registers = ["%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9"]


class Locals:
    """Knows the memory location of every local variable."""
    _var_to_location: dict[IRVar, str]
    _stack_used: int

    def __init__(self, variables: list[IRVar]) -> None:
        self._stack_used = 8 * len(variables)
        self._var_to_location = {}
        for (i, v) in enumerate(variables):
            self._var_to_location[v] = f"{-(i + 1) * 8}(%rbp)"
        for fn_name in ["print_int", "print_bool", "read_int"]:
            self._var_to_location[IRVar(fn_name)] = f"${fn_name}"

    def get_ref(self, v: IRVar) -> str:
        """Returns an Assembly reference like `-24(%rbp)`
        for the memory location that stores the given variable"""
        return self._var_to_location[v]

    def stack_used(self) -> int:
        return self._stack_used


def get_all_ir_variables(instructions: list[Instruction]) -> list[IRVar]:
    result_list: list[IRVar] = []
    result_set: set[IRVar] = set()

    def add(v: IRVar) -> None:
        if v not in result_set:
            result_list.append(v)
            result_set.add(v)

    for i in instructions:
        for field in dataclasses.fields(i):
            value = getattr(i, field.name)
            if isinstance(value, IRVar):
                add(value)
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, IRVar):
                        add(v)
    return result_list


def generate_function(func: IRFunction) -> str:
    locals = Locals(
        variables=get_all_ir_variables(func.ir)
    )
    lines = [
        f".global {func.name}",
        f".type {func.name}, @function",
        f"{func.name}:",
        f"    pushq %rbp",
        f"    movq %rsp, %rbp",
        f"    subq ${locals.stack_used()}, %rsp",
    ]
    func_end_label = f".L{func.name}_end"

    def emit(line: str) -> None:
        if line.startswith(".") or line.endswith(":"):
            lines.append(line)
        else:
            lines.append("    " + line)

    for (i, arg) in enumerate(func.args):
        emit(f"movq {argument_registers[i]}, {locals.get_ref(arg)}")

    for ins in func.ir:
        emit('# ' + str(ins))
        match ins:
            case Label():
                emit("")
                # ".L" prefix marks the symbol as "private".
                # This makes GDB backtraces look nicer too:
                # https://stackoverflow.com/a/26065570/965979
                emit(f'.{ins.name}:')
            case LoadIntConst():
                if -2**31 <= ins.value < 2**31:
                    emit(f'movq ${ins.value}, {locals.get_ref(ins.dest)}')
                else:
                    # Due to a quirk of x86-64, we must use
                    # a different instruction for large integers.
                    # It can only write to a register,
                    # not a memory location, so we use %rax
                    # as a temporary.
                    emit(f'movabsq ${ins.value}, %rax')
                    emit(f'movq %rax, {locals.get_ref(ins.dest)}')
            case Jump():
                emit(f'jmp .{ins.label.name}')
            case LoadBoolConst():
                emit(
                    f'movq ${1 if ins.value else 0}, {locals.get_ref(ins.dest)}')
            case Copy():
                emit(f'movq {locals.get_ref(ins.source)}, %rax')
                emit(f'movq %rax, {locals.get_ref(ins.dest)}')
            case CondJump():
                emit(f'cmpq $0, {locals.get_ref(ins.cond)}')
                emit(f'jne .{ins.then_label.name}')
                emit(f'jmp .{ins.else_label.name}')
            case Call():
                if ins.fun.name in all_intrinsics.keys():
                    all_intrinsics[ins.fun.name](IntrinsicArgs(
                        [locals.get_ref(v) for v in ins.args],
                        "%rax",
                        emit
                    ))
                    pass
                else:
                    for (i, arg) in enumerate(ins.args):
                        emit(
                            f'movq {locals.get_ref(arg)}, {argument_registers[i]}')
                    if ins.fun.name in ["print_int", "print_bool", "read_int"]:
                        emit(f'callq {ins.fun.name}')
                    elif ins.fun.name.startswith("V"):
                        emit(f'callq {locals.get_ref(ins.fun)}')
                    else:
                        emit(f'callq {ins.fun.name}')
                emit(f'movq %rax, {locals.get_ref(ins.dest)}')
            case Return():
                emit(f"movq {locals.get_ref(ins.value)}, %rax")
                emit(f"jmp {func_end_label}")
    emit(f"{func_end_label}:")
    emit("movq %rbp, %rsp")
    emit("popq %rbp")
    emit("ret")
    return "\n".join(lines)


def generate_assembly(functions: list[IRFunction]) -> str:
    start = "\n".join([
        ".extern print_int",
        ".extern print_bool",
        ".extern read_int",
        ".section .text",
    ])
    middle = "\n".join([generate_function(f) for f in functions])
    return start + "\n" + middle
