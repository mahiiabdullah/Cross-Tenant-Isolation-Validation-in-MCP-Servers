# 11 — Sandboxing (WASM, gVisor, Firecracker, OS Process Isolation)

> Concept 11 of 14.
> rubric. Concept coverage: **Architecture** macro-category.

## (A) Formal Definition

**Sandboxing** is the practice of executing untrusted code in a
restricted environment that limits the code's access to system
resources. Four instantiations are relevant to MCP server
deployments:

- **WebAssembly (WASM).** A portable bytecode format executed in a
  sandboxed VM. Standards: **W3C WebAssembly Core Specification**
  (W3C, 2024 draft; specific revision requires empirical
  verification); **WebAssembly System Interface (WASI) Preview 2**
  (Bytecode Alliance).
- **gVisor.** Google's userspace kernel that intercepts application
  syscalls and re-implements them in userspace. Reference: **"gVisor:
  Protecting Google Cloud Users from Kernel Exploits"** (Lacasse,
  2018; published at USENIX ; specific bib entry requires empirical
  verification).
- **Firecracker.** Amazon's micro-VMM optimised for multi-tenant
  workloads. Reference: **"Firecracker: Lightweight Virtualization
  for Serverless Applications"** (Agache et al., NSDI 2020).
- **OS process isolation.** Traditional POSIX process isolation with
  UID / GID / namespace / seccomp / cgroups; classic UNIX security
  model with modern Linux extensions.

The security literature also references **Capsicum** (FreeBSD
capabilities), **Landlock** (Linux), and **eBPF** (Linux) as
complementary sandboxing primitives.

## (B) Threat Model

- **Attacker position.** Untrusted code executing in the MCP
  server's address space or on the same host — e.g. a tool handler
  written by a tenant, a dynamic plugin, or a malicious dependency.
- **Assets.** The host operating system; the host's file system;
  other tenants' processes and data; the kernel itself.
- **Preconditions.** (i) Untrusted code runs in the same process
  as trusted code. (ii) The OS-level isolation is misconfigured
  (e.g. shared UID, no seccomp filter, no namespace isolation).

## (C) Real-World / Theoretical Example

An MCP server allows tenants to register custom tool handlers
written in arbitrary Python. Tenant X uploads a handler that calls
`subprocess.run(["cat", "/etc/passwd"])`. Without sandboxing, the
handler reads the host's password file, leaking information about
the host's users — including other tenants' service accounts. A
gVisor- or Firecracker-sandboxed deployment would confine the
handler's syscalls.

## (D) Standard Defenses

- **WASM execution of untrusted handlers.** Compile tenant-supplied
  logic to WASM; enforce WASI capability-based access.
- **Micro-VM per tenant.** Firecracker micro-VM per tenant with
  minimal guest kernel and minimal API surface.
- **gVisor user-space kernel.** Intercept all syscalls in
  userspace, eliminating direct kernel exposure.
- **Seccomp / AppArmor / SELinux.** Mandatory access control on
  per-process syscalls and file access.
- **Linux namespaces.** PID, network, mount, UTS, IPC, and user
  namespaces isolate tenants' views of the OS.
- **cgroups.** Resource limits per tenant (CPU, memory, IOPS,
  PIDs).

## (E) Open Research Problems

- **Performance overhead.** gVisor and Firecracker add measurable
  latency; the overhead in MCP-tool-dispatch latency has not been
  characterised.
- **Side-channel leakage.** Even with sandboxing, timing,
  cache-line, and TLB side channels can leak information across
  sandboxes.
- **Granular resource accounting.** Per-tenant I/O accounting under
  cgroups is approximate; budget enforcement can be defeated.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `transport`, `session`.
- **MCP primitive.** Process model (one process per tenant vs
  shared worker); OS-level isolation around the server.
- **Phase-1 ticket cross-references.**
  - `A-TRN-005` — cross-tenant impersonation via shared stdio
    worker (a shared stdio worker is a sandboxing failure).
  - `A-SES-002` — post-restart session reuse (a fresh-process
    restart without fresh session ID is a sandboxing-policy gap).
- **Source.** `docs/notes/mcp_learning/01_transport.md` §D–E,
  `06_sessions.md` §D–E.