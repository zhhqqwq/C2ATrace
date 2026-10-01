# C2ATrace v0.1 项目交付包

> Context-to-Action Trace — Provider-Boundary Context-to-Action Provenance

交付包状态：CURRENT HANDOFF BASELINE  
项目协议版本：v0.1  
交付状态快照日期：2026-10-01  
状态基线提交：`55879decbe8fe3bcb98e51a5da839934544bfe6e`

---

## 1. 交付目的

这份交付包用于让新的维护者、实现者、审阅者或合作方在不依赖历史聊天上下文的情况下接管 C2ATrace。

它回答五个问题：

1. 这个项目为什么存在；
2. v0.1 到底定义了什么；
3. 哪些内容已经冻结，哪些仍在进行；
4. 目前仓库中有哪些可交付资产；
5. 下一位负责人应该从哪里继续，以及哪些边界不能跨越。

本文件是项目交接入口，不替代规范正文。发生冲突时，编号 normative requirements、冻结 Schema、Conformance Suite manifest 与对应 audit 文件优先。

---

## 2. 项目构想

C2ATrace 的目标是建立一个开放、可移植、可独立验证的 **Context-to-Action provenance protocol**。

它解决的不是“模型为什么这么想”，而是一个更可观察、更可验证的问题：

> 应用到底把什么发送到了模型，这些输入来自哪里、经过了什么转换、属于哪个实际 provider request；模型返回了什么；应用最后实际选择并执行了什么工具调用；工具返回了什么；我们又观察到了什么外部结果。

项目核心定位：

> **C2ATrace is the provenance layer between context assembly and agent actions.**

更完整的协议定位：

> A policy-neutral interoperability protocol for preserving source and transformation provenance into the exact application-visible provider request, and linking that request to subsequent model outputs, tool executions, and observed effects.

---

## 3. 为什么需要 C2ATrace

现代 agent 系统中的审计链条经常在几个地方断裂：

- 检索系统知道“拿到了哪些资料”，但不知道哪些内容最终真的进入 provider request；
- prompt builder 会截断、拼接、重排、模板化、序列化，但这些变换通常没有可验证 lineage；
- SDK/provider 可能 retry、failover、hedge，使一个逻辑调用对应多个物理 attempt；
- 流式输出可能部分完成，capture completeness 与 provider completion 被混在一起；
- 模型提出的 tool call 可能被应用修改参数、添加 repo/tenant/auth/default；
- allow/deny policy 经常被错误建模成“执行事件”；
- tool success 往往被错误解释成真实世界效果已经发生；
- hash/signature 常被错误升级为“记录是真的”或“历史完整”；
- 隐私保护又会让 plaintext 无法直接保留。

C2ATrace 的方案不是增加一个 SaaS dashboard，而是定义一个可以被不同 SDK、provider adapter、tool adapter、verifier、observability system 共同使用的协议层。

---

## 4. 项目理念

v0.1 的核心设计原则已经冻结在规范中：

- Specification before integrations.
- Provider-neutral.
- Framework-neutral.
- Policy-neutral.
- Observability-compatible, not an observability replacement.
- Unknown over guessing.
- Conservative over false precision.
- Integrity is not truth.
- Execution is not outcome.
- Included is not causally responsible.
- Tainted is not malicious.
- Trusted is not objectively true.
- Sanitized is not automatically trusted.
- Valid chain is not complete history.
- Provider internals remain unknown unless separately evidenced.
- Signature validity is not record truth.
- Signature validity is not capture completeness.
- ReceiptLink integrity is not global-history completeness.
- Tool-reported success is not external Effect truth.
- EffectObservation is not OutcomeVerification.
- There is no unqualified overall `fully_verified` boolean.

这些不是文档风格偏好，而是 v0.1 的 claim-safety 边界。

---

## 5. 核心链路

C2ATrace 的主链路是：

~~~text
SourceRef
  ↓
SourceObservation
  ↓
Transform / Derivation
  ↓
ModelInputComponent / ContextFragment
  ↓ RequestBinding
RequestSnapshot
  ↓
ProviderAttempt
  ↓
ModelOutput
  ↓
ToolProposal
  ↓ optional application preparation Transform
ToolInvocation
  ↓
ToolExecution
  ↓
ToolResult
  ↓
EffectObservation
~~~

逻辑和完整性层还包括：

~~~text
Run
ModelInvocation
ToolDecision
TrustAssertion
TaintAssertion
CaptureDiagnostic
Receipt
ExternalReference
ReceiptLink
IntegrityEnvelope
VerificationFinding
VerificationReport
~~~

---

## 6. 核心对象分类

C2ATrace 使用三类主要 runtime provenance 对象：

| 分类 | 含义 | 典型对象 |
|---|---|---|
| Artifact | 不可变的记录数据表示 | SourceObservation, RequestSnapshot, ModelOutput, ToolInvocation, ToolResult |
| Activity | 使用/生成 Artifact 的过程 | Transform, ModelInvocation, ProviderAttempt, ToolExecution |
| Assertion | 对对象、关系或属性的记录声明 | Derivation, RequestBinding, ToolDecision, TrustAssertion, TaintAssertion, CaptureDiagnostic |

结构/meta 对象独立存在：

| 分类 | 对象 |
|---|---|
| Reference | SourceRef, ExternalReference form |
| Scope | Run |
| Package | Receipt / Authenticated Receipt Payload |
| Integrity metadata | ReceiptLink, IntegrityEnvelope |
| Verifier output metadata | VerificationFinding, VerificationReport |

这个分类是协议语义的重要组成部分。不能因为实现方便把 Assertion 编成 Activity，也不能把 Package/Verifier output 塞进 runtime provenance graph。

---

## 7. 已解决的核心问题

v0.1 已经完成并冻结以下大型语义问题。

### 7.1 Source 与 observation

- locator 不等于 source identity；
- 相同 bytes / ETag 不合并不同 observation occurrence；
- redirect/version hint 不自动形成 identity；
- unknown source 是一等状态；
- capture extent 是相对 capture target 的 bounded claim。

### 7.2 Transform 与 Derivation

- Transform 是 Activity；
- Derivation 是显式 Assertion；
- use/generate 不自动等于 derivation；
- exact / partial / unknown 的边界已经定义；
- Region lineage 支持 split/concat/truncate/extract 等；
- control-only input 不自动成为 representation ancestry。

### 7.3 Request boundary

核心 capture levels：

~~~text
sdk_arguments
provider_payload
prepared_http_body
unknown
~~~

RequestBinding 是 occurrence-specific、capture-level-local 的 inclusion assertion。

`prepared_http_body` 是 application-side 捕获边界，不是 provider receipt，也不是 provider internal prompt。

### 7.4 Model invocation 与 provider attempt

明确区分：

~~~text
ModelInvocation
≠
ProviderAttempt
≠
RequestSnapshot
≠
ModelOutput
~~~

retry / failover / hedge 可以属于同一个逻辑 ModelInvocation。

response termination 与 output capture extent 是独立维度。

### 7.5 Tool chain

核心分离：

~~~text
ToolProposal
≠
ToolInvocation
≠
ToolExecution
≠
ToolResult
≠
EffectObservation
≠
OutcomeVerification
~~~

ToolInvocation 表示最终 application-visible pre-execution effective call。

argument provenance 可以区分：

~~~text
model_supplied
application_supplied
mixed
unknown
~~~

ToolDecision 是 Assertion，不用伪造 ToolExecution 表达 deny。

### 7.6 Trust / Taint

Trust 与 Taint 都是 policy/issuer scoped assertions，不是对象固有真值。

v0.1 明确：

- trust 不自动继承；
- taint 有 content/control 区分；
- taint propagation 是 policy-scoped；
- sanitization 必须显式、scope-specific、evidence-bounded；
- sanitization 不允许擦除 provenance history。

### 7.7 Privacy

支持 package-relative privacy：

~~~text
full
hash_only
hmac
redacted
mixed
unknown
~~~

关键边界：

- withheld ≠ absent；
- hash-only ≠ confidentiality guarantee；
- HMAC 可允许 independent-but-not-public verification；
- redacted representation ≠ original representation；
- privacy omission 不能增强 provenance claim。

### 7.8 Integrity / Receipt

v0.1 已冻结：

- Receipt identity；
- subset Receipt semantics；
- ExternalReference；
- multi-Receipt Resolution Set；
- ReceiptLink；
- RFC 8785 JCS；
- SHA-256；
- Ed25519；
- embedded / detached IntegrityEnvelope；
- signer/key reference 边界；
- signed redacted/hash-only evidence 语义；
- valid chain ≠ complete history。

### 7.9 Adapter contracts

Provider Adapter 与 Tool Adapter 都已经完成 responsibility / visibility boundary。

Adapter capability declaration：

> 表示“这个 adapter 声称能够观察什么”。

CaptureDiagnostic：

> 表示“某次实际 instrumentation occurrence 捕获到、部分捕获、不可用、unsupported、bypass 或 unknown”。

二者不能互相替代。

### 7.10 Verifier contract

Verifier 被限定为 evidence-bounded、invocation-relative。

结果不是单一强弱等级，而是 typed result domains，例如：

~~~text
valid / invalid
matched / mismatched
resolved / unresolved / ambiguous
established / asserted / unknown / unverified
present / not_present / withheld
consistent / conflict
unsupported
~~~

Verifier 不得产生一个无条件 `fully_verified=true` 代替这些维度。

---

## 8. 当前完成状态

### 8.1 语义与契约

以下 Gate 已全部完成：

- Phase 0 Foundations；
- Phase 1 Part A — Source；
- Part B — Transform / Derivation；
- Part C — Request；
- Part D — Model Invocation / Output；
- Part E — Tool / Effect；
- Part F — Trust / Taint；
- Part G — Privacy；
- Part H — Integrity / Receipt；
- Provider Adapter Contract；
- Tool Adapter Contract；
- Verifier Contract。

### 8.2 Normative requirements

当前 accepted numbered requirements：

~~~text
907
~~~

family 分布：

| Family | Count |
|---|---:|
| TM | 12 |
| CLAIM | 6 |
| GRAPH | 16 |
| SRC | 22 |
| DRV | 32 |
| REQ | 52 |
| OUT | 53 |
| TOOL | 62 |
| TRUST | 25 |
| TAINT | 59 |
| PRIV | 80 |
| RCPT | 51 |
| INTG | 70 |
| PAD | 95 |
| TAD | 118 |
| VFY | 154 |

每条 requirement 都有 planned test ID。

### 8.3 JSON Schema Freeze

v0.1 JSON Schema：

> **ACCEPTED / FROZEN**

关键审计结果：

- Draft 2020-12；
- 16 个 frozen Schema resources；
- 16 个 unique `$id`；
- 259 个 cross-schema `$ref` 已审计；
- 0 broken ref；
- 24 个 runtime Record union branch；
- 5 个 top-level document branch；
- 34 个预期 wire object 均有明确 schema home。

Freeze audit 位于：

`schema/v0.1/FREEZE-AUDIT.md`

Schema manifest：

`schema/v0.1/manifest.json`

### 8.4 基础 fixtures / vectors

当前冻结基线包括：

- 9 个 valid Receipt fixtures；
- 6 个 invalid fixtures：
  - 2 schema-invalid；
  - 3 semantic-invalid；
  - 1 crypto-invalid；
- deterministic JCS/SHA-256/Ed25519 vector；
- HMAC-SHA256 privacy vector；
- hash-only SHA-256 privacy vector；
- integrity separation vector；
- scenario manifest。

已经验证：

- valid Receipt ARP digest 可重算；
- schema-invalid 在 Schema 层失败；
- semantic-invalid 保持 Schema-valid；
- crypto-invalid 保持 Schema-valid 但 digest mismatch；
- ExternalReference pin 与 ReceiptLink digest 可匹配目标 Receipt；
- Ed25519 正确 key / wrong key 与 tampered ARP separation 行为符合定义。

---

## 9. 当前正在进行的 Gate：Conformance Suite

当前 source of truth：

`conformance/v0.1/manifest.json`

状态：

> **IN PROGRESS**

### 9.1 Case mapping

~~~text
requirements: 907
mapped_cases: 907
~~~

即所有 requirement 已经有唯一 case ID。

Case ID 同时绑定：

- requirement ID；
- planned-test ID。

不会因为两个 requirement 共用类似 test 名就自动合并。

### 9.2 当前可执行/接受进度

当前 manifest：

~~~text
mapped cases       907 / 907
executable cases   136
accepted cases       6
~~~

当前 enforcement 分类：

| Layer | Total | Executable / Accepted state |
|---|---:|---|
| direct_schema | 6 | 6 accepted |
| mixed_schema_semantic | 87 | 87 executable，0 remaining；acceptance pending |
| semantic_verifier | 771 | 当前尚处大规模 materialization 前期 |
| deterministic_vector | 43 | 43 executable，0 remaining；acceptance pending |

注意：这是 Conformance executability review 后的当前责任分类，也是当前工作量规划的 source of truth。

Schema Freeze 初期分类曾经更粗；之后对 REQ-005、REQ-006、REQ-013、REQ-014、RCPT-012、RCPT-013 做了执行层纠正。协议语义和 frozen Schema 均未改变。

### 9.3 direct_schema

状态：

> **ACCEPTED**

当前 6 条：

- REQ-004
- PAD-002
- PAD-003
- TAD-002
- TAD-003
- VFY-105

### 9.4 deterministic wave

当前：

~~~text
43 / 43 executable
0 remaining
materialization complete; runner acceptance pending
~~~

已覆盖至少：

- JCS profile；
- invalid / duplicate-name canonicalization rejection；
- exact UTF-8 canonical bytes；
- no extra Unicode normalization；
- array-order preservation；
- complete-ARP SHA-256 scope；
- Ed25519 profile；
- Signing Statement domain / receipt / digest / algorithm / key-ref / envelope-id binding；
- invalid signature；
- post-sign ARP tamper separation；
- privacy hash-only；
- privacy HMAC；
- embedded vs detached envelope binding；
- detached target mismatch separation；
- signed record deletion / fresh digest recomputation；
- commitment compatibility and representation-basis separation；
- HMAC secret/candidate/comparison-domain capability boundaries；
- original vs redacted commitment separation；
- whole-scope hash/HMAC bounded equality；
- signed hash-only / HMAC / redacted scope composition；
- signed ReceiptLink pin authentication boundaries。

### 9.5 mixed wave

当前：

~~~text
87 / 87 executable
0 remaining
materialization complete; runner acceptance pending
~~~

已覆盖：

- ownership/cardinality；
- request capture-level vocabulary；
- attempt/execution terminal-disposition vocabulary；
- output capture-extent vocabulary；
- ToolDecision decision vocabulary；
- EffectObservation basis requirement；
- output ownership；
- RequestBinding；
- provider/tool adapter declarations；
- taint state；
- commitment basis；
- ReceiptLink pin；
- Trust/Taint subject, dimension/kind, issuer/policy explicitness；
- Taint channel / precision vocabulary；
- sanitization discharge semantic evidence boundary；
- local/external reference explicitness and address form；
- accepted output / ModelOutput / OutputItem ownership and kind；
- ToolExecution / ToolResult ownership；
- EffectObservation evidence basis；
- ToolDecision subject；
- CaptureDiagnostic scope；
- Derivation partial/region/many-to-one contributor semantics；
- attempt-scoped / invocation-scoped RequestSnapshot boundaries；
- request preparation level ordering；
- binding occurrence / partial source scope；
- proposal-to-invocation explicit lineage；
- redaction Transform/Derivation lineage；
- Provider request snapshot-or-diagnostic behavior；
- Tool argument rewrite effective value；
- effect capability / bounded proposition / separate observation / external attestation；
- explicit ToolInvocation capture degradation；
- non-1:1 proposal→invocation cardinality；
- verifier profile dispatch / resolver evidence / key-relative signature / resolver attribution。

### 9.6 semantic verifier

这是下一阶段最大的工作量。

总计：

~~~text
771 requirements
~~~

主要包含：

- reference resolution；
- graph invariants；
- immutable identity；
- exact/partial provenance；
- request inclusion；
- retry/failover semantics；
- trust/taint propagation；
- privacy capability downgrade；
- Receipt completeness/conflict；
- claim composition；
- verifier reporting boundaries；
- prohibited inference。

---

## 10. Conformance Harness 架构

目录：

`conformance/v0.1/`

已经定义：

- `README.md`
- `RUNNER-CONTRACT.md`
- suite manifest；
- case schema；
- case-index schema；
- expected-result schema；
- harness-input schema；
- deterministic-vector schema；
- 16 个 family index；
- cases；
- expected results；
- audit files。

Runner phase 顺序：

~~~text
1. schema_validate
2. resolve_references
3. graph_checks
4. representation_checks
5. privacy_checks
6. integrity_checks
7. claim_checks
8. aggregate_report
~~~

Golden result 不比较：

- free-text message；
- implementation-generated finding ID；
- independent finding ordering；
- human-readable formatting。

Golden result 比较的是规范性 status、subject、evidence basis、prohibited inference 等 bounded matcher。

---

## 11. 当前仓库交付资产

### 11.1 规范

`spec/`

包含：

- Foundations；
- Part A-H；
- Threat Model；
- Claims；
- Terminology；
- Provider Adapter Contract；
- Tool Adapter Contract；
- Verifier Contract。

### 11.2 Frozen wire format

`schema/v0.1/`

包括：

- primitive/reference/representation；
- core/source/transform/request/model/tool；
- trust-taint/privacy/adapter；
- records/receipt/verifier/top-level schema；
- manifest；
- semantic-check boundary；
- freeze audit。

### 11.3 Fixtures

`fixtures/v0.1/`

用于 frozen Schema 与基础 semantic/crypto separation。

### 11.4 Deterministic vectors

`vectors/v0.1/`

用于 integrity/privacy algorithm behavior 与 scenario baseline。

### 11.5 Traceability

`traceability/v0.1/`

907 条 requirement 的：

~~~text
requirement
→ planned test
→ enforcement layer
→ target schema/vector
~~~

映射。

### 11.6 Conformance Suite

`conformance/v0.1/`

当前正在扩展为：

~~~text
requirement
→ case
→ materialized input
→ execution phases
→ expected normalized result
→ independent runner acceptance
~~~

---

## 12. 当前不可做的事情

在 Conformance Suite Gate 通过之前，不应把以下工作视为正式解锁：

### Product Independent Verifier implementation

仍然 BLOCKED。

原因：Verifier Contract 已冻结，但 907 条 requirement 的 executable acceptance suite 尚未完成。

### SDK implementation

仍然 BLOCKED。

原因：SDK 在完整 conformance suite 前实现，会把尚未机械覆盖的语义重新编码进代码，增加 spec/schema/implementation drift 风险。

### Schema 随意修改

v0.1 Schema 已冻结。

不能为了让一个 case “好写”而随意修改 frozen Schema。

如果发现真正 freeze-breaking defect，必须：

1. 证明它是 frozen wire format defect，而不是 case/harness/verifier 错误；
2. 记录 impact；
3. 明确是否需要 reopen v0.1 freeze 或进入新 schema version/profile；
4. 不得静默修改。

---

## 13. 下一阶段实施路线

### Stage C1 — direct_schema

状态：

> DONE / ACCEPTED

### Stage C2 — deterministic vectors

状态：

> MATERIALIZATION COMPLETE / ACCEPTANCE PENDING

~~~text
43 / 43 executable
0 remaining
~~~

全部 deterministic requirements 已有可独立重算的向量与 exact normative expectations。下一步等待独立 runner 与后续 cross-language normalized equivalence acceptance。

### Stage C3 — mixed_schema_semantic

状态：

> MATERIALIZATION COMPLETE / ACCEPTANCE PENDING

~~~text
87 / 87 executable
0 remaining
~~~

全部 mixed-schema-semantic requirements 已覆盖适用 JSON Schema 层与 semantic verifier 层。下一步等待独立 runner 与后续 cross-language normalized equivalence acceptance。

### Stage C4 — semantic_verifier case materialization

为 771 条 requirement 建立可执行输入与 normative finding matcher。

建议按语义波次推进：

1. reference / identity / graph；
2. Source / Derivation；
3. Request；
4. Model retry/output；
5. Tool/effect；
6. Trust/Taint；
7. Privacy；
8. Receipt/Integrity；
9. Adapter diagnostics；
10. Verifier composition/reporting。

### Stage C5 — Cross-language runner

需要至少两个独立实现对同一套 case/golden result 得到 equivalent normalized result。

Runner 是测试基础设施，不等于 Product Independent Verifier。

### Stage C6 — Final Conformance Gate

Gate 条件：

- 907/907 cases accepted；
- 所有 case input 可 deterministic materialize；
- 所有 expected result 可 machine compare；
- deterministic vectors independently recomputable；
- mixed cases 覆盖 schema + semantic；
- cross-language normalized results equivalent；
- 不依赖 free-text、动态 finding ID、未规定顺序；
- suite manifest 状态切换为 accepted。

---

## 14. Conformance Gate 之后的开发路线

Gate 通过后，才进入正式实现：

### Stage D — Independent Verifier

优先实现：

- Receipt/Resolution Set loading；
- frozen Schema resolution；
- reference resolution；
- graph invariants；
- representation/commitment verification；
- privacy capability handling；
- JCS/SHA-256/Ed25519；
- typed VerificationFinding；
- conflict/completeness；
- VerificationReport；
- CLI inspect/verify。

### Stage E — SDK

优先 Python SDK：

- object builders；
- immutable IDs；
- provenance graph recording；
- Receipt packaging；
- privacy descriptors；
- integrity envelope；
- conformance self-test integration。

### Stage F — Adapters

建议顺序：

1. OpenAI-compatible provider adapter；
2. Anthropic provider adapter；
3. function tool adapter；
4. MCP tool adapter。

### Stage G — Observability export

在不改变核心协议语义的前提下，再考虑：

- OpenInference；
- OTLP；
- JSONL transport/export。

---

## 15. v0.1 明确不做什么

C2ATrace v0.1 不是：

- agent runtime；
- workflow engine；
- dashboard/SaaS；
- vector database；
- model gateway；
- prompt injection detector；
- authorization engine；
- policy decision engine；
- model-internal causal attribution system；
- external-world OutcomeVerification system；
- Proof-of-Done system。

不要把这些功能重新塞进 core protocol。

---

## 16. 主要工程风险

### 16.1 907-case 规模

最大风险已经从“语义不清”转为“conformance materialization 规模”。

缓解方式：

- wave-based generation；
- family index；
- schema-validated case format；
- normalized expected result matcher；
- automated audit。

### 16.2 semantic verifier case explosion

771 条 semantic requirements 不应变成 771 套互不相关的手写 harness。

应优先抽取可复用 scenario primitives：

- missing/ambiguous reference；
- duplicate ID；
- cycle；
- representation mismatch；
- partial receipt；
- conflicting assertions；
- unsupported profile；
- missing capability；
- tampered payload；
- retry uncertainty。

### 16.3 cross-language canonicalization

重点风险：

- RFC 8785 实现差异；
- JSON number handling；
- base64url padding；
- Ed25519 key encoding；
- JSON Pointer；
- Unicode scalar offsets。

必须用 golden vectors 锁死。

### 16.4 privacy capability leakage

HMAC key 只属于 verifier harness capability，不得进入 historical Receipt 或 ordinary VerificationFinding。

### 16.5 claim strengthening

实现者最容易错误输出：

~~~text
TRUE
PROVEN
SAFE
TRUSTWORTHY
CAUSED
COMPLETE
FULLY VERIFIED
~~~

除非某个 profile 明确定义了对应的更强语义，否则应继续使用 typed bounded wording。

---

## 17. 接管时必须遵守的维护规则

1. 不根据时间戳覆盖显式 provenance dependency。
2. 不把缺失 edge 当成否定证明。
3. 不从相同内容/hash 推导相同 identity。
4. 不把 capability declaration 当成 occurrence capture proof。
5. 不把 signature valid 当成 record true。
6. 不把 ToolResult success 当成 Effect true。
7. 不把 EffectObservation 当成 desired outcome verified。
8. 不让 privacy omission 升级 claim。
9. 不让 sanitizer 擦除 upstream provenance。
10. 不为实现方便重新引入整体 `fully_verified` boolean。
11. 每次 protocol-level MUST/MUST NOT 必须继续映射到 conformance case。
12. frozen Schema 变更必须走明确 freeze-breaking/versioning 流程。

---

## 18. 项目验收定义

### 已验收

- semantic model；
- adapter contracts；
- verifier contract；
- 907 requirement traceability；
- v0.1 JSON Schema Freeze；
- direct_schema conformance layer。

### 部分完成

- mixed_schema_semantic conformance；
- deterministic_vector conformance；
- semantic_verifier case materialization；
- expected Finding golden files。

### 未验收

- complete 907-case suite；
- cross-language conformance；
- Product Independent Verifier；
- SDK；
- provider/tool production adapters。

---

## 19. 下一位负责人应立即做什么

当前最合适的执行顺序：

~~~text
1. 建立 semantic_verifier reusable scenario primitives
2. 批量 materialize 771 semantic_verifier cases
3. 完成 expected VerificationFinding matcher
4. 实现独立 conformance runner A
5. 实现第二语言 runner B
6. 执行 deterministic_vector / mixed acceptance
7. 907/907 acceptance audit
8. Conformance Suite Gate
9. 解锁 Product Independent Verifier
10. 解锁 SDK
~~~

不要跳过第 7-8 步直接开始 SDK。

---

## 20. 当前状态一句话

> C2ATrace v0.1 的语义、adapter/verifier contracts 与 wire format 已经冻结；项目当前的主要工作不再是“设计协议”，而是把 907 条 normative requirements 全部转化为可跨语言执行和独立复现的 conformance evidence。

---

## 21. 交付判定

本交付包对应的是：

> **Specification + Frozen Schema + Traceability + In-Progress Conformance Suite handoff**

不是：

> production SDK / production verifier handoff。

接手方可以安全继续 Conformance Suite，但在 Gate 通过前不应宣称 v0.1 implementation-ready。
