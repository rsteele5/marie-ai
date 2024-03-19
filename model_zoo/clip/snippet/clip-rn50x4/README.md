---
tags:
  - vision
---

# Model Card: marie/clip-snippet-rn50x4

Disclaimer: The model card is taken and modified from the official CLIP repository, it can be
found [here](https://github.com/openai/CLIP/blob/main/model-card.md).

## Model Details

Fine tuned OpenAI CLIP model for snippet similarity embedding.

### Model Date

March 2024

# Uses

This model is used for finding similarity between image and text snippets. It can be used for various applications like
template matching, recommendation systems, etc.

## Data

The model was trained on private dataset of image and text snippets.

# Checkpoints

```shell
clip_1_0.00013816356658935547_params_clip.pth
```


Accuracy: 42/43 = 97.67%
Average Similarity for same: 22.17, 0.96
Average Similarity for diff: 5.56, 0.28