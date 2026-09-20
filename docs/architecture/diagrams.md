# Diagrams

## Host roles

```mermaid
flowchart LR
  air[M3 Air\nhuman]
  m1[M1 mini\ncontrol]
  st[Studio\ncompute]
  air -->|Tailscale SSH / UI| m1
  air -->|Tailscale SSH / Jupyter client| st
  m1 -->|jobs / route| st
```

## Trust zones

```mermaid
flowchart TB
  subgraph public [Public Internet]
    gh[GitHub]
    cloud[Optional LLM APIs]
  end
  subgraph tailnet [Tailscale - untrusted for app auth]
    m1[M1 services]
    st[Studio Ollama]
    air[Air clients]
  end
  subgraph loopback [Host loopback]
    local[127.0.0.1 publishes]
  end
  air --> m1
  air --> st
  m1 --> st
  m1 --> gh
  st --> cloud
```

## Work-order states

```mermaid
stateDiagram-v2
  [*] --> created
  created --> queued
  created --> cancelled
  queued --> running
  queued --> cancelled
  running --> awaiting_approval
  running --> completed
  running --> failed
  running --> queued: retry
  awaiting_approval --> running: approved
  awaiting_approval --> cancelled
  awaiting_approval --> failed
  failed --> queued: retry
  failed --> [*]
  completed --> [*]
  cancelled --> [*]
```
