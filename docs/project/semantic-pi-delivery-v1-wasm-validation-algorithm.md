---
summary: "Reviewed deterministic validator algorithm for the restricted semantic Pi Wasm component."
read_when: ["Implementing or reviewing r23 module closure validation."]
type: "rfc_annex"
status: "in_review"
rfc_revision: "semantic-pi-delivery-v1-r23"
---
# Restricted Wasm validation algorithm — r23

This algorithm and `semantic-pi-delivery-v1-wasm-grammar.json` are normative reviewed bytes. Generated packet copies must be byte-identical or carry packet rows whose bytes are exactly these sources.

## Byte reader

The reader is single-pass, bounded, and consumes the complete file. `u32` and `u64` use unsigned LEB128; `s32` and `s64` use signed LEB128. Reject overflow, redundant terminal bytes, unused high bits, negative zero, and any encoding longer than `ceil(bits/7)`. Re-encoding the decoded integer must reproduce the exact consumed bytes. Vectors are canonical `u32 count` followed by exactly count values. Names are canonical-length strict UTF-8, NFC, and within the grammar limit.

Require exact magic/version. Each non-custom section ID occurs at most once in the reviewed section order. A section is `id || u32 payload_length || payload`; the subreader must end exactly at payload end. Only one custom section named `name` is legal and it follows data or is last when data is absent. Unknown IDs and trailing bytes reject.

## Sections

- **type**: vector of function types. Each starts `0x60`, followed by parameter/result value-type vectors. Only reviewed i32/i64 bytes are legal; at most one result.
- **function**: vector of type indices for defined functions. Each index is in type range.
- **memory**: exactly one memory. Limits flag is `0x01`, minimum and maximum are canonical u32, `minimum <= maximum <= 1024`.
- **global**: vector of i32/i64 globals followed by mutability byte `0x00|0x01`. Initializer is exactly matching `*.const` plus `end`; no global dependency. `global.set` rejects immutable targets.
- **export**: vector of unique NFC names. Export kind is function `0x00` or memory `0x02`. Exactly the four reviewed exports exist, memory index is zero, and each function type equals the reviewed ABI.
- **code**: vector count equals function count. Each body is `u32 body_length`, then a vector of local groups `{u32 count,value_type}`, instructions, and final `end`; group counts are positive, their checked sum is the expanded-local count and is at most 256, and the subreader ends exactly.
- **data**: only flag byte `0x00`, then offset `i32.const nonnegative; end`, then a byte vector; other segment flags reject; data bytes fit within minimum memory and segments do not overlap.
- **name**: after the custom-section name string, each subsection is exactly `u8 subsection_id || canonical_u32(payload_length) || payload`, and its bounded subreader ends exactly at payload end. Only module-name and function-name subsection IDs `0` and `1` are legal, in ascending order and each at most once. Module-name payload is exactly the canonical name string `pi-ontology-workflows`; absence of the module-name subsection is legal, but when present no other value is. Function-name payload is a canonical vector of `{function_index,name}` pairs with strictly increasing, unique indices; every index is in range and every name is unique by exact NFC scalar sequence. Unknown, repeated, out-of-order, duplicate-index, duplicate-name, or trailing subsection bytes reject.

Absent import/start/table/element/tag/data-count sections are not zero-length sections; their appearance rejects.

## Instruction and type validation

Validate each body with an operand-type stack and control stack. The initial control frame has the function result type. `block`, `loop`, and `if` accept only empty `0x40` or one i32/i64 result type; `if` pops i32. Each frame records start height, label types, end types, the parent's unreachable boolean saved on frame entry as `entry_unreachable`, and the current arm's unreachable boolean. A new arm starts with current unreachable equal to `entry_unreachable`. Loop label types are empty; block/if label types equal their result types. `else` is legal once for `if`: validate and consume the then-arm end types using the then-arm unreachable state, require the remaining operand-stack height to equal the frame start height exactly, then restore the operand stack to that height and restore the frame's current unreachable boolean to the saved `entry_unreachable` before validating the else arm. Then-arm unreachability never leaks into the else arm. An `if` with nonempty result type must contain `else`; an empty-result `if` may omit it. `end` validates and consumes the frame end types using that arm's unreachable state, requires the remaining operand-stack height to equal the frame start height exactly, pops the frame, and only then pushes its end types to the parent in order. Function completion requires exactly its result types and no extra operand.

For every opcode, require membership in the reviewed JSON list and apply only the following closed stack transitions:

Immediate decoding is exhaustive: `block|loop|if` consume exactly one block-type byte `40|7f|7e`; `br|br_if|call|local.get|local.set|local.tee|global.get|global.set` consume one canonical `u32`; every load/store consumes `canonical_u32 alignment_exponent || canonical_u32 offset`; `memory.size|memory.grow` consumes exactly byte `00`; `i32.const` consumes canonical `s32`; `i64.const` consumes canonical `s64`; every other reviewed opcode consumes no immediate. The body reader advances by exactly this production before applying its stack rule; no external opcode table is consulted.

- local/global get pushes declared type; set pops it; tee pops then pushes it;
- loads pop i32 address and push their declared result; stores pop the declared value type then pop the i32 address. Exact memory rules are `i32.load: pop i32, push i32, max alignment exponent 2`; `i64.load: pop i32, push i64, max 3`; `i32.load8_u: pop i32, push i32, max 0`; `i32.store: pop i32 value then i32 address, max 2`; `i64.store: pop i64 value then i32 address, max 3`; `i32.store8: pop i32 value then i32 address, max 0`. Offset is canonical u32 and checked against the 32-bit address space;
- `i32.const|i64.const` push respectively i32/i64. Exact numeric transitions are: `i32.eqz|i32.clz|i32.ctz: i32 -> i32`; `i64.eqz: i64 -> i32`; `i32.eq|i32.ne|i32.lt_u|i32.gt_u|i32.le_u|i32.ge_u: i32,i32 -> i32`; `i64.eq|i64.ne: i64,i64 -> i32`; `i32.add|i32.sub|i32.mul|i32.and|i32.or|i32.xor|i32.shl|i32.shr_u: i32,i32 -> i32`; `i64.add|i64.sub|i64.mul|i64.and|i64.or|i64.xor|i64.shl|i64.shr_u: i64,i64 -> i64`; `i32.wrap_i64: i64 -> i32`; and `i64.extend_i32_u: i32 -> i64`. Binary operands pop right then left and push the stated result; no other numeric transition exists;
- `select` pops the i32 condition, then right and left values of one equal reviewed i32/i64 type, and pushes that same selected value type;
- `call` pops callee parameters in reverse order and pushes results; index must be in defined-function range;
- `br`/`br_if` depth must name a live frame and validate its label types; `br_if` first pops an i32 condition, then peeks/type-checks and preserves label values on the fallthrough stack;
- `return` validates function result types;
- `drop` pops one value; `nop` changes nothing; `unreachable`, unconditional `br`, and `return` truncate to the current frame height and mark that frame unreachable. In an unreachable frame, a pop at frame height yields the requested reviewed type without consuming a value; explicit values above height still pop/type-check normally;
- memory size/grow use reserved zero byte; grow pops i32 and pushes i32.

Rule `wasm_encoding` assigns malformed/noncanonical immediate, missing/extra end, section overrun, and trailing bytes to `malformed_input`. Rule `wasm_validation` assigns stack underflow, type mismatch, invalid index/depth/alignment, values below frame height, unreachable misuse, and final extra values to `unsupported_protocol`. No external engine result is trusted.

## ABI execution checks

Structural validation proves only module closure. The host-owned metered interpreter separately enforces ten million instructions, one memory, no imports/I/O/clocks/randomness, exact JCS input, bounded output, and abort/deadline checks. `alloc(length:i32)->ptr:i32` interprets both values as unsigned 32-bit integers, requires length `1..16777216`, pointer alignment to 8 bytes, checked `ptr+length` without 32-bit wrap, complete containment in current memory, no overlap with any prior live allocation, and no memory growth beyond the reviewed maximum; only the host writes the exact JCS input into that range. `prepare(ptr:i32,length:i32)->i64` and `applied(ptr:i32,length:i32)->i64` receive that live input range. Their result i64 is interpreted unsigned: high 32 bits pointer, low 32 bits length. Reject overflow, alias with live input, out-of-memory range, length over 16 MiB, bytes changing during copy, reusing a consumed allocation, or retaining a live allocation after the call. Packed-pointer result rules apply only to `prepare` and `applied`, never to `alloc`. Host fixture cases own runtime ABI faults; structural validators do not fabricate execution.

## Independent implementation rule

Python and Node implementations may share only this reviewed text and grammar JSON. They share no parser, LEB helper, type-stack code, Wasm engine, generated AST, or expected-output builder. Both must emit the same first precedence error for every reviewed raw vector.
