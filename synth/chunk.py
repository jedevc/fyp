from typing import List, Optional


class Variable:
    def __init__(self, name: str, vtype: str, size: int):
        self.name = name
        self.vtype = vtype
        self.size = size


class Chunk:
    def __init__(self, variables: List[Variable]):
        self._vars = variables
        self._table = {
            var.name: i
            for i, var in enumerate(variables)
            if not var.name.startswith("_")
        }

    @property
    def variables(self):
        return self._vars

    def lookup(self, name: str) -> Optional[Variable]:
        if name.startswith("_"):
            raise KeyError("cannot lookup hidden variable")

        i = self._table.get(name)
        if i is None:
            return None
        else:
            return self._vars[i]

    def add(self, variable: Variable):
        for i, var in enumerate(self._vars):
            if not var.name.startswith("_"):
                continue

            if var.vtype == variable.vtype:
                if var.size == variable.size:
                    self._vars[i] = variable
                    self._table[variable.name] = i
                    return
                elif var.size >= variable.size:
                    self._vars.insert(i, variable)
                    self._table[variable.name] = i
                    return

        raise RuntimeError("no space")
