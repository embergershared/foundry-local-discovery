# Foundry Local on Azure Local — Pitch, Setup & Demo

Oct 25, 2026 · @Emm

## At a glance

In an Azure Local project, Foundry Local is the AI inference layer: it runs Foundry-catalog models on the customer's own AKS Arc cluster, managed through Azure Arc, behind an OpenAI-compatible endpoint — connected or fully disconnected ([deployment overview](https://learn.microsoft.com/en-us/azure/azure-sovereign-clouds/private/foundry-local/deploy-overview)). Your RTX 5070 Ti PC plays the developer workstation: same model catalog and same API the app team builds against before promoting to the cluster.

Watch the status line: Foundry Local on devices is GA since April 2026, but deploying on Azure Local still requires preview access per Microsoft Learn ([model endpoint docs](https://learn.microsoft.com/en-us/azure/azure-arc/agents-tools-foundry-local/prepare-model-endpoint)). Confirm the customer's preview status before you promise timelines.

Prep before Wednesday morning:

- [ ] Monday: confirm the customer's facts — Azure Local version, GPU nodes in the cluster, connected or disconnected, preview access
- [ ] Monday: ask your Azure Local or Foundry specialists for a lab cluster you can show live, or a recording
- [ ] Monday: set up the workstation and pre-download models (Workstation setup steps 1–6)
- [ ] Tuesday: full dry run with a timer, including the Wi-Fi-off moment
- [ ] Tuesday: pick a prompt from the customer's domain (their kind of document, their language)
- [ ] Wednesday: reboot, start the service, warm-load the first model 15 minutes before the call

## Value pitch

The one-liner: **bring Foundry models to the data, not the data to the cloud — AI inference on the Azure Local you already run, governed through Azure Arc, with the same OpenAI API your developers use everywhere.**

### The problems it solves

| Customer pain | What Foundry Local on Azure Local changes |
| --- | --- |
| Regulation or policy forbids sending data to cloud AI | Models run on customer-controlled hardware in their own datacenter |
| Air-gapped, classified or isolated sites | Disconnected deployment via expansion packs; authentication uses the local Active Directory instead of public Entra ID ([disconnected overview](https://learn.microsoft.com/azure/azure-sovereign-clouds/private/foundry-local/disconnected-operations/concept-overview)) |
| Azure Local is in place, but has no AI story | Adds as an Azure Arc extension (type `Microsoft.Foundry`) on an AKS Arc cluster ([extension docs](https://learn.microsoft.com/en-us/azure/azure-sovereign-clouds/private/foundry-local/deploy-foundry-local-arc-extension)) |
| Ops teams want Kubernetes-native operations | An operator handles model caching, deployment and serving, across multiple nodes ([multi-node docs](https://learn.microsoft.com/en-gb/azure/azure-sovereign-clouds/private/foundry-local/concept-multi-node-deployment)) |
| Fear of a separate AI governance silo | Managed from the Azure portal through Arc, with Azure RBAC and Entra ID authentication on by default |
| Apps would need rewriting for on-prem AI | OpenAI-compatible `/v1/chat/completions` endpoint: change the base URL, keep the code |

### Three value pillars

1. **Sovereignty and control.** Data, models and operations stay on premises, including fully disconnected.
2. **One Azure operating model.** The same Arc control plane, RBAC and portal the customer already uses for Azure Local.
3. **Developer continuity.** Build on a workstation with Foundry Local, deploy to the cluster, burst to Foundry cloud — one API throughout.

### Positioning

Foundry Local is the AI layer of Microsoft's Sovereign Private Cloud, alongside Azure Local for infrastructure and Microsoft 365 Local for productivity ([Tech Community](https://techcommunity.microsoft.com/tag/mais%202026)).

- **Microsoft Foundry (cloud):** frontier models, hosted agents, fine-tuning, evaluation.
- **Foundry Local on Azure Local:** shared, multi-user inference on the customer's cluster, connected or disconnected.
- **Foundry Local on devices:** one user, one PC — the developer workstation in this demo.

### Objection handling

| Objection | Response |
| --- | --- |
| "Is this production-ready?" | The device runtime is GA; the Azure Local deployment needs preview access per current docs. Confirm the latest status with the product team before committing dates. |
| "What GPUs do we need?" | Size per model. Microsoft Learn suggests 40 GB+ VRAM, or multi-GPU, for gpt-oss-20b on the cluster ([model endpoint docs](https://learn.microsoft.com/en-us/azure/azure-arc/agents-tools-foundry-local/prepare-model-endpoint)). Small models run on far less. |
| "We're fully air-gapped." | Disconnected mode uses the same operator and cluster model, with artifacts imported via expansion packs. |
| "Can't we just run vLLM ourselves?" | You can, but you own patching, model packaging, auth and lifecycle. Here it is a Microsoft-supported Arc extension with a curated catalog and the same API as cloud. |
| "Can developers start before the cluster is ready?" | Yes — that is the workstation part of this demo. Same API; only the endpoint changes later. |
| "Are large models supported?" | Microsoft announced large models on Foundry Local for qualified customers in February 2026 ([Microsoft News](https://news.microsoft.com/source/emea/2026/02/new-enhancements-to-microsofts-sovereign-cloud-offerings-even-when-completely-disconnected)). |

## Workstation setup (RTX 5070 Ti PC)

The PC is the developer inner loop of the Azure Local story: the team prototypes here, then deploys the same models to the cluster. Budget about an hour on Monday, mostly model downloads. Run everything in PowerShell.

**Prerequisites:** Windows 11 24H2 or later recommended, a current NVIDIA Game Ready or Studio driver, Python 3.11+, and admin rights to install software ([Microsoft Learn](https://learn.microsoft.com/windows/ai/foundry-local/get-started/)).

1. **Install the CLI**, then close and reopen the terminal so `foundry` is on your PATH:

   ```powershell
   winget install Microsoft.FoundryLocal
   foundry --version
   ```
2. **Start and check the service.** Note the local endpoint and port it prints:

   ```powershell
   foundry service status
   ```

   If you see a service connection error, run `foundry service restart`.
3. **List models.** The first run downloads execution providers for your hardware, including CUDA for the 5070 Ti:

   ```powershell
   foundry model list
   foundry model list --filter device=GPU
   ```
4. **Confirm the GPU is used.** Run by alias and Foundry Local picks the CUDA variant; check with `foundry service ps` and watch GPU load in Task Manager:

   ```powershell
   foundry model run phi-4-mini
   foundry service ps
   ```
5. **Pre-download the demo models** so nothing downloads live on the call. Confirm the exact aliases in `foundry model list` first; the catalog changes.

   ```powershell
   foundry model download phi-4-mini
   foundry model download qwen2.5-7b
   foundry model download gpt-oss-20b
   foundry cache list
   ```
6. **Build the two-minute app.** This shows a customer that existing OpenAI code just works:

   ```powershell
   pip install openai
   ```

   Save as `local_chat.py`, setting the port from step 2 and the model ID from `foundry service ps`:

   ```python
   from openai import OpenAI
   
   client = OpenAI(base_url="http://localhost:<PORT>/v1", api_key="not-needed")
   
   stream = client.chat.completions.create(
       model="<MODEL-ID>",
       messages=[{"role": "user", "content": "Summarize this contract clause in 3 bullets: ..."}],
       stream=True,
   )
   for chunk in stream:
       if chunk.choices and chunk.choices[0].delta.content:
           print(chunk.choices[0].delta.content, end="", flush=True)
   ```

   For an app that ships Foundry Local inside it, use `pip install foundry-local-sdk-winml` on Windows; don't install it alongside `foundry-local-sdk`, as they conflict ([Microsoft Learn](https://learn.microsoft.com/windows/ai/foundry-local/get-started/)).

### Which models fit 16 GB VRAM

| Model | Role in the demo | Fit on 16 GB |
| --- | --- | --- |
| phi-4-mini | Opener: instant, fast streaming | Easy fit |
| qwen2.5-7b | Better-quality summaries and extraction | Comfortable fit |
| gpt-oss-20b | The "wow": OpenAI open-weight reasoning model on a PC | Tight — test on Monday. On the cluster, docs suggest 40 GB+ VRAM. It is a 21B-total, 3.6B-active mixture-of-experts model ([Foundry catalog](https://ai.azure.com/catalog/models/FW-GPT-OSS-20B)) |

Unload one model before loading the next to keep VRAM free: `foundry model unload <model>`. If gpt-oss-20b fails to load or runs slowly, drop it from the demo and use qwen2.5-7b as the quality model.

## Production path on Azure Local

On the cluster, Foundry Local installs as an Azure Arc extension, and an operator turns each ModelDeployment resource into model pods behind one OpenAI-compatible endpoint ([model endpoint docs](https://learn.microsoft.com/en-us/azure/azure-arc/agents-tools-foundry-local/prepare-model-endpoint)).

&#91;embedded content: Foundry Local on Azure Local · architecture\]

The only change between the workstation prototype and production is the endpoint the app points at.

What a deployment takes — use this to walk the customer through the YAML if you can't show a live cluster:

1. **Prerequisites:** an Azure Local instance; an AKS Arc cluster on Kubernetes 1.29+ registered with Arc; kubectl, Helm and Azure CLI with `k8s-extension`; a supported region; preview access ([requirements](https://learn.microsoft.com/azure/azure-sovereign-clouds/private/foundry-local/concept-requirements)).
2. **Platform dependencies:** cert-manager, trust-manager and a Gateway API provider — Foundry Local routes model traffic through the Gateway API, not an Ingress controller ([extension docs](https://learn.microsoft.com/en-us/azure/azure-sovereign-clouds/private/foundry-local/deploy-foundry-local-arc-extension)).
3. **Install the extension** (portal or CLI; Entra ID auth is on by default):

   ```powershell
   az k8s-extension create `
     --resource-group <rg> --cluster-name <arc_cluster> `
     --cluster-type connectedClusters `
     --name "inference-operator" --extension-type Microsoft.Foundry `
     --scope cluster --release-namespace "foundry-local-operator"
   ```
4. **Deploy a model** with a ModelDeployment resource, then `kubectl apply -f`:

   ```yaml
   apiVersion: foundrylocal.azure.com/v1
   kind: ModelDeployment
   metadata:
     name: gpt-oss-20b
     namespace: foundry-local-operator
   spec:
     workloadType: generative
     compute: gpu
     runtime: vllm
     model:
       catalog:
         name: gpt-oss-20b
         version: "latest"
     replicas: 1
   ```
5. **Verify:** `kubectl get modeldeployment gpt-oss-20b -n foundry-local-operator` until it shows Running; docs note GPU deployments can take 10–30 minutes.
6. **Test:** `kubectl port-forward svc/gpt-oss-20b -n foundry-local-operator 5000:5000`, then call `/v1/chat/completions` on port 5000.

For a disconnected site, import the Foundry Local expansion pack before installing the extension ([disconnected overview](https://learn.microsoft.com/azure/azure-sovereign-clouds/private/foundry-local/disconnected-operations/concept-overview)).

## Demo flow (25 minutes)

The arc: **sovereign by design → developers start today on a workstation → production runs on your Azure Local, governed by Arc.** Each act ends on one line the customer should repeat to their boss.

| Time | Show | Say |
| --- | --- | --- |
| 0–3 min | Frame their requirement: data and AI must stay in their datacenter, possibly disconnected | "Which AI use cases are blocked today because the data can't leave?" |
| 3–7 min | The architecture diagram above: Arc on top, cluster in the middle, one endpoint | "AI becomes one more Arc extension on the Azure Local you already run." |
| 7–10 min | Workstation: `foundry model list --filter device=GPU`, then `foundry model run phi-4-mini` with their kind of prompt | "Your developers can start today, before the cluster has GPUs." |
| 10–12 min | **Offline moment:** turn Wi-Fi off, ask a second prompt | "No network. This is what disconnected looks like." |
| 12–15 min | Run `local_chat.py`, then point out the one changed line: `base_url` | "Standard OpenAI SDK code. Moving to the cluster changes one URL." |
| 15–21 min | **The cluster:** live — Arc extension in the portal, `kubectl get modeldeployment`, a call to the endpoint. No cluster — walk the ModelDeployment YAML and the `az k8s-extension` command | "One YAML file per model. Your platform team runs it like any Kubernetes workload." |
| 21–25 min | Close on the continuum: workstation → Azure Local → Foundry cloud for frontier work | "Pick where each workload runs by its data rules, not by rewriting code." |

### Wow moments to land

- The Wi-Fi toggle, tied to their disconnected requirement. Pause and let it sink in.
- Task Manager GPU graph spiking while tokens stream.
- Side by side: the workstation `base_url` and the cluster endpoint.

### Fallback plan

- **No lab cluster:** show the YAML and CLI from the Production path section, and a recording if your specialists have one.
- **gpt-oss-20b won't load on the PC:** use qwen2.5-7b, and say the cluster sizing is where the big models live.
- **Service errors:** `foundry service restart`, then rerun the last command.
- **Model starts downloading on stage:** switch to a cached model from `foundry cache list`.

### Close and next steps

- [ ] Pick one sovereign use case and the data it touches
- [ ] Confirm preview access and GPU node plans for their Azure Local cluster
- [ ] Offer a hands-on session: developers on workstations, platform team on a pilot ModelDeployment
- [ ] Decide connected vs disconnected deployment, which sets the install path

## Sources

- [Deployment overview for Foundry Local on Azure Local — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-sovereign-clouds/private/foundry-local/deploy-overview)
- [Requirements for Foundry Local on Azure Local — Microsoft Learn](https://learn.microsoft.com/azure/azure-sovereign-clouds/private/foundry-local/concept-requirements)
- [Deploy Foundry Local as an Azure Arc extension — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-sovereign-clouds/private/foundry-local/deploy-foundry-local-arc-extension)
- [Create your language model endpoint (ModelDeployment) — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-arc/agents-tools-foundry-local/prepare-model-endpoint)
- [Foundry Local on Azure Local: prepare a language model — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-arc/agents-tools-foundry-local/prepare-language-model)
- [Multi-node deployment — Microsoft Learn](https://learn.microsoft.com/en-gb/azure/azure-sovereign-clouds/private/foundry-local/concept-multi-node-deployment)
- [Disconnected environments overview — Microsoft Learn](https://learn.microsoft.com/azure/azure-sovereign-clouds/private/foundry-local/disconnected-operations/concept-overview)
- [Sovereign Cloud enhancements, February 2026 — Microsoft News](https://news.microsoft.com/source/emea/2026/02/new-enhancements-to-microsofts-sovereign-cloud-offerings-even-when-completely-disconnected)
- [Build a Sovereign Private Cloud with Azure Local — Tech Community](https://techcommunity.microsoft.com/tag/mais%202026)
- [Foundry Local is now Generally Available — Microsoft Foundry Blog](https://devblogs.microsoft.com/foundry/foundry-local-ga/)
- [Get started with Foundry Local on Windows — Microsoft Learn](https://learn.microsoft.com/windows/ai/foundry-local/get-started/)
- [Foundry Local CLI reference — Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry-local/reference/reference-cli)
- [gpt-oss-20b — Foundry model catalog](https://ai.azure.com/catalog/models/FW-GPT-OSS-20B)
