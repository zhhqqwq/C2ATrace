# C2ATrace v0.1 项目交接检查清单

状态：CURRENT HANDOFF CHECKLIST  
适用阶段：Frozen Schema → Conformance Suite

## A. 接管前确认

- [ ] 阅读根目录 `README.md`。
- [ ] 阅读 `delivery/v0.1/PROJECT-DELIVERY-PACKAGE.md`。
- [ ] 阅读 `spec/README.md`。
- [ ] 阅读 `schema/v0.1/FREEZE-AUDIT.md`。
- [ ] 阅读 `traceability/v0.1/manifest.json`。
- [ ] 阅读 `conformance/v0.1/README.md`。
- [ ] 阅读 `conformance/v0.1/RUNNER-CONTRACT.md`。
- [ ] 阅读 `conformance/v0.1/manifest.json`。

## B. 当前冻结边界

接管人必须确认：

- [ ] v0.1 Schema 状态是 FROZEN。
- [ ] 907 条 normative requirements 已全部映射。
- [ ] Conformance Suite 尚未完成。
- [ ] Product Independent Verifier 尚未解锁。
- [ ] SDK 尚未解锁。
- [ ] 不以“实现方便”为理由静默修改 frozen Schema。

## C. 当前 Conformance 进度

当前基线：

~~~text
requirements / mapped cases      907 / 907
executable cases                 501
accepted cases                     6

direct_schema                     6 / 6 accepted
mixed_schema_semantic            87 / 87 executable
deterministic_vector             43 / 43 executable
semantic_verifier               365 / 771 executable
~~~

- [ ] 继续工作前重新读取 manifest，避免使用过期数字。
- [ ] 新 case ID 必须保持全局唯一。
- [ ] requirement ID 与 planned-test ID 必须同时保留。
- [ ] 不因为 planned-test 名称相同而合并 requirement。

## D. Case materialization 规则

每个 executable case 必须具备：

- [ ] requirement mapping；
- [ ] planned-test mapping；
- [ ] deterministic input；
- [ ] 明确 execution phases；
- [ ] expected-result document；
- [ ] normative matcher；
- [ ] harness self-check；
- [ ] index status 更新。

Mixed case 还必须：

- [ ] 覆盖适用 JSON Schema 层；
- [ ] 覆盖 semantic verifier 层。

Deterministic vector case 还必须：

- [ ] 可独立重算；
- [ ] 正负例行为明确；
- [ ] 不依赖实现私有状态。

## E. Golden result 规则

Golden result 不得依赖：

- [ ] free-text message；
- [ ] implementation-generated finding ID；
- [ ] independent finding ordering；
- [ ] human-readable renderer；
- [ ] 未规定的 object-key ordering。

Golden matcher 只比较规范性字段，例如：

- status；
- domain；
- subject/scope；
- evidence basis；
- prohibited inference；
- process outcome。

## F. 必须保持的语义边界

接管过程中禁止引入以下错误简化：

- [ ] Signature valid → record true。
- [ ] Signature valid → capture complete。
- [ ] ToolResult success → Effect true。
- [ ] EffectObservation → Outcome verified。
- [ ] ToolProposal → ToolExecution。
- [ ] allow → executed。
- [ ] missing edge → relation did not exist。
- [ ] same content/hash → same identity。
- [ ] sanitized → trusted。
- [ ] tainted → malicious。
- [ ] fully resolved Resolution Set → complete global history。
- [ ] overall fully_verified boolean。

## G. 推荐执行顺序

- [x] 完成 deterministic_vector materialization（43 / 43 executable；runner acceptance pending）。
- [x] 完成 mixed_schema_semantic materialization（87 / 87 executable；runner acceptance pending）。
- [x] 建立 semantic primitive catalog + 771/771 coverage matrix（21 primitive families；Wave 01 foundation materialized）。
- [ ] 继续批量 materialize semantic_verifier cases（当前 365 / 771 executable）。
- [ ] 完成 expected VerificationFinding matcher。
- [ ] 实现 conformance runner A。
- [ ] 实现独立第二语言 runner B。
- [ ] 对 907 cases 做 normalized cross-language comparison。
- [ ] 完成 Final Conformance Audit。
- [ ] 将 suite manifest 切换到 accepted。
- [ ] 之后才解除 Product Verifier / SDK block。

## H. Freeze-breaking defect 处理

如果发现 frozen Schema 可能存在错误：

1. [ ] 先证明不是 case/harness/verifier 实现错误。
2. [ ] 给出最小复现。
3. [ ] 对照 normative requirement。
4. [ ] 记录影响的 fixture/case/vector。
5. [ ] 判断是否必须 reopen freeze 或新建版本/profile。
6. [ ] 未完成以上步骤前不得直接修改 v0.1 wire format。

## I. 正式交付完成判据

当前交付属于：

> Specification + Frozen Schema + Traceability + In-Progress Conformance Suite

只有当：

~~~text
907 / 907 accepted
+
cross-language normalized equivalence
+
final conformance audit PASS
~~~

才可进入下一交付级别：

> Implementation-Ready Protocol Baseline
