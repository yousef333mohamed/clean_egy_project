# Route optimization architecture

Step 12 converts governed ML predictions and operational records into an advisory daily collection plan. It never executes the plan.

## Data flow

1. An authenticated user with `optimization:request` selects a date, bins, trucks, and depot.
2. The backend resolves bin coordinates and current non-null waste weight, calls the real Data Science provider for overflow and collection-priority scores, derives workforce availability from the latest attendance date, and derives truck availability from the latest trip status.
3. Stale or incomplete predictive evidence is rejected. Missing measurements are not converted to zero. Trucks without an availability record are treated as unavailable and reported.
4. The backend sends a strict, bounded request over the private network to `optimization-service` using a file-mounted service identity token.
5. Google OR-Tools solves a capacitated vehicle-routing problem with time windows, a workforce-derived route limit, service times, traffic/environment duration multipliers, priority-sensitive preferred arrival times, and optional dropped stops.
6. The optimizer returns route sequences, truck assignments, worker requirements, distance, duration, load, fuel estimates, unassigned bins, assumptions, warnings, and resource-loss alternatives.
7. The backend persists the immutable request/result evidence and exposes a grounded GenAI explanation. If the LLM is unavailable or introduces an unsupported number, a deterministic explanation is returned.
8. An authorized manager can record one approval or rejection. This only changes review metadata; no dispatch, assignment, schedule, or external system is mutated.

## Constraints and objective

- Each assigned bin is visited at most once.
- A route's estimated load cannot exceed the assigned truck capacity.
- The number of routes cannot exceed `available_workers // workers_per_route`.
- Stops and routes must fit the configured working day and stop time windows.
- Distance uses the Haversine formula and therefore is an explicit approximation, not a road-network navigation guarantee.
- Travel duration applies operator-supplied average speed, traffic, and environmental multipliers.
- High priority/overflow bins receive earlier soft arrival targets and higher penalties if dropped.
- Fuel is estimated from route distance and the supplied truck efficiency.
- Alternatives re-solve with a used truck unavailable. Infeasible plans can include hypothetical additional-worker or restored-truck scenarios.

## Trust and safety boundaries

- The optimizer has no public port, database credentials, dispatch integration, or write path to operational systems.
- Backend RBAC separates plan requests from manager approvals.
- Service tokens come from secret files in production and are never accepted in request payloads.
- Batch size and solve time are bounded.
- Request IDs and bounded request telemetry support diagnosis without logging plan payloads.
- Prometheus counters and histograms track provider requests, failures, latency, solve status, and unassigned-bin totals without asset identifiers.
- `requires_human_approval` is always `true`; `executes_operations` is always `false` at every API boundary.

## Known limitations

- One shared depot is supported per solve.
- Distances are straight-line estimates; a governed road-distance matrix is required before relying on travel estimates operationally.
- Traffic and environmental conditions are scenario multipliers, not live feeds.
- Workforce availability is based on the latest attendance snapshot on or before the plan date, not future roster commitments.
- Latest truck trip status is a conservative availability proxy, not a maintenance-system reservation.
- The solver recommends worker counts, not named employees.
- A feasible solution is not proof of a globally optimal solution within the bounded solve time.
