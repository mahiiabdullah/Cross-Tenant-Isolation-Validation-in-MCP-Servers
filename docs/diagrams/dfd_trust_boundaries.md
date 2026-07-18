%% DFD — Trust Boundaries for MCP Isolation Research
%% Phase 5 deliverable. Renders to dfd_trust_boundaries.svg.
%% See docs/02_Threat_Model.md and docs/04_Attack_Taxonomy.md.

flowchart TB
    subgraph External["External Entities"]
        TA["Tenant A<br/>(Honest or Malicious)"]
        TB["Tenant B<br/>(Honest or Malicious)"]
        NA["Network Adversary<br/>(passive / active MITM)"]
    end

    subgraph Host["Orchestrator / LLM Host"]
        ORC["Orchestrator<br/>(Client SDK + Model)"]
    end

    subgraph Server["MCP Server (trust boundary under study)"]
        AUTH["Auth Layer<br/>token verify, principal binding"]
        SESS["Session Manager<br/>session_id -> principal"]
        NS["Namespace / Tool Registry"]
        TOOL["Tool Dispatcher"]
        RES["Resource Resolver"]
        MEM["Memory Store"]
        CCH["Cache Layer"]
    end

    subgraph Stores["Persistent Stores"]
        DB["Session Store<br/>(tenant_id, session_id)"]
        CDB["Cache Store<br/>Redis / in-proc LRU"]
        MEMDB["Memory Store<br/>embeddings + logs"]
        FS["Resource FS<br/>/srv/data/{tenant}/..."]
    end

    %% Trust boundary edges (dashed red)
    TA -. "TB-1: Tenant to Orchestrator<br/>(browser CORS / IPC)" .-> ORC
    TB -. "TB-1: Tenant to Orchestrator" .-> ORC
    NA -. "TB-2: On-path on Transport<br/>(cleartext HTTP+SSE)" .-> ORC
    ORC -. "TB-3: Transport<br/>(stdio / HTTP+SSE / streamable HTTP)" .-> AUTH

    %% Inter-server trust boundary (inter-tenant implicit)
    TOOL -. "TB-4: Inter-tenant implicit boundary<br/>(shared registry / scratchpad / cache)" .-> TOOL

    %% Server -> Stores trust boundary
    AUTH -. "TB-5: Server to Stores<br/>(per-tenant key prefix mandatory)" .-> DB
    CCH  -. "TB-5: Server to Stores" .-> CDB
    MEM  -. "TB-5: Server to Stores" .-> MEMDB
    RES  -. "TB-5: Server to Stores" .-> FS

    %% Data-flow edges (solid black)
    ORC --> AUTH
    AUTH --> SESS
    SESS --> NS
    SESS --> TOOL
    SESS --> RES
    NS --> TOOL
    TOOL --> CCH
    TOOL --> MEM
    RES --> FS
    SESS --> DB

    classDef trustBoundary stroke:#c00,stroke-width:2px,stroke-dasharray:6 4,fill:#fff5f5
    classDef process fill:#eef,stroke:#333,stroke-width:1px
    classDef store fill:#efe,stroke:#333,stroke-width:1px
    classDef external fill:#ffe,stroke:#333,stroke-width:1px

    class TB-1,TB-2,TB-3,TB-4,TB-5 trustBoundary
    class AUTH,SESS,NS,TOOL,RES,MEM,CCH,ORC process
    class DB,CDB,MEMDB,FS store
    class TA,TB,NA external