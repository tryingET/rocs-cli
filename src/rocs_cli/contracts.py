"""Versioned, machine-readable contract for every public CLI operation."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

COMMAND_CONTRACT_VERSION = 2

_RAW_COMMANDS = {
    "version": ("introspection", False, [0]),
    "contracts": ("introspection", False, [0]),
    "constitution.validate": ("constitutional-foundry", False, [0, 1]),
    "constitution.challenge": ("constitutional-foundry", False, [0, 1]),
    "constitution.differential": ("constitutional-foundry", False, [0, 1]),
    "constitution.mutate": ("constitutional-foundry", False, [0, 1]),
    "repair-market": ("repair-market", False, [0, 1]),
    "context.create": ("intelligence-membrane", True, [0, 1]),
    "proposal.validate": ("intelligence-membrane", False, [0, 1]),
    "proposal.compile": ("intelligence-membrane", True, [0, 1]),
    "transaction.prepare": ("semantic-transaction", True, [0, 1]),
    "transaction.simulate": ("semantic-transaction", False, [0, 1]),
    "transaction.apply": ("semantic-transaction", True, [0, 1]),
    "transaction.verify": ("semantic-transaction", False, [0, 1]),
    "transaction.rollback": ("semantic-transaction", True, [0, 1]),
    "fleet.observe": ("fleet", False, [0, 1, 2]),
    "fleet.plan": ("fleet", False, [0, 1, 2]),
    "fleet.apply": ("fleet", True, [0, 1, 2]),
    "fleet.run": ("fleet", True, [0, 1, 2]),
    "bootstrap": ("repo", True, [0, 1, 2]),
    "converge": ("repo", True, [0, 1, 2]),
    "vendor": ("distribution", True, [0, 1, 2]),
    "release.plan": ("release", False, [0, 1, 2]),
    "release.apply": ("release", True, [0, 1, 2]),
    "verify": ("integrity", False, [0, 1]),
    "cleanup": ("maintenance", True, [0, 1]),
    "doctor": ("acceptance", False, [0, 1]),
    "generate": ("generator", True, [0, 1, 2]),
    "benchmark": ("performance", False, [0, 1]),
    "rules": ("ontology", False, [0]),
    "explain": ("ontology", False, [0, 1]),
    "resolve": ("ontology", False, [0, 1]),
    "summary": ("ontology", False, [0, 1]),
    "validate": ("ontology", False, [0, 1, 2]),
    "diff": ("ontology", True, [0, 1, 2]),
    "lint": ("ontology", False, [0, 1, 2]),
    "check-inverses": ("ontology", True, [0, 1, 2]),
    "graph": ("ontology", True, [0, 1]),
    "build": ("ontology", True, [0, 1, 2]),
    "pack": ("ontology", False, [0, 1]),
    "vendored-check": ("integrity", False, [0, 1]),
    "cache.dir": ("cache", False, [0]),
    "cache.ls": ("cache", False, [0]),
    "cache.clear": ("cache", True, [0]),
    "cache.prune": ("cache", True, [0]),
    "normalize": ("ontology", True, [0, 1, 2]),
}
COMMANDS: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {
        name: MappingProxyType({"capability": capability, "mutates": mutates, "exit_codes": list(exit_codes)})
        for name, (capability, mutates, exit_codes) in _RAW_COMMANDS.items()
    }
)


def command_contract() -> dict[str, object]:
    """Return a detached deterministic representation of the closed protocol."""
    return {
        "schema_version": COMMAND_CONTRACT_VERSION,
        "commands": {name: dict(COMMANDS[name]) for name in sorted(COMMANDS)},
    }
