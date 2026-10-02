# Submission flow

A broker is the outside firm that sends an opportunity. The company is who the deal is about. The owner is the internal team member tracking that one submission. Contacts, documents, and notes belong to the submission, not to the broker. The app reviews records that already exist.

```mermaid
flowchart LR
  Broker["Broker<br/>outside firm"] -->|sends an opportunity| Submission
  Company["Company<br/>who the deal is about"] -->|is the subject| Submission
  Owner["Owner<br/>internal team member"] -->|tracks| Submission
  Submission --> Contacts["Contacts<br/>people at the company"]
  Submission --> Documents["Documents<br/>file references"]
  Submission --> Notes["Notes<br/>internal comments"]
```

An operator starts on the list, narrows it, then opens one record. The back link returns to the same filters.

```mermaid
flowchart TD
  List["List /submissions"] --> Filters["Filter by status, broker, or company"]
  Filters --> Rows["Each row shows company, broker, owner, counts, and the latest note"]
  Rows --> Detail["Open /submissions/id"]
  Detail --> Summary["Summary, status, priority, broker, and owner"]
  Detail --> Related["Contacts, documents, and notes"]
  Related --> Back["Back to the list with the same filters"]
```

A submission's status is `new`, `in_review`, `closed`, or `lost`. Priority is `high`, `medium`, or `low`.
