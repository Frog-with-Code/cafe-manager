```mermaid
---
config:
  layout: elk
---

stateDiagram-v2
    [*] --> AVAILABLE
    
    AVAILABLE --> RESERVED : reserve(people_amount)
    
    RESERVED --> OCCUPIED : occupy()
    
    OCCUPIED --> AVAILABLE : free()
```