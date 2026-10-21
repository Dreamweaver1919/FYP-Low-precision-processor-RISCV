# FYP Low-Precision Processor RISC-V — GitHub 发布规格

日期：2026-10-21  
目标远程仓库：`https://github.com/Dreamweaver1919/FYP-Low-precision-processor-RISCV`

## 目的与受众

把当前 FYP 工作目录整理为可公开阅读、可本地复现、适合毕业答辩和代码审阅的 GitHub 仓库。受众是项目导师、答辩评审和具备 RISC-V/Vivado 背景的开发者。

仓库应使读者能够理解：项目从 CV32E40P 冻结基线出发，加入了哪些 XpulpNN DATE-2020 范围内的低精度指令与量化机制，怎样验证功能与 FPGA OOC 时序，以及哪些结论尚未达到板级证明。

## 发布范围

提交以下内容：

- `rtl/`：核心覆盖层、独立 NN 执行模块、FPGA system wrapper；
- `verification/`：独立软件模型、CPU 程序、SystemVerilog 测试平台、构建与运行脚本、静态配置；
- `scripts/`：独立 Vivado 工程生成和 OOC 脚本；
- `docs/`：本地 ABI 规格、论文分析、验证索引、基准比较、独立审查和最终验证报告；
- `vendor/cv32e40p/`：已冻结的上游来源快照、原始许可证、来源哈希；
- 精简的 `artifacts/`：源码完整性/差异补丁、最终 release evidence、共同 benchmark ROM 与机器可读的验证、基准和 FPGA 汇总；
- 原 `FYP.xpr`：仅作为项目开始时的参照工程，连同 README 中的 SHA-256；
- 顶层 README、许可证说明、贡献说明、GitHub Actions 的只读 Python 验证。

不提交以下内容：

- Vivado `FYP.cache/`、`FYP.hw/`、`FYP.ip_user_files/`、`FYP.runs/`、`FYP.sim/` 及临时 XSim 目录；
- DCP、bitstream、Vivado/XSim log、`.jou`、`.pb`、生成的 ELF/map/disassembly、逐次运行目录和 Python bytecode；
- 包含本机绝对路径或可从脚本生成的大型工件。

未提交的完整历史日志和 DCP 仍保留在本机工作区；公开仓库保留可验证的摘要、固定共同 ROM 和重建入口。

## 目录与根文件

```text
rtl/                         HDL 实现
verification/                模型、软件、TB、运行脚本与配置
scripts/                     Vivado Tcl
docs/                        规格、调查和可审阅结果
vendor/cv32e40p/             上游冻结来源和许可
artifacts/delivery/          manifest、overlay patch、release evidence
artifacts/verification/      summary、benchmark comparison、固定 ROM
artifacts/fpga/summary.json  路由资源和时序摘要
.github/workflows/verify.yml Python 模型和来源完整性 CI
README.md                    发布说明和复现入口
LICENSE                      本项目文件的许可声明
THIRD_PARTY_NOTICES.md       上游来源、许可证与边界
CONTRIBUTING.md              复现与贡献约定
.gitignore                   生成工件和本机目录排除规则
```

`README.md` 应直接介绍目标、架构、实现范围、快速验证、可选 Vivado 重建、已验证性能/时序和边界。其内容以现有 `README-xpulpnn.md`、最终验证报告及验证索引为事实来源，但不保留依赖本机路径才能理解的说明。

## 许可证与来源

本项目新建的文件采用 Apache-2.0，前提是其内容未复制受上游不同许可约束的代码。`vendor/cv32e40p/` 与其递归 vendor 内容保留原始许可证和版权头，且不重新许可。顶层 `THIRD_PARTY_NOTICES.md` 指向其来源清单、原 CV32E40P 来源及每个适用许可证。

原 `FYP.xpr` 的 SHA-256 必须保持：

`9d348bcda279dbd563006ed12d1ae816f06b0ff66022e54145c753f7af3f0e82`

发布前必须运行现有来源完整性检查，确认冻结的 140 个来源文件和该 XPR 未变化。

## 可复现性与 CI

GitHub Actions 只运行不需要 Vivado、XSim 或本机 RISC-V 工具链的 Python unit suite：

```text
python -m unittest discover -s verification/tests -v
```

CI 成功意味着模型、编码、来源哈希和发布输入检查通过；它不宣称 RTL 仿真或 FPGA 时序在 GitHub runner 上完成。README 给出 Windows 本地环境下的 XSim/Vivado 重建命令，并说明需自行配置工具路径。

## 验收条件

1. `git status --ignored` 表明 Vivado/XSim 临时树、DCP、log 和用户本机缓存不被跟踪。
2. Git 索引中包含上述发布范围所需的 HDL、验证、文档、许可证和固定 ROM。
3. `python -m unittest discover -s verification/tests -v` 通过。
4. `README.md` 的仓库内链接可解析，不要求读者先打开本机 `C:` 绝对路径。
5. 运行 `verification/scripts/package_delivery.py` 成功，验证 141 项来源完整性和 ZIP CRC/member hash。
6. 首次提交具有清晰的发布说明，并推送到指定的空 GitHub 仓库；推送失败时保留本地提交，不覆盖远程内容。

## 结果边界

发布的结论是：功能回归通过；核心与 system wrapper 的 20 ns（50 MHz）OOC 时序通过；扩展核的 10 ns OOC 未闭合。OOC 不代表 KV260 板卡引脚、时钟连接、bitstream、硬件运行或功耗已验证。性能数字说明本项目的 local legacy dot8 与 native kernel，不等同于论文作者的优化 baseline 或普适加速比。
