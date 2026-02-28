import dataclasses
from compiler.ir import *
from compiler.intrinsics import *


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


def generate_assembly(instructions: list[Instruction]) -> str:
    locals = Locals(
        variables=get_all_ir_variables(instructions)
    )
    lines = [
        "    .extern print_int",
        "    .extern print_bool",
        "    .extern read_int",
        "    .global main",
        "    .type main, @function",
        "    .section .text",
        "main:",
        "    pushq %rbp",
        "    movq %rsp, %rbp",
        f"    subq ${locals.stack_used()}, %rsp"
    ]

    def emit(line: str) -> None:
        if line.startswith(".L"):
            lines.append(line)
        else:
            lines.append("    " + line)

    # ... Emit initial declarations and stack setup here ...

    for ins in instructions:
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
                    registers = ["%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9"]
                    for (i, arg) in enumerate(ins.args):
                        emit(f'movq {locals.get_ref(arg)}, {registers[i]}')
                    if ins.fun.name in ["print_int", "print_bool", "read_int"]:
                        emit(f'call {ins.fun.name}')
                    else:
                        emit(f'call {locals.get_ref(ins.fun)}')
                emit(f'movq %rax, {locals.get_ref(ins.dest)}')
    emit("movq %rbp, %rsp")
    emit("popq %rbp")
    emit("ret")
    return "\n".join(lines)
