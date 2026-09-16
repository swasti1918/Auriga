# Reasoning and Design Decisions

## 1. Problem Understanding

The main challenge is not simply displaying support tickets. The goal is to help a small IT helpdesk quickly identify which unresolved ticket needs attention first.

Each ticket can have a different priority, response deadline, status, and assigned support agent. Therefore, the application needs a deterministic queue-ordering strategy instead of relying on manual scanning.

The main design goal is:

> The most pressing unresolved ticket should always be visible at the top of the queue.

The system also needs to reduce manual work by automatically assigning tickets and escalating tickets when their agreed response time is breached.

---

## 2. Queue Ordering

The queue uses the following ordering rules:

1. Overdue unresolved tickets
2. Urgent tickets
3. High-priority tickets
4. Normal-priority tickets
5. Earlier response deadlines
6. Earlier creation time as a tie-breaker

The priority hierarchy is:

```text
Urgent > High > Normal