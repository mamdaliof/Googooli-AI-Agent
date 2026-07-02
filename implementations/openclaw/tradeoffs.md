# Tradeoffs Matrix: OpenClaw Agent

## 1. Architectural Code Structure

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **Monolithic Connectors** | Simple, single-file scripts for rapid prototyping and local testing. | Harder to scale, poor separation of concerns, difficult to extend. | Rejected. |
| **Modular Connectors** | Clean division (NIM client, Googooli client, channels). Easily extensible to new messaging platforms. | Marginally more file structure overhead initially. | **Selected**. Enables clean unit testing per module. |

## 2. LLM Model Interface

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **Raw requests HTTP calls** | Zero dependency wrapper, highly lightweight. | Need to write raw payload builders and stream processors manually. | Rejected. |
| **Standard OpenAI Client** | Reuses industry standard library; Nvidia NIM supports OpenAI-compatible endpoints. | Requires `openai` pip package dependency. | **Selected**. Simplifies reasoning/chat code significantly. |

## 3. Network and Timeout Configurations
* **NIM Client Timeout**: Set to `15.0` seconds to account for token-by-token generation and network latency on server deployments.
* **Googooli Endpoint Fallback**: On request failure or connection timeout (`3.0` seconds), continue processing using static/local core persona.
