---
summary: "Scope/debt lane result for Decision 85 insertion evidence v1 r1."
read_when: ["Reviewing Decision 85 lane convergence."]
type: "review"
status: "complete"
---
# Scope/debt lane — r1

- Frozen commit: `14104636081ce127e46d56050ff3d07447c702ad`
- Tree: `0893e65d2095f386f422c4de6fa0bc739ddb8ec7`
- Aggregate: `272c892af593ff10ddb056b1914f20372308fe8a47ca28b3ca04ca8e27882991`
- Dispatch: `dispatch-1785105990788`
- Verdict: `ready_for_adr`

No blockers or unresolved material findings. The redesign has six named top-level schemas and 68 top-level properties, explicitly closes the required insertion semantics, and removes the failed generic resolver, production/recovery, SQL, seccomp, Wasm, consumer, and authority-overlay surfaces. Process-local attempt/frame/guard state is operational state, not a parallel governance authority.

Legal next move: controlling synthesis only. No implementation or live authority is granted.
