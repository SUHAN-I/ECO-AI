# 🗑️ YOLO11 Trash Detection Model

Fine-tuned YOLO11 model for detecting and classifying recyclable materials and trash.

## 📊 Model Details

| Attribute | Value |
|-----------|-------|
| **Base Model** | YOLO11n (Nano) |
| **Task** | Object Detection |
| **Input Size** | 640x640 |
| **Classes** | 6 |
| **Framework** | PyTorch / ONNX |

## 🏷️ Classes

| ID | Class | Description |
|----|-------|-------------|
| 0 | cardboard | Cardboard boxes, packaging |
| 1 | glass | Glass bottles, jars |
| 2 | metal | Cans, metal scraps |
| 3 | paper | Newspapers, office paper |
| 4 | plastic | Plastic bottles, containers |
| 5 | trash | General waste |

## 📥 Download Model (No API Required)

### Direct Download Links

| Format | Link | Size |
|--------|------|------|
| PyTorch | [Download .pt](https://huggingface.co/SUHAN-I/YOLO11/resolve/main/yolo11_trash_detection.pt) | ~5.5 MB |
| ONNX | [Download .onnx](https://huggingface.co/SUHAN-I/YOLO11/resolve/main/yolo11_trash_detection.onnx) | ~10 MB |

### Using wget/curl
```bash
# PyTorch Model
wget https://huggingface.co/SUHAN-I/YOLO11/resolve/main/yolo11_trash_detection.pt

# ONNX Model
wget https://huggingface.co/SUHAN-I/YOLO11/resolve/main/yolo11_trash_detection.onnx
