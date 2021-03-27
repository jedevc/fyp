from typing import Any, BinaryIO, Dict, List

from elftools.dwarf.dwarf_expr import DWARFExprParser
from elftools.elf.elffile import ELFFile


class SolveUtils:
    def __init__(self, binary: BinaryIO):
        self._elf = ELFFile(binary)

        self._dwarf = None
        self._dwarf_parser = None
        self._cu = None
        self._setup_dwarf()

        self.var_locations: Dict[str, List[Any]] = {}
        if self._cu:
            for die in self._cu.iter_DIEs():
                if die.tag != "DW_TAG_variable":
                    continue

                name = die.attributes["DW_AT_name"].value.decode()
                loc = die.attributes["DW_AT_location"].value
                locexpr = self._dwarf_parser.parse_expr(loc)

                assert len(locexpr) == 1
                assert name not in self.var_locations
                self.var_locations[name] = [locexpr[0].op_name, *locexpr[0].args]

    def _setup_dwarf(self):
        if not self._elf.has_dwarf_info():
            return

        self._dwarf = self._elf.get_dwarf_info()
        self._dwarf_parser = DWARFExprParser(self._dwarf.structs)

        # just take the first compilation unit (it's probably the one we want)
        try:
            self._cu = next(self._dwarf.iter_CUs())
        except StopIteration:
            self._cu = None
