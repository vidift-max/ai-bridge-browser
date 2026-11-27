# Local model selection — free, Wi-Fi-only, no automatic download

## Decision

Do not download or initialize a model in this change. The first candidate for a controlled device test is **onnx-community/Qwen2.5-0.5B-Instruct**, using Transformers.js and a quantized ONNX variant, because the model is explicitly marked for Transformers.js and lists Portuguese among its supported languages.

Official references reviewed on 2026-11-23:
- Transformers.js runs in-browser with ONNX Runtime; CPU/WASM is the default, WebGPU is optional, and quantization is recommended for constrained devices: https://huggingface.co/docs/transformers.js/index
- The ONNX Community Qwen model card lists Transformers.js usage and multilingual metadata including Portuguese: https://huggingface.co/onnx-community/Qwen2.5-0.5B-Instruct
- The Q4 ONNX weight file is approximately 786 MB: https://huggingface.co/onnx-community/Qwen2.5-0.5B-Instruct/blob/main/onnx/model_q4.onnx
- WebLLM requires WebGPU; its browser and hardware requirements make it a less suitable first choice for an unknown Android tablet: https://webllm.io/docs/faq/

## Why not start with LFM2.5-350M

LFM2.5-350M is attractive because its model card lists Portuguese and an ONNX/Transformers.js route. However, the ONNX repository currently declares the `lfm1.0` license, not a standard Apache-2.0 identifier. Commercial-use and redistribution terms must be reviewed before adoption. It is therefore not the default project candidate yet.

## Hard gates before any model download

1. User must explicitly approve a specific model download.
2. Browser must report Wi-Fi explicitly through the strict Wi-Fi gate; unknown network type blocks.
3. HTTPS secure context is required.
4. Show exact model, estimated download size, storage requirement, and the fact that first download consumes Wi-Fi bandwidth.
5. Check available storage and device capability; do not infer compatibility from browser brand alone.
6. Abort on network change/offline and do not fall back to cellular or remote inference.
7. No automatic model download on page load.
8. No prompt, token, OAuth cookie, or Blogger content is sent to model hosts or remote inference APIs.
9. Model must run locally after download; if not, stop and report the limitation.
10. Keep the model identity distinct from GPT-6. A small local model is not GPT-6 and must not be presented as equivalent.

## Current status

- Candidate researched: Qwen2.5-0.5B-Instruct ONNX, Q4.
- Approximate Q4 weight file: 786 MB (not necessarily total download; tokenizer/config and runtime assets add more).
- Download: NOT STARTED.
- Model runtime dependency: NOT INSTALLED.
- Inference: NOT IMPLEMENTED.
- Android tablet compatibility: UNKNOWN until the in-browser diagnostic and controlled test run.
- Wi-Fi-only enforcement: implemented as a fail-closed browser policy, but must be validated on the target browser.
- This document is an evaluation record, not authorization to download.
