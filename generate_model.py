import os
os.makedirs('models', exist_ok=True)
from app.ml.train_model import create_model
print('Building model...')
m = create_model()
m.save('models/plant_disease_model.h5')
print('Model saved successfully!')
