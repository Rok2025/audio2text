# Models

This directory is intentionally not committed to GitHub.

The local service expects the following model layout:

```text
models/
  paraformer-zh/
    model.pt
    config.yaml
    configuration.json
    tokens.json
    seg_dict
    am.mvn
  fsmn-vad/
    model.pt
    config.yaml
    configuration.json
    am.mvn
```

The current Paraformer model file is about 944 MB, which is too large for a regular GitHub repository. Keep model files in one of these places instead:

- private deployment artifact, for example `audio2text-models.tar.gz`
- object storage or file server
- GitHub Release asset
- Git LFS, only if the team accepts LFS quota and bandwidth management

Before running Docker on a fresh clone, copy the model directories into `./models`, mount them into the container, or run:

```bash
bash scripts/download_models.sh
```
