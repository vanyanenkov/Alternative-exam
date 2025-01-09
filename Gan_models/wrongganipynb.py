# -*- coding: utf-8 -*-
"""wrongGanipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1S6T9MHDmgj05rknJIYptRQyQ7kZjAdXE

### Пример неправильной работы модели GAN без предварительной обработки значений(даже очень простая модель дискриминатора сразу понимает где неправильные данные и быстро учится безошибочно определять функцию потерь)
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch import optim
from torch.nn import Sigmoid, BatchNorm1d, Dropout, LeakyReLU, Linear, Module, ReLU, Sequential, functional, Tanh
from tqdm import tqdm
from torch.utils.data import DataLoader, TensorDataset

import re

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

import matplotlib.pyplot as plt

data = pd.read_csv('urinaset (2).csv')
data = data.iloc[:, 1:]

def replace_ranges_with_means(value):
    match = re.match(r"(\d+)-(\d+)", str(value))
    if str(value).startswith('>'):
        return int(value[1:]) + 5
    elif match:
        start, end = map(int, match.groups())
        return (start + end) / 2
    elif value == "TMTC":
        return 150
    else:
        try:
            return float(value)
        except ValueError:
            return np.nan

data['WBC'] = data['WBC'].apply(replace_ranges_with_means)
data['WBC'] = data['WBC'].fillna(data['WBC'].median())
data['RBC'] = data['RBC'].apply(replace_ranges_with_means)
data['RBC'] = data['RBC'].fillna(data['RBC'].median())
data = data.convert_dtypes()
data


def labelencoder(df):
    for c in df.columns:
        if df[c].dtype == 'string':
            df[c] = df[c].fillna('N')
            lbl = LabelEncoder()
            lbl.fit(list(df[c].values))
            df[c] = lbl.transform(df[c].values)
    return df


data = labelencoder(data)
data

df_x_train, df_x_test, df_y_train, df_y_test = train_test_split(
    data.drop("Diagnosis", axis=1),
    data["Diagnosis"],
    test_size=0.2,
)

# Преобразование данных в тензоры
X_train = torch.tensor(df_x_train.values.astype(np.float32), dtype=torch.float32)
X_test = torch.tensor(df_x_test.values.astype(np.float32), dtype=torch.float32)
y_train = torch.tensor(df_y_train.values, dtype=torch.float32).unsqueeze(1)
y_test = torch.tensor(df_y_test.values, dtype=torch.float32).unsqueeze(1)

batch_size = 32
train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

input_dim = df_x_train.shape[1]

# class CoachModel(nn.Module):
#     def __init__(self, input_dim):
#         super(CoachModel, self).__init__()
#         self.layers = nn.Sequential(
#             Linear(input_dim, 128),
#             ReLU(),
#             Dropout(0.2),
#             Linear(128, 128),
#             ReLU(),
#             Dropout(0.2),
#             Linear(128, 64),
#             ReLU(),
#             Dropout(0.2),
#             Linear(64, 1),
#             Sigmoid()
#         )

#     def forward(self, x):
#         return self.layers(x)


# model_coach = CoachModel(input_dim)

# optimizer = optim.Adam(model_coach.parameters())
# criterion = nn.BCELoss()  # Binary Cross Entropy Loss

# num_epochs = 25
# for epoch in range(num_epochs):
#     model_coach.train()
#     running_loss = 0.0
#     for batch_X, batch_y in train_loader:
#         optimizer.zero_grad()
#         outputs = model_coach(batch_X)
#         loss = criterion(outputs, batch_y)
#         loss.backward()
#         optimizer.step()
#         running_loss += loss.item()

# model_coach.eval()
# with torch.no_grad():
#     test_loss = 0.0
#     correct = 0
#     total = 0
#     for batch_X, batch_y in test_loader:
#         outputs = model_coach(batch_X)
#         loss = criterion(outputs, batch_y)
#         test_loss += loss.item()
#         predicted = (outputs >= 0.5).float()
#         correct += (predicted == batch_y).sum().item()
#         total += batch_y.size(0)

# accuracy = correct / total
# print(f"Test Loss: {test_loss / len(test_loader):.4f}")
# print(f"Test Accuracy: {accuracy:.4f}")

class my_Generator(nn.Module):
    def __init__(self, input_dim):
        super(my_Generator, self).__init__()
        self.layers = nn.Sequential(
            Linear(input_dim, 256),
            ReLU(),
            Dropout(0.2),
            Linear(256, 128),
            ReLU(),
            Dropout(0.2),
            Linear(128, 85),
            ReLU(),
            Dropout(0.2),
            Linear(85, 85),
            ReLU(),
            Dropout(0.2),
            Linear(85, input_dim),
            Tanh()
        )

    def forward(self, x):
        return self.layers(x)


class my_Discriminator(nn.Module):
    def __init__(self, input_dim):
        super(my_Discriminator, self).__init__()
        self.model = nn.Sequential(
            Linear(input_dim, 4),
            ReLU(),
            # Dropout(0.4),
            # Linear(4, 2),
            # ReLU(),
            # Dropout(0.4),
            # Linear(64, 32),
            # ReLU(),
            # Dropout(0.4),
            # Linear(32, 20),
            # ReLU(),
            # Dropout(0.4),
            Linear(4, 1),
            Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

my_Generator = my_Generator(input_dim)
my_Discriminator = my_Discriminator(input_dim)

optimizer_myG = optim.Adam(my_Generator.parameters(), lr=0.0002)
optimizer_myD = optim.Adam(my_Discriminator.parameters(), lr=0.0002)

# Параметры
num_epochs = 1000

d_losses = []
g_losses = []

# Тренировочный цикл
for epoch in range(num_epochs):
    for batch_X, batch_y in train_loader:
        batch_size = batch_X.size(0)

        # ================================
        # Обучение дискриминатора
        # ================================
        optimizer_myD.zero_grad()

        # Реальные данные
        real_labels = torch.ones(batch_size, 1)
        outputs_real = my_Discriminator(batch_X)
        d_loss_real = criterion(outputs_real, real_labels)

        # Сгенерированные данные
        noise = torch.randn(batch_size, input_dim)
        fake_data = my_Generator(noise)
        fake_labels = torch.zeros(batch_size, 1)
        outputs_fake = my_Discriminator(fake_data.detach())
        d_loss_fake = criterion(outputs_fake, fake_labels)

        # Общая ошибка дискриминатора
        d_loss = d_loss_real + d_loss_fake
        d_loss.backward()
        optimizer_myD.step()

        # ================================
        # Обучение генератора
        # ================================
        optimizer_myG.zero_grad()

        # Обманываем дискриминатор
        fake_labels = torch.ones(batch_size,
                                 1)
        outputs_fake = my_Discriminator(fake_data)
        g_loss = criterion(outputs_fake, fake_labels)
        g_loss.backward()
        optimizer_myG.step()

        d_losses.append(d_loss.item())
        g_losses.append(g_loss.item())

    if (epoch + 1) % 100 == 0:
        print(f"Epoch [{epoch + 1}/{num_epochs}], d_loss: {d_loss.item():.4f}, g_loss: {g_loss.item():.4f}")

d_losses
g_losses

# Построение графиков
plt.figure(figsize=(10, 5))
plt.plot(d_losses, label="Discriminator Loss")
plt.plot(g_losses, label="Generator Loss")
plt.xlabel("iterations")
plt.ylabel("Loss")
plt.title("Generator and Discriminator Loss During Training")
plt.legend()
plt.show()