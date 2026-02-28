# Approach Generation Reference

Quick reference for generating fundamentally different approaches during explore mode.

## Principle: Vary on Fundamental Axes

Good exploration varies approaches on **fundamental axes**, not superficial differences.

**Good variation** (different axes):
- Modal vs Inline vs Full page (interaction pattern)
- Monolith vs Microservice vs Serverless (architecture)
- Sync vs Async vs Event-driven (communication)

**Bad variation** (same axis):
- Blue modal vs Green modal (just color)
- Redux vs Zustand (just implementation)
- PostgreSQL vs MySQL (just vendor)

---

## Frontend Approaches

### Interaction Patterns

| Pattern | When to Use | Pros | Cons | Scope |
|---------|-------------|------|------|-------|
| **Modal wizard** | Multi-step flows, focused tasks | Familiar, clear progress, blocks distractions | Interrupts context, mobile-unfriendly | M |
| **Inline expansion** | Quick edits, contextual actions | Stays in context, fast | Limited space, can clutter | S |
| **Side panel** | Detail views, forms alongside list | Persistent, good for compare | Takes screen real estate | M |
| **Full page** | Complex forms, dashboards | Maximum space, dedicated focus | Navigation required, context switch | M-L |
| **Command palette** | Power users, keyboard-first | Fast, discoverable, extensible | Learning curve, not for forms | S-M |
| **Progressive disclosure** | Complex features, onboarding | Clean initial view, gradual reveal | Hidden features, user confusion | M |
| **Drawer/sheet** | Mobile-first, quick actions | Mobile-native, swipeable | Limited on desktop | S |
| **Popover/tooltip** | Micro-interactions, hints | Lightweight, contextual | Limited space, positioning issues | S |

### Layout Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| **List/Detail** | Browsing + viewing items | Familiar, efficient | Limited to 2 levels |
| **Dashboard grid** | Multiple metrics, overview | Scannable, customizable | Overwhelming if too many |
| **Kanban** | Workflow, status tracking | Visual, drag-drop | Horizontal scroll, limited info |
| **Timeline** | Chronological data, activity | Clear sequence | Vertical scroll, dense |
| **Table** | Data-heavy, sortable/filterable | Dense info, familiar | Mobile-unfriendly |
| **Cards** | Visual items, mixed content | Scannable, flexible | Less dense than table |

### State Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| **Optimistic UI** | Fast feedback, low-risk actions | Feels instant | Rollback complexity |
| **Pessimistic UI** | Critical actions, high-risk | Accurate state | Feels slow |
| **Skeleton loading** | Content-heavy pages | Perceived performance | Extra UI work |
| **Streaming/partial** | Large data, real-time | Progressive reveal | Complexity |

---

## Backend Approaches

### Architecture Patterns

| Pattern | When to Use | Pros | Cons | Scope |
|---------|-------------|------|------|-------|
| **Extend existing** | Low risk, incremental change | Minimal disruption, fast | May not scale, tech debt | S |
| **New service** | Clear boundary, team ownership | Clean separation, independent deploy | Operational overhead | M-L |
| **Event-driven** | Async workflows, decoupling | Scalable, resilient | Eventual consistency, debugging | M-L |
| **External provider** | Commodity feature, time pressure | Fast to ship, maintained | Vendor lock-in, cost | S-M |
| **Gateway/facade** | Multiple backends, aggregation | Single interface, flexibility | Added hop, complexity | M |
| **CQRS** | Read/write asymmetry, scale | Performance, separate models | Complexity, sync issues | L |
| **Serverless** | Sporadic load, simple functions | Cost efficient, auto-scale | Cold starts, vendor lock | M |
| **Edge functions** | Low latency, geographically distributed | Fast, close to user | Limited runtime, debugging | S-M |

### Data Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| **Add columns** | Simple extension | Non-breaking, fast | Schema coupling |
| **New table** | Separate concern | Clean model | Joins, migration |
| **Soft references** | Loose coupling | Flexible | Integrity issues |
| **Event sourcing** | Audit, temporal queries | Full history | Storage, complexity |
| **Materialized views** | Read performance | Fast queries | Sync lag, storage |

### Auth/Permissions Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| **RBAC** | Simple hierarchies | Familiar, easy to reason | Inflexible |
| **ABAC** | Complex policies | Very flexible | Complex to debug |
| **ReBAC** | Relationship-based | Natural for social/org | Graph complexity |
| **ACL** | Fine-grained resources | Precise control | Management overhead |
| **External engine** | Policy as code (OPA/Cedar) | Powerful, auditable | Operational overhead |

### Integration Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| **REST API** | Standard CRUD | Familiar, tooling | Over/under fetching |
| **GraphQL** | Flexible queries, mobile | Efficient fetching | Complexity, caching |
| **gRPC** | Internal services, performance | Fast, typed | Browser support |
| **Webhooks** | External notifications | Simple, push-based | Reliability, retry |
| **Message queue** | Async processing | Decoupled, reliable | Infrastructure |
| **Direct DB** | Simple, internal | Fast, no overhead | Coupling |

---

## Fullstack Approaches

### Rendering Patterns

| Pattern | When to Use | Pros | Cons | Scope |
|---------|-------------|------|------|-------|
| **SSR (traditional)** | SEO, simple apps | Simple mental model, fast initial | Page reloads, server load | M |
| **SPA + API** | Rich interactions, app-like | Smooth UX, offline capable | Initial load, SEO | M |
| **SSR + hydration** | SEO + interactivity | Best of both | Complexity, hydration issues | M-L |
| **Islands** | Mostly static + interactive parts | Minimal JS, fast | Build complexity | M |
| **Streaming SSR** | Large pages, fast TTFB | Progressive render | Server complexity | M |
| **Edge SSR** | Low latency, personalization | Fast globally | Limited runtime | M |
| **Static + client** | Content sites, blogs | Fast, cheap hosting | Limited dynamism | S |

### Data Fetching Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| **Server Components** | React 19+, data-heavy | No client fetch, secure | Learning curve |
| **Loader pattern** | Route-based data | Colocated, parallel | Framework-specific |
| **Client fetch** | Dynamic, user-specific | Simple, flexible | Waterfalls, loading states |
| **Hybrid** | Mixed static/dynamic | Optimal per-route | Complexity |

---

## Tooling Approaches

### Interface Patterns

| Pattern | When to Use | Pros | Cons | Scope |
|---------|-------------|------|------|-------|
| **CLI flags** | Unix composable, scripts | Familiar, pipeable | Learning curve | S-M |
| **Interactive CLI** | First-time setup, wizards | Discoverable, guided | Not scriptable | S-M |
| **Config file** | Reproducible, complex options | Version controlled, declarative | Verbose | M |
| **GUI wrapper** | Visual tasks, non-technical users | Accessible | Extra dependency | M-L |
| **TUI** | Terminal power users | Rich without GUI | Limited adoption | M |
| **VS Code extension** | IDE users, contextual | Integrated, discoverable | Platform-specific | M |
| **Web dashboard** | Team visibility, remote | Accessible, shareable | Hosting required | M-L |

### Execution Patterns

| Pattern | When to Use | Pros | Cons |
|---------|-------------|------|------|
| **Local binary** | Performance, offline | Fast, no deps | Distribution |
| **Node/Python script** | Quick iteration | Easy to modify | Runtime required |
| **Docker container** | Isolation, reproducible | Consistent env | Overhead |
| **Cloud function** | Triggered, serverless | No infra | Cold starts |
| **GitHub Action** | CI/CD integration | Automated | GitHub-specific |

---

## Quick Selection Guide

### By User Type

| User Type | Prefer | Avoid |
|-----------|--------|-------|
| Power users | CLI, keyboard shortcuts, config files | Wizards, heavy GUIs |
| Casual users | GUIs, wizards, progressive disclosure | CLI flags, config files |
| Developers | APIs, code-first, documentation | Black boxes |
| Operators | Dashboards, alerts, automation | Manual processes |

### By Constraint

| Constraint | Prefer | Avoid |
|------------|--------|-------|
| Time pressure | Extend existing, external providers | New services, rewrites |
| Scale concerns | Event-driven, CQRS, caching | Monolithic, sync |
| Team size (small) | Monolith, simple patterns | Microservices |
| Team size (large) | Clear boundaries, services | Shared monolith |
| Mobile-first | Drawer, bottom sheet, minimal | Full modals, sidebars |

### By Risk Tolerance

| Risk Level | Approach Style |
|------------|----------------|
| Low risk | Extend existing, familiar patterns, proven tech |
| Medium risk | New service with existing tech, moderate refactors |
| High risk | New architecture, unfamiliar tech, major rewrites |

---

## Anti-patterns to Avoid

**Don't generate approaches that differ only in:**
- Color/styling (CSS change, not architectural)
- Library choice (React Query vs SWR — same pattern)
- Database vendor (PostgreSQL vs MySQL — same pattern)
- Cloud provider (AWS vs GCP — same pattern)

**Do generate approaches that differ in:**
- User interaction pattern
- Data flow architecture
- Where logic/state lives
- Sync vs async model
- Level of coupling
- Build vs buy decision
