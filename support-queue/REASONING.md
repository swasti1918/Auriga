# Reasoning and Design Decisions

## 1. Understanding the Problem

The main challenge is not simply displaying support tickets. The important requirement is deciding which ticket should appear first.

The helpdesk receives tickets with different priorities and agreed response times. Therefore, the application needs a deterministic queue-ordering rule.

## 2. Queue Ordering

I used the following ordering:

1. Overdue unresolved tickets
2. Urgent tickets
3. Normal tickets
4. Earlier response deadlines
5. Earlier creation time as a tie-breaker

This provides a predictable ordering and prevents the helpdesk team from having to manually scan the entire ticket list.

## 3. Why Overdue Tickets Are Surfaced

A ticket that has already passed its promised response time requires attention because the agreed response window has already been missed.

The application therefore calculates whether:

```text
response_due < current_time
```

## 4. Why Priority Is Separate From Deadline

Priority and deadline represent different pieces of information.

For example:

- An urgent ticket may have 30 minutes remaining.
- A normal ticket may already be overdue.

The system therefore tracks both attributes instead of treating priority as the only ordering factor.

## 5. Search and Filters

The helpdesk also needs to find specific tickets quickly.

The application therefore provides:

- Customer/ticket search
- Status filter
- Assignee filter

This reduces the need to manually scan a large queue.

## 6. Assignment

A small helpdesk needs to know who is responsible for each ticket without requiring the customer or ticket creator to choose an owner.

New tickets are automatically assigned to the least-loaded unresolved team member. The assignment can still be changed later by an operator when needed.

## 7. Persistence

SQLite was selected because it is lightweight and does not require a separate database server.

Tickets remain available after restarting the Streamlit application.

## 8. Technology Choice

Python and Streamlit were selected because they allow the application to be developed quickly while providing a usable browser-based interface.

SQLite was used for storage and Pandas was used for convenient ticket filtering and sorting.

## 9. Scope

The implementation focuses on the core helpdesk workflow:

Create → Prioritize → Queue → Assign → Update → Resolve

Features such as authentication, email notifications and multi-team support were intentionally left outside the MVP because the primary requirement is reliable queue ordering.
