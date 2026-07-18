sequenceDiagram
    participant FW as Framework / Scheduler
    participant PG as PayloadGenerator
    participant CA as Connector (Tenant A)
    participant CB as Connector (Tenant B)
    participant SRV as MCP Server (dummy or real)
    participant EV as Evaluator (Oracle)
    participant LG as EventLogger
    participant MC as Metrics Collector

    FW->>PG: generate(recipe, seed=42)
    PG-->>FW: payload (JSON, contains marker)
    FW->>CA: call_tool("echo", args=payload)
    CA->>SRV: JSON-RPC tools/call (Tenant A token)
    SRV-->>CA: result_A
    CA-->>FW: result_A
    FW->>CB: read_resource(uri=/victim)
    CB->>SRV: JSON-RPC resources/read (Tenant B token)
    SRV-->>CB: result_B (may contain payload)
    CB-->>FW: result_B
    FW->>EV: evaluate([call_A, call_B], tenants={A,B})
    EV->>EV: substring + sha256-prefix match on marker
    EV-->>FW: [LeakageEvent] or []
    FW->>LG: emit({event_type: "call", ...})
    FW->>LG: emit({event_type: "leakage", ...})
    LG-->>FW: ok
    FW->>MC: compute_metrics(events)
    MC-->>FW: [MetricResult(leakage_rate, time_to_leak_ms, defense_overhead_ms, utility_retention)]
    FW->>FW: Reporter.render(metrics, events) -> report.md + report.html