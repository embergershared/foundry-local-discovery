# Demo Foundry local

## Foundry Local CLI

Requires these models:

```pwsh
foundry model download qwen3.5-4b
foundry model download nemotron-speech-streaming-en-0.6b
foundry model download phi-4-mini
```

- Start on the WSL Ubuntu
```bash
watch -n 0.5 nvidia-smi
```

- In Windows terminal
```pwsh
foundry server start

foundry run qwen3.5-4b

    Few prompts:
    What can you do and what is your name?

    /voice on
    How do you say Good morning in French?

    /voice off
    Explain the core principles of quantum entanglement in simple terms. Then, compare and contrast the concepts of superposition and measurement in quantum mechanics.

    /exit

foundry cache list
foundry model unload qwen3.5-4b
foundry cache list

foundry model list               # --device gpu  (NPU/GPU/CPU)

foundry server status

foundry cache location

foundry server stop
```

## Foundry local WebAPI

- In Windows terminal, split tab

```pwsh
# Foundry local tab
foundry server start
foundry model load qwen3.5-4b

# ● success: Server ready (http://127.0.0.1:58783)
# PS D:\Git> foundry model load qwen3.5-4b
# ■ Loading model (qwen3.5-4b-generic-gpu:4, 4.1 GB)
# ● success: Loaded 'qwen3.5-4b' (GPU variant 'qwen3.5-4b-generic-gpu:4') into memory.

# Update the port and the model full name

# Chat agent tab
Set-Location '<path-to-clone>'

.\.venv\Scripts\python -m local_chat `
  --base-url 'http://127.0.0.1:58783/v1' `
  --model 'qwen3.5-4b-generic-gpu:4' `
  --prompt 'Explain local inference in three bullets.'

foundry server stop
```

## Foundry Local on as Azure Arc extension

- Follow all the deployments steps, prereqs, etc.

- Create a YAML file defining the model as a deployment

```yaml
apiVersion: foundrylocal.azure.com/v1
kind: ModelDeployment
metadata:
  name: <deployment-name>
  namespace: foundry-local-operator
spec:
  model:
    catalog:
      name: <model-name-from-catalog>
      version: "latest"
  compute: gpu              # or cpu
  runtime: vllm             # or onnx-genai
  workloadType: generative
  replicas: 1
  resources:
    requests:
      cpu: "2"
      memory: "32Gi"
    limits:
      cpu: "4"
      memory: "64Gi"
      gpu: 1
```

- Deploy it

```kubectl apply -f model-deployment.yaml```

- Get the endpoint and use it in the Agents/Apps calling the model
