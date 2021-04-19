from functools import reduce
from typing import Any, Dict, List, Optional, Set, Tuple

from ..graph import (
    Array,
    Assignment,
    Block,
    Call,
    ChunkVariable,
    Deref,
    Expression,
    Ref,
    Value,
    Variable,
)
from ..node import ArrayTypeNode, PointerTypeNode


class Lifter:
    """
    Utility methods for lifting variables to their most common usages.

    These functions provide primitives for the interpreter to replace function
    calls, function signatures and variable usages with the lifted paramter.
    """

    class VRef(Ref):
        pass

    @staticmethod
    def capture_usages(
        base: Block,
        var: ChunkVariable,
        recursive: bool = True,
        exclude: Optional[Set[Block]] = None,
    ) -> List["UsageCapture"]:
        """
        Find and capture all the usages (and their contexts) of a variable in a
        block.
        """

        captures: List[UsageCapture] = []
        stack: List[Any] = []

        exclude = set() if exclude is None else exclude

        def finder(part):
            if isinstance(part, Variable) and part.variable == var:
                use = part

                work = list(stack)
                while True:
                    item = work.pop()
                    if isinstance(item, (Ref, Deref, Array)):
                        use = item
                    elif isinstance(item, Assignment):
                        use = Lifter.VRef(use, use.id)
                        break
                    else:
                        break

                captures.append(UsageCapture(var, use))

                stack.append(part)
            else:
                stack.append(part)
                if recursive and isinstance(part, Call):
                    captures.extend(
                        Lifter.capture_usages(part.block, var, True, exclude | {base})
                    )

        if base not in exclude:
            base.traverse(finder)

        return captures

    @staticmethod
    def lift(
        base: Block, var: ChunkVariable
    ) -> Tuple["UsageCapture", ChunkVariable, Dict[int, Expression]]:
        """
        Return all the helpful primitives we can use in constructing the exact
        substitutions to perform to help left parameters.
        """

        captures = Lifter.capture_usages(base, var)
        root = reduce(UsageCapture.maximal, captures)
        root_var = root.nvar()
        root_inv = root.invert()

        translations = {}
        for use in Lifter.capture_usages(base, var, False):
            translations[use.capture.id] = use.replace(root_inv).simplify().capture

        return root, root_var, translations

    @staticmethod
    def rewrite(use: "UsageCapture", ctx: "UsageCapture") -> "UsageCapture":
        """
        Rewrite how a usage would appear in the context of another capture.

        Note that both the usage and the context must both be in the same
        global context.
        """

        use = use.simplify()
        ctx = ctx.simplify()

        ctx_inv = ctx.invert()
        return use.replace(ctx_inv).simplify()


class UsageCapture:
    """
    Representation and utility methods for capturing the context around a
    variable reference. We use these to detect how variables are used, and
    combine them in different ways.
    """

    def __init__(self, var: ChunkVariable, capture: Expression):
        self.var = var
        self.capture = capture

    def nvar(self) -> ChunkVariable:
        return self._nvar(self.capture)

    def invert(self) -> "UsageCapture":
        nvar = self.nvar()
        return UsageCapture(nvar, self._invert(self.capture, Variable(nvar)))

    def simplify(self) -> "UsageCapture":
        return UsageCapture(self.var, self._simplify(self.capture))

    def replace(self, new: "UsageCapture") -> "UsageCapture":
        return UsageCapture(new.var, self._replace(self.capture, new.capture))

    def maximal(self, other: "UsageCapture") -> "UsageCapture":
        return UsageCapture(
            self.var, self._simplify(self._maximal(self.capture, other.capture))
        )

    def _nvar(self, target: Expression) -> ChunkVariable:
        if isinstance(target, Variable):
            return target.variable
        elif isinstance(target, Ref):
            var = self._nvar(target.target)
            if var.vtype is None:
                return ChunkVariable(var.name, None, var.chunk)
            else:
                return ChunkVariable(var.name, PointerTypeNode(var.vtype), var.chunk)
        elif isinstance(target, (Array, Deref)):
            var = self._nvar(target.target)
            assert isinstance(var.vtype, (ArrayTypeNode, PointerTypeNode))
            return ChunkVariable(var.name, var.vtype.base, var.chunk)
        else:
            raise RuntimeError()

    def _invert(self, target: Expression, initial: Any) -> Expression:
        if isinstance(target, Variable):
            assert target.variable.name == self.var.name
            return initial
        elif isinstance(target, Ref):
            return self._invert(target.target, Deref(initial, target.id))
        elif isinstance(target, (Array, Deref)):
            return self._invert(target.target, Ref(initial, target.id))
        else:
            raise RuntimeError()

    def _replace(self, target: Expression, new: Expression) -> Expression:
        if isinstance(target, Variable):
            assert target.variable.name == self.var.name
            return new
        elif isinstance(target, Lifter.VRef):
            return self._replace(target.target, new)
        elif isinstance(target, Ref):
            result = self._replace(target.target, new)
            assert isinstance(result, (Variable, Array, Deref))
            return Ref(result, target.id)
        elif isinstance(target, Deref):
            return Deref(self._replace(target.target, new), target.id)
        elif isinstance(target, Array):
            return Array(self._replace(target.target, new), target.index, target.id)
        else:
            raise RuntimeError()

    def _simplify(self, target: Any) -> Any:
        # NOTE: commented out code are "interesting" invalid transformations

        if isinstance(target, Lifter.VRef):
            return self._simplify(Ref(target.target))

        if isinstance(target, Variable):
            return target
        elif isinstance(target, Ref):
            if isinstance(target.target, Deref):
                return self._simplify(target.target.target)
            # elif isinstance(target.target, Array):
            #    return self._simplify(target.target.target)
        elif isinstance(target, Deref):
            if isinstance(target.target, Ref):
                return self._simplify(target.target.target)
        elif isinstance(target, Array):
            pass
            # if isinstance(target.target, Ref):
            #     return self._simplify(target.target.target)
        else:
            raise RuntimeError()

        result = self._simplify(target.target)

        if isinstance(target, Variable):
            return target
        elif isinstance(target, Ref):
            if isinstance(result, Deref):
                return result.target
            # elif isinstance(result, Array):
            #     return result.target
            else:
                return Ref(result)
        elif isinstance(target, Deref):
            if isinstance(result, Ref):
                return result.target
            else:
                return Deref(result)
        elif isinstance(target, Array):
            return Array(result, target.index)
            # if isinstance(result, Ref):
            #     return result.target
            # else:
            #     return Array(result, target.index)
        else:
            raise RuntimeError()

    def _maximal(self, first: Expression, second: Expression) -> Expression:
        if isinstance(first, Ref) and isinstance(second, Ref):
            common = self._maximal(first.target, second.target)
            assert isinstance(common, (Variable, Array, Deref))
            return Ref(common)
        elif isinstance(first, Ref):
            return first
        elif isinstance(second, Ref):
            return second
        elif isinstance(first, Variable):
            return first
        elif isinstance(second, Variable):
            return second
        elif isinstance(first, Deref) and isinstance(second, Deref):
            common = self._maximal(first.target, second.target)
            return Deref(common)
        elif isinstance(first, Array) and isinstance(second, Array):
            if (
                isinstance(first.index, Value)
                and isinstance(second.index, Value)
                and first.index.value == second.index.value
            ):
                common = self._maximal(first.target, second.target)
                return Array(common, first.index)
            else:
                return Deref(self._maximal(first.target, second.target))
        elif isinstance(first, Deref) and isinstance(second, Array):
            return self._maximal(first.target, second.target)
        elif isinstance(first, Array) and isinstance(second, Deref):
            return self._maximal(first.target, second.target)
        else:
            raise RuntimeError()

    def __repr__(self) -> str:
        return repr(self.capture)
