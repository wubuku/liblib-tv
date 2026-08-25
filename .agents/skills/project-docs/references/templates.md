# Document Templates

## README.md Template

```markdown
# {Project Name}

> {One-line description} | {3-5 keywords} | {Tech stack highlight}

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

{Extended description (2-3 sentences explaining the value proposition).}

## Features

- ✨ **{Feature 1}**: {Brief explanation}
- 🚀 **{Feature 2}**: {Brief explanation}
- 🔌 **{Feature 3}**: {Brief explanation}
- 📊 **{Feature 4}**: {Brief explanation}

## Quick Start

### Prerequisites

- {Technology} {version}+
- {Technology} {version}+
- {Technology} {version}+

### Installation

```bash
# Clone the repository
git clone https://github.com/{owner}/{repo}.git
cd {repo}

# Build
{build_command}

# Run
{run_command}
```

## Documentation

| Document | Description |
|----------|-------------|
| [AGENTS.md](AGENTS.md) | AI Agent navigation |
| [MEMORY.md](MEMORY.md) | Quick reference |
| [docs/](docs/) | Full documentation |

## License

{License} - see [LICENSE](LICENSE)
```

---

## AGENTS.md Template

```markdown
# {Project Name} — Agent Navigation

## 1. Project Overview
- Type: (e.g., BFF API / SDK / Data pipeline)
- Tech stack: (languages, frameworks, key infra)
- Status: (PoC / dev / production)

## 2. Documentation Index
- [AGENTS.md](AGENTS.md) — You are here
- [MEMORY.md](MEMORY.md) — Quick reference
- [README.md](README.md) — Human landing page
- [docs/](docs/) — Full documentation
- [.cursor/rules/](.cursor/rules/) — Cursor Rules

## 3. Quick Commands

    build:  {command}
    test:   {command}
    lint:   {command}
    verify: {command}

## 4. Module Overview

| Module | Path | Responsibility |
|--------|------|----------------|
| api | src/api/ | Interfaces + DTOs |
| core | src/core/ | Business logic |

## 5. Agent Constraints

- **DO NOT** modify: (critical paths)
- **ALWAYS** verify after: (database migrations, API changes)
- **BEFORE** changing: (read relevant docs)

## 6. Maintenance

- New docs → update this file
- Doc issues → fix the doc, not this file
```

---

## MEMORY.md Template

```markdown
# MEMORY.md - 速查手册

> 日常开发、测试、巡检的快速参考。详细文档见：`docs/development-guides/` · `docs/technology-stack/` · `.cursor/rules/*.mdc`（AGENTS.md 索引）

## 核心工作流

1. **DDDML-First** → `dddml/` 目录，这是唯一数据源
2. **生成代码** → Docker 命令
3. **实现业务逻辑** → Service 层，使用生成的代码
4. **编译验证** → `mvn clean install -DskipTests`
5. **运行测试** → 通过后才算完成

## 关键命令

```bash
# DDDML 代码生成
docker run --rm -v .:/myapp wubuku/dddappp-java:master ...

# 编译
mvn clean install -DskipTests

# 测试
mvn test -pl dermai-service-rest -Dtest=<TestClass>
```

## 服务与端口

| 服务 | 端口 | 启动方式 |
|------|------|----------|
| api-service | 8091 | Maven run |
| rag-service | 8081 | 见下方 |
| PostgreSQL | 5432 | 本地 localhost |

## ⚠️ 高频注意事项

- **不要手动创建 DTO**：DDDML 生成是唯一来源
- **创建命令不设 version**，更新命令必须设 version
- **不要修改** `Abstract*State` 和 `Bff*Projection` 接口
- **Cursor Rules**：`.cursor/rules/*.mdc`，按编号索引
- **有问题先查** `docs/development-guides/` 和 `MEMORY.md`
```

---

## Cursor Rule Template (.mdc)

```yaml
---
name: rule-name
description: Brief description of what this rule enforces
applied_to: "**/*.java"  # Glob pattern for files this applies to
---

# Rule Name

## Purpose

What this rule enforces and why.

## Examples

### ✅ Correct

```java
// Example of correct usage
```

### ❌ Incorrect

```java
// Example of incorrect usage
```

## Exception Cases

- Case 1: When X, this rule does not apply
- Case 2: Y is allowed because Z
```

---

## docs/README.md Template

```markdown
# 文档导航

## 文档目录

| 目录 | 说明 |
|------|------|
| [development-guides/](development-guides/) | 开发指南 |
| [technology-stack/](technology-stack/) | 技术栈文档 |
| [api-testing/](api-testing/) | API 测试 |
| [operations-guides/](operations-guides/) | 运维指南 |
| [requirements-analysis/](requirements-analysis/) | 需求分析（可选） |
| [technical-documents/](technical-documents/) | 技术文档 |
| [drafts/](drafts/) | 草稿文档 |

## 快速导航

- [AGENTS.md](../AGENTS.md) — AI Agent 导航入口
- [MEMORY.md](../MEMORY.md) — AI 速查手册
- [.cursor/rules/](../.cursor/rules/) — Cursor Rules
```

---

## docs/drafts/README.md Template

```markdown
# 草稿文档

> 活跃迭代中的设计文档和实施计划。

## 命名规范

| 类型 | 模式 | 示例 |
|------|------|------|
| 设计文档 | `<topic>-design.md` | `go-sdk-design.md` |
| 实施计划 | `<component>-plan.md` | `spring-ai-plan.md` |
| 进度追踪 | `<component>-progress.md` | `api-progress.md` |

## 当前草稿

| 文件 | 说明 | 最后更新 |
|------|------|----------|
| [积分系统设计.md](积分系统设计.md) | 积分系统 DDDML 设计 | 2025-08-15 |

## 归档草稿

已完成的草稿移动到 [../archive/](../archive/)。
```

---

## docs/archive/README.md Template

```markdown
# 归档文档

> 历史文档，仅供参考，不再维护。

## 归档规则

1. 功能完全实现 + 设计稳定 2+ 周无变更 → 归档
2. 文件名加日期前缀：`YYYY-MM-DD_<原名>.md`

## 归档索引

| 日期 | 文件 | 说明 |
|------|------|------|
| 2025-08-15 | [2025-08-15_积分系统设计.md](2025-08-15_积分系统设计.md) | 已实现，移至正式文档 |
```

---

## CONTRIBUTING.md Template

```markdown
# Contributing to {Project Name}

Thank you for considering contributing! Please follow these guidelines.

## Development Setup

### Prerequisites

- {Technology} {version}+
- {Technology} {version}+
- Git

### Environment Setup

```bash
# 1. Fork and clone
git clone https://github.com/{your-fork}/{repo}.git
cd {repo}

# 2. Build and test
{build_and_test_commands}

# 3. Run application
{run_command}
```

## Code Standards

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `RagChatService` |
| Methods | camelCase | `embedDocument()` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT` |

## Testing Requirements

> ⚠️ **Tests are production code.** All PRs must pass tests.

```bash
# Run all tests
{test_command}

# Run specific test
{test_command} -Dtest=MyClassTest
```

## Commit Message Format

```
<type>(<scope>): <subject>

<body>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code restructuring
- `test`: Adding or updating tests

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch
3. **Write** code and tests
4. **Ensure** tests pass
5. **Commit** using conventional commits format
6. **Push** to your fork
7. **Open** a Pull Request

## Questions?

- 📖 Check [docs/](docs/) for documentation
- 🐛 Report bugs via [Issues](https://github.com/{owner}/{repo}/issues)
```

---

## Architecture Document Template

```markdown
# Architecture Design

## Design Principles

| Principle | Description |
|-----------|-------------|
| Principle 1 | Description |
| Principle 2 | Description |

## System Overview

```
┌─────────────────────────────────────┐
│           REST API                  │
├─────────────────────────────────────┤
│  Module 1 │ Module 2 │ Module 3     │
├─────────────────────────────────────┤
│           Core Services             │
├─────────────────────────────────────┤
│         Data Layer                  │
└─────────────────────────────────────┘
```

## Module Structure

| Module | Responsibility | Key Classes |
|--------|----------------|-------------|
| `module-api` | DTOs, interfaces | Request/Response DTOs |
| `module-core` | Core logic | Services, Managers |

## Core Patterns

### Pattern 1

```java
// Example code
```

## Database Design

### Key Tables

| Table | Purpose |
|-------|---------|
| `table_name` | Description |

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| X | Y | Because Z |
```

---

## Testing Guide Template

```markdown
# Testing Guide

> Tests are production code. Write tests alongside code. Tests must pass.

## Testing Pyramid

```
           ┌──────────┐
           │   E2E    │
           ├──────────┤
           │Integration│
           ├──────────┤
           │   Unit    │
           └──────────┘
```

## Quick Commands

```bash
# All tests
{test_command}

# Single module
{test_command} -pl module-name

# Single test class
{test_command} -Dtest=MyClassTest
```

## Unit Testing

### Structure

```java
class MyServiceTest {
    @Mock private MyRepository repository;
    @InjectMocks private MyService service;

    @Test
    void shouldDoXWhenY() {
        // given
        when(repository.findById(1L)).thenReturn(Optional.of(entity));

        // when
        Result result = service.doSomething(1L);

        // then
        assertThat(result.getValue()).isEqualTo("expected");
    }
}
```

## Integration Testing

```java
@SpringBootTest
@AutoConfigureMockMvc
class MyControllerIntegrationTest {
    // Test code
}
```

## Coverage Requirements

| Type | Target |
|------|--------|
| Instructions | ≥80% |
| Branches | ≥70% |
```

---

## Troubleshooting Document Template

```markdown
# Troubleshooting Guide

## Startup Issues

### Application Fails to Start

**Symptoms:**
- Error message or exception

**Diagnosis:**
```bash
# Check X
command_to_check
```

**Solutions:**
1. Step 1
2. Step 2

---

## Runtime Issues

### Problem Description

**Symptoms:**
- What users observe

**Cause:**
- Root cause

**Solution:**
- How to fix
```

---

## DOCUMENTATION_PLAN.md Template

```markdown
# Documentation Plan

## Current State Assessment

### Existing Documents
- [ ] List existing docs and their status

### Gaps Identified
- [ ] List documentation gaps

## Plan

### P0 (Foundation)
- [ ] Task 1
- [ ] Task 2

### P1 (Core Engineering)
- [ ] Task 3
- [ ] Task 4

### P2 (Detailed Guidance)
- [ ] Task 5
- [ ] Task 6

## Timeline

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Week 1 | P0 tasks | X hours |
| Week 2 | P1 tasks | Y hours |

## Dependencies

- Task 1 must complete before Task 3
- ...
```
