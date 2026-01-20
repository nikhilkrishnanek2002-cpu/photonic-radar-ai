from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from data_preprocessing import create_dataset
from model import build_model

def train():
    X, y = create_dataset()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2)

    model = build_model()
    history = model.fit(Xtr, ytr, epochs=10, validation_data=(Xte, yte))

    model.save("results/radar_model.h5")

    plt.plot(history.history['accuracy'], label="Train")
    plt.plot(history.history['val_accuracy'], label="Val")
    plt.legend()
    plt.savefig("results/accuracy.png")
    plt.show()

    return model, Xte, yte
