```mermaid
---
config:
  layout: elk
---

stateDiagram-v2
    [*] --> FREE
    
    FREE --> BUSY : work()
    
    BUSY --> FREE : rest()
```