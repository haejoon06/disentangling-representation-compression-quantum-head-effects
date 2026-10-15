from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from article09.features import load_embeddings
from article09.metrics import classification_metrics, expected_calibration_error, multiclass_brier
from article09.models import MatchedMLP, VQCNet, trainable_parameters
from article09.reducers import AngleScaler
from article09.utils import stable_subset_indices


@pytest.mark.parametrize("classes", [9, 10])
def test_parameter_matched_mlp_and_vqc(classes: int):
    expected = 36 + 7 * classes
    mlp = MatchedMLP(classes)
    vqc = VQCNet(classes, backend="default.qubit")
    assert trainable_parameters(mlp) == expected
    assert trainable_parameters(vqc) == expected


def test_vqc_batched_forward_and_backward():
    model = VQCNet(10, backend="default.qubit")
    x = torch.zeros(4, 6)
    y = torch.tensor([0, 1, 2, 3])
    logits = model(x)
    assert logits.shape == (4, 10)
    loss = torch.nn.functional.cross_entropy(logits, y)
    loss.backward()
    assert model.theta.grad is not None
    assert torch.isfinite(model.theta.grad).all()


def test_angle_scaler_bounds_and_shape():
    x = np.arange(60, dtype=np.float32).reshape(10, 6)
    scaler = AngleScaler.fit(x)
    output = scaler.transform(x)
    assert output.shape == x.shape
    assert np.max(output) <= math.pi
    assert np.min(output) >= -math.pi


def test_balanced_subset_is_reproducible():
    y = np.repeat(np.arange(3), 20)
    a = stable_subset_indices(y, 5, 11)
    b = stable_subset_indices(y, 5, 11)
    assert np.array_equal(a, b)
    assert np.array_equal(np.bincount(y[a]), np.array([5, 5, 5]))


def test_metrics_perfect_predictions():
    y = np.array([0, 1, 2, 0, 1, 2])
    probabilities = np.eye(3)[y] * 0.98 + 0.02 / 3
    metrics = classification_metrics(y, probabilities)
    assert metrics["macro_f1"] == pytest.approx(1.0)
    assert metrics["accuracy"] == pytest.approx(1.0)
    assert metrics["mcc"] == pytest.approx(1.0)
    assert 0 <= metrics["ece"] <= 1
    assert metrics["brier"] >= 0


def test_test_embedding_access_is_guarded():
    with pytest.raises(PermissionError):
        load_embeddings("cifar10", "test", allow_test=False)

