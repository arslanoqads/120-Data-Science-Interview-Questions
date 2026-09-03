# 02 — Kubernetes fluency: Pods, Services, Deployments, HPA

> Week 18 — objects an FDE must read and debug (not full SRE / CNI depth). Research notes (raw).

---

## Fundamentals

Kubernetes fluency for this curriculum is **four objects** plus how they fail together. You do **not** need custom controllers, cluster federation, or CNI packet debugging.

### Pod

Smallest schedulable unit: one or more containers sharing network namespace (localhost) and volumes. **Ephemeral.** Never treat a Pod IP as durable. Multi-container Pods are for sidecars (OTEL, service mesh) that must die/live with the app — not for “API + Redis in one Pod” in production.

Official concept: [Pods](https://kubernetes.io/docs/concepts/workloads/pods/).

### Deployment

Desired replica count + Pod **template**. Owns **ReplicaSets**; implements **rolling updates** and **rollbacks** via revision history. Changing the template (image digest, env checksum) creates a new ReplicaSet; the Deployment controller ramps new Pods and drains old ones per `strategy.rollingUpdate` (`maxUnavailable`, `maxSurge`).

Official: [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/). Rollback: [rolling back](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment).

**GitOps note:** if you set `spec.replicas` in Git **and** attach an HPA, the two fight. Strong practice: let HPA own replicas; omit or ignore `replicas` in the GitOps app of record.

### Service

Stable virtual IP / DNS name in front of Pods selected by **labels**. Types:

| Type | Role |
|------|------|
| ClusterIP | Default; in-cluster LLM API / gateway |
| NodePort | Rare in cloud; debugging |
| LoadBalancer | Cloud LB → nodes → Pods |
| ExternalName | DNS alias |

HTTP APIs usually: **Service → Ingress or Gateway API**. Canary **percentage splits** need Ingress weights, Gateway API `HTTPRoute` weights, or a mesh — a ClusterIP Service alone is **equal-cost** across Ready endpoints ([Services](https://kubernetes.io/docs/concepts/services-networking/service/); [Gateway API](https://gateway-api.sigs.k8s.io/)).

**Endpoints vs Ready:** traffic goes to Pods that pass **readiness**. Mis-set probes empty the Endpoints list → 5xx at the LB.

### HorizontalPodAutoscaler (HPA)

Controller that adjusts a workload’s `replicas` (Deployment, StatefulSet, anything with a **scale subresource**) from metrics. **Not** for DaemonSets.

- API: **`autoscaling/v2`** (CPU, memory, custom, external, multiple metrics).  
- Control loop: kube-controller-manager `--horizontal-pod-autoscaler-sync-period` default **15s**.  
- Formula (docs):  
  `desiredReplicas = ceil(currentReplicas × currentMetricValue / desiredMetricValue)`  
  Skip if ratio is within tolerance (default **0.1**).  
- Multiple metrics: take the **max** proposed replica count (capped by `maxReplicas`).  
- CPU utilization is **percent of requests**. **If any container lacks a CPU request, CPU utilization is undefined and HPA will not act on that metric.**

Official: [HPA concept](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/), [walkthrough](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/), [API](https://kubernetes.io/docs/reference/kubernetes-api/autoscaling/horizontal-pod-autoscaler-v2/).

Metrics path: `metrics.k8s.io` (usually **Metrics Server**), `custom.metrics.k8s.io` (e.g. [prometheus-adapter](https://github.com/kubernetes-sigs/prometheus-adapter)), `external.metrics.k8s.io`.

**Behavior (`v2`):** `scaleUp` / `scaleDown` policies + `stabilizationWindowSeconds`. Defaults: scale-up aggressive (0s stabilization), scale-down **300s** lookback — pick the safest (highest) recommendation in the window for down. This is how you stop **flapping**.

`minReplicas` defaults to 1; 0 requires scale-to-zero feature gates and object/external metrics. Production LLM APIs almost never want `minReplicas: 0` without an explicit cold-start budget (Cloud Run analogy: min instances).

### Mental model for an LLM API

```
Ingress / Gateway API  →  Service  →  Deployment (API pods)
                                         ↑
                                        HPA (CPU *or* custom RPS / inflight / latency)
Workers: Deployment consuming SQS/PubSub
         HPA or KEDA on queue depth
```

**Replica count ≠ capacity:** provider rate limits, connection pools, and GPU inference queues saturate **before** CPU.

### Related objects you must recognize (not master)

- **PodDisruptionBudget (PDB):** voluntary evictions (node drain, cluster upgrade) leave `minAvailable` Pods.  
- **Topology spread:** schedule across AZs.  
- **`preStop` + `terminationGracePeriodSeconds`:** finish SSE/WebSocket generations.  
- **VPA:** resizes requests/limits; disruptive; do not dual-wield VPA+HPA on the **same** CPU metric casually.  
- **KEDA:** ScaledObject that **manages an HPA** for event sources (queue, cron); CNCF; scale-to-zero for workers.

KubeCon / SIG-Autoscaling: Cluster Autoscaler **node** scale-down criteria vs HPA **pod** scale — different loops ([SIG-Autoscaling Deep Dive](https://www.youtube.com/watch?v=odxPyW_rZNQ)). AWS-centric but pedagogically clear: HPA + node provisioner + KEDA as three layers ([Scale your EKS](https://www.youtube.com/watch?v=H2REI7uE_yc)).

---

## Alternatives & Tradeoffs

| Scaling lever | Pros | Cons |
|---------------|------|------|
| HPA on CPU | Built-in; Metrics Server | LLM pods often **I/O-bound** waiting on provider; CPU under-signals load |
| HPA on memory | Easy to set | Lagging; OOM loops get **multiplied**; caches look like “need more pods” |
| HPA on custom RPS / concurrency / inflight | Matches real demand | prometheus-adapter (or equivalent) ops |
| HPA on queue depth (workers) | Correct for async agents | Scale-up lag; need `maxReplicas` ≤ downstream quota |
| VPA | Right-sizes CPU/mem | Restarts; fights HPA if both on CPU |
| KEDA | Event-driven; scale to zero | Extra CRDs/operators |
| Cluster Autoscaler / Karpenter | Nodes appear when pods Pending | Minutes of scheduling delay; not a substitute for `minReplicas` headroom |
| Gateway API vs Ingress | First-class weights, HTTPRoute | Newer; implementation-dependent |

| Traffic object | Pros | Cons |
|----------------|------|------|
| ClusterIP only | Simple | No L7 canary |
| Ingress | Ubiquitous | Annotation soup; vendor-specific canary |
| Gateway API | Portable canary weights (Cloud Deploy path) | Must run a Gateway implementation |

---

## Necessity

Without **Services**, clients break whenever Pods reschedule.

Without **Deployments**, you hand-edit Pods and lose rolling updates/rollback.

Without **HPA** (or Cloud Run autoscaling), spikes → timeout storms and retry amplification; valleys → wasted spend.

Without CPU **requests**, “HPA on 70% CPU” is a no-op and you learn this during a launch.

Without **readiness**, a rolling update sends traffic to pods still establishing TLS to OpenAI/Anthropic.

Without PDB + topology spread, a node upgrade or AZ blip takes the **only** Ready replica of a `minReplicas: 1` chat API.

Without graceful shutdown, rolling updates **cut streams**; users see truncated answers and retry → more load.

---

## Industry Practice

**Common:** Deployment + ClusterIP + Ingress; HPA `averageUtilization: 70` CPU; `minReplicas: 1`; no PDB; `replicas` also set in Helm.

**Strong / senior:**

- Requests/limits from profiling; watch `container_cpu_cfs_throttled_seconds_total` if limits are tight  
- PDBs for voluntary evictions  
- Separate HPAs for **API vs workers**  
- Custom metrics: inflight requests, p95, queue depth; **`maxReplicas` capped by provider RPM**  
- `behavior.scaleDown.stabilizationWindowSeconds` 180–300s; scale-up may want a **short** window if pods start slowly (avoid overshoot while unready)  
- Topology spread across AZs; `preStop` + grace ≥ max generation time  
- `kubectl describe hpa` / events as the first debug (metrics-server missing, targets unknown)  
- Labels that Week 20 cost dashboards will use (`app`, `version`, `env`)

Adobe KubeCon (Argo Rollouts analysis duration 5–10 min for moderate traffic, scrape ~15s) is about **canary**, but the same “enough data points” logic applies to HPA: do not expect 15s CPU to save a 2-minute prompt ([`aWP6ZUdPXak`](https://www.youtube.com/watch?v=aWP6ZUdPXak)).

---

## Concrete Scenario (URL)

**HPA concept + algorithm + v2 behavior** — scale Deployment min/max; CPU vs custom; stabilization:  
https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/

**Walkthrough:**  
https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/

**v2 API reference** — default metric 80% CPU if unspecified; minReplicas 0 caveats:  
https://kubernetes.io/docs/reference/kubernetes-api/autoscaling/horizontal-pod-autoscaler-v2/

**Pods / Services / Deployments:**  
https://kubernetes.io/docs/concepts/workloads/pods/  
https://kubernetes.io/docs/concepts/services-networking/service/  
https://kubernetes.io/docs/concepts/workloads/controllers/deployment/

**prometheus-adapter** (custom metrics API):  
https://github.com/kubernetes-sigs/prometheus-adapter

**KubeCon SIG-Autoscaling** (CA scale-down + HPA/VPA Q&A):  
https://www.youtube.com/watch?v=odxPyW_rZNQ

**CNCF channel** (search HPA / autoscaling):  
https://www.youtube.com/@cncf

**Illustrative YAML (teaching, not a cluster apply):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-api
spec:
  selector:
    matchLabels: { app: llm-api }
  template:
    metadata:
      labels: { app: llm-api }
    spec:
      terminationGracePeriodSeconds: 120
      containers:
        - name: api
          image: registry.example.com/llm-api@sha256:abc…
          ports: [{ containerPort: 8080 }]
          resources:
            requests: { cpu: "500m", memory: "1Gi" }
            limits: { memory: "1Gi" }
          readinessProbe:
            httpGet: { path: /ready, port: 8080 }
            periodSeconds: 5
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            periodSeconds: 15
          lifecycle:
            preStop:
              exec: { command: ["sleep", "10"] }
---
apiVersion: v1
kind: Service
metadata: { name: llm-api }
spec:
  selector: { app: llm-api }
  ports: [{ port: 80, targetPort: 8080 }]
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: llm-api }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
```

Replace the CPU metric with custom inflight/RPS for provider-bound APIs.

---

## Open Questions

- For streaming LLM responses, should **readiness** consider connection budget / inflight cap rather than (or in addition to) CPU?  
- Scale-to-zero for agent workers: worth cold-start vs always-on `minReplicas: 1`?  
- When to prefer **Gateway API** over Ingress for canary weight splitting (file 03)?  
- HPA on **p95 latency**: does it create a death spiral (latency high → more pods → more provider 429 → worse latency)?  
- Should `maxReplicas` be a **platform policy** (OPA) tied to spend, not an app guess?

---

## Sources

- https://kubernetes.io/docs/concepts/workloads/pods/  
- https://kubernetes.io/docs/concepts/services-networking/service/  
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/  
- https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/  
- https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/  
- https://kubernetes.io/docs/reference/kubernetes-api/autoscaling/horizontal-pod-autoscaler-v2/  
- https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/  
- https://gateway-api.sigs.k8s.io/  
- https://github.com/kubernetes-sigs/prometheus-adapter  
- https://keda.sh/docs/latest/concepts/  
- https://www.youtube.com/watch?v=odxPyW_rZNQ  
- https://www.youtube.com/watch?v=H2REI7uE_yc  
- https://www.youtube.com/@cncf  
