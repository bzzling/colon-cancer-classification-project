import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
from torchvision.models import vgg16
from PIL import Image
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
from tqdm import tqdm

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

train_dataset = ImageFolder(root='datasets/train', transform=transform)
val_dataset = ImageFolder(root='datasets/val', transform=transform)
test_dataset = ImageFolder(root='datasets/test', transform=transform)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

print("Class mapping:", train_dataset.class_to_idx)

vgg16_model = vgg16(pretrained=True)

vgg16_model.classifier = nn.Sequential(*list(vgg16_model.classifier.children())[:-1])
vgg16_model = vgg16_model.eval().to('cuda')  # Set to evaluation mode

def extract_features(data_loader, model, device='cuda'):
    features = []
    labels = []

    with torch.no_grad():
        for images, label in tqdm(data_loader):
            images = images.to(device)
            output = model(images)
            features.append(output.cpu().numpy())
            labels.append(label.numpy())

    features = np.vstack(features)
    labels = np.hstack(labels)
    return features, labels

train_features, train_labels = extract_features(train_loader, vgg16_model)
val_features, val_labels = extract_features(val_loader, vgg16_model)
test_features, test_labels = extract_features(test_loader, vgg16_model)

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(train_features, train_labels)

val_predictions = rf_model.predict(val_features)
val_accuracy = accuracy_score(val_labels, val_predictions)
print(f"Validation Accuracy: {val_accuracy:.2f}")

print("Validation Classification Report:")
print(classification_report(val_labels, val_predictions))

test_predictions = rf_model.predict(test_features)
test_accuracy = accuracy_score(test_labels, test_predictions)
print(f"Test Accuracy: {test_accuracy:.2f}")

print("Test Classification Report:")
print(classification_report(test_labels, test_predictions))

rf_model_path = "random_forest_colon_cancer.pth"
joblib.dump(rf_model, rf_model_path)
print(f"Random Forest model saved to {rf_model_path}")