from __future__ import annotations
from typing import Optional, Dict
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix
import seaborn as sns

def plot_classification_curves(y_true: np.ndarray, y_pred: np.ndarray, 
                               y_prob: Optional[np.ndarray]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    
    # ROC
    if y_prob is not None and y_prob.ndim == 1:
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        plt.figure()
        plt.plot(fpr, tpr, label="ROC")
        plt.plot([0, 1], [0, 1], "--", color="gray")
        plt.xlabel("FPR"); 
        plt.ylabel("TPR"); 
        plt.title("ROC curve")
        out["roc"] = 1
        
    # PR
    if y_prob is not None and y_prob.ndim == 1:
        prec, rec, _ = precision_recall_curve(y_true, y_prob)
        plt.figure()
        plt.plot(rec, prec, label="PR")
        plt.xlabel("Recall"); 
        plt.ylabel("Precision"); 
        plt.title("PR curve")
        out["pr"] = 1
        
    # Confusion
    plt.figure()
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title("Confusion matrix")
    out["confusion"] = 1
    return out

def plot_regression_residuals(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, int]:
    out: Dict[str, int] = {}
    residuals = y_true - y_pred
    plt.figure()
    sns.histplot(residuals, kde=True)
    plt.title("Residuals distribution")
    out["residuals"] = 1
    return out