# Article 09 Locked Experimental Protocol

## Research objective

The study separates performance loss caused by compressing a frozen 384-dimensional visual representation into six dimensions from the difference caused by the downstream classical or quantum decision head.

The principal comparison is a controlled factorial design:

```text
Frozen DINOv2 ViT-S/14 (384D)
  -> PCA-6 | LDA-6 | NCA-6 | supervised projection-6
  -> identical scaled 6D vectors
  -> LR | RBF-SVM | parameter-matched MLP | VQC
```

## Datasets and splits

- CIFAR-10: 45,000 train, 5,000 validation from the official train set; official test locked.
- EuroSAT RGB: group-aware stratified 70/15/15 split with seed 2026.
- PathMNIST: official train, validation, and test splits.

Before split freezing, the pipeline performs decode validation, SHA-256 exact-duplicate audit, pHash candidate retrieval at Hamming distance <= 4, SSIM confirmation at >= 0.98, group construction, and crossing-group quarantine.

## Matched budget

- Training: 150 samples per class for every seed.
- Validation: one fixed balanced set of 100 samples per class using seed 2026.
- Test: all non-quarantined examples in the locked test split.
- Final seeds: 11, 22, 33, 44, 55, 66, 77, 88, 99, 111.
- Pilot seed: 2026.

## Representation and reducers

Images are converted to RGB, resized to 224 x 224 using bicubic interpolation, normalized with ImageNet statistics, and encoded once using frozen DINOv2 ViT-S/14. The 384D CLS token is cached as float32.

Reducers are fitted using training data only:

- PCA-6 without whitening.
- LDA-6 with SVD solver.
- NCA-6 initialized by PCA.
- Learned supervised projection 384 -> 6 -> class logits; the classifier layer is discarded.

Each reduced representation is scaled using training statistics and mapped to angle range using `pi * tanh(z)`. All four heads receive exactly the same vectors.

## Heads

- Multinomial Logistic Regression.
- RBF-SVM with calibrated probabilities.
- MLP: Linear(6, 6, bias=False), Tanh, Linear(6, C, bias=True).
- VQC: six qubits, two data-reuploading layers, RY input encoding, trainable Rot gates, ring CNOT entanglement, six Pauli-Z expectations, and Linear(6, C).

The MLP and VQC have exactly `36 + 7C` trainable parameters: 106 for CIFAR-10 and EuroSAT, and 99 for PathMNIST.

## Selection and isolation

Hyperparameters are selected only on validation data using pilot seed 2026. Primary criterion is validation macro-F1; validation NLL is the tie-breaker. Selected settings, split hashes, embedding hashes, metric definitions, architecture, and final seeds are written to `frozen/protocol_v1.json`. The test stage refuses to run without a matching freeze hash.

## Endpoints and statistics

Primary endpoint: macro-F1. Secondary endpoints: balanced accuracy, accuracy, MCC, macro precision/recall, OVR macro ROC-AUC, NLL, ECE, multiclass Brier score, training time, and inference time.

The analysis reports compression penalty, VQC-versus-matched-MLP gap, VQC-versus-RBF gap, paired bootstrap confidence intervals, Friedman tests across reducers, planned Wilcoxon signed-rank comparisons with Holm correction, per-dataset average ranks, and direction consistency. Datasets are not pooled as pseudo-independent samples.

## Completion criteria

The experiment is complete only when all three datasets, four reducers, four heads, and ten seeds have either valid outputs or explicit failure records; all 120 VQC conditions and 60 full-space references are accounted for; test isolation is verified; per-sample predictions and runtime records exist; and the notebook reconstructs every manuscript table and figure from raw outputs.

