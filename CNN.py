# -*- coding: utf-8 -*-
"""CNN_FTIR.ipynb

Automatically generated by Colaboratory.

**Identifying Priority Functional group of molecules using Deep CNN given Fourier transform Infrared spectral images.**
"""

import tables
import numpy as np

from sklearn.model_selection import StratifiedKFold

from keras.models import Sequential, Model
from keras.layers import Dense, Conv2D, MaxPooling2D, Activation, Flatten, Dropout, BatchNormalization, add
from keras.optimizers import Adam

from keras import metrics
from imblearn.metrics import classification_report_imbalanced

import matplotlib.pyplot as plt
import statistics

from keras.callbacks import EarlyStopping

#Converting HDF5 to numpy array
def load_data():
	hdf5_path = "/Data.hdf5"
	hdf5_file = tables.open_file(hdf5_path, mode='r')


	data_num = hdf5_file.root.X.shape
	y = np.asarray(hdf5_file.root.y,dtype = np.int32)
	X = np.asarray(hdf5_file.root.X,dtype = np.float32)

	X = X/255.0

	hdf5_file.close()
	return X,y


#To convert Onehot encoding to label encoding 
def convert(y):
   y_label = np.ones(y.shape[0])
   for i in range(y.shape[0]):
    for j in range(y.shape[1]):
      if y[i][j]==1:
        y_label[i] = j
   return y_label

def create_model():
      model = Sequential()
      # input: 224x224 images with 1 channels -> (224, 224, 1) tensors.
      # this applies 32 convolution filters of size 7x7 each.
      model.add(Conv2D(32, (7, 7), activation='relu', input_shape=(224, 224, 1)))
      model.add(Conv2D(32, (5, 5), activation='relu'))
      model.add(MaxPooling2D(pool_size=(2, 2)))
      model.add(Dropout(0.5))

      model.add(Conv2D(64, (3, 3), activation='relu'))
      model.add(Conv2D(64, (3, 3), activation='relu'))
      model.add(MaxPooling2D(pool_size=(2, 2)))
      model.add(Dropout(0.5))

      model.add(Flatten())
      model.add(Dense(256, activation='relu'))
      model.add(BatchNormalization())
      model.add(Dropout(0.5))
      model.add(Dense(10, activation='softmax'))
      adam = Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-8)
      model.compile(loss='categorical_crossentropy', optimizer=adam,metrics=["accuracy"])
      
      return model

def plot_model_history(model_history):
    fig, axs = plt.subplots(1,2,figsize=(15,5))
    # summarize history for accuracy
    axs[0].plot(range(1,len(model_history.history['acc'])+1),model_history.history['acc'])
    axs[0].plot(range(1,len(model_history.history['val_acc'])+1),model_history.history['val_acc'])
    axs[0].set_title('Model Accuracy')
    axs[0].set_ylabel('Accuracy')
    axs[0].set_xlabel('Epoch')
    axs[0].set_xticks(np.arange(1,len(model_history.history['acc'])+1),len(model_history.history['acc'])/10)
    axs[0].legend(['train', 'val'], loc='best')
    # summarize history for loss
    axs[1].plot(range(1,len(model_history.history['loss'])+1),model_history.history['loss'])
    axs[1].plot(range(1,len(model_history.history['val_loss'])+1),model_history.history['val_loss'])
    axs[1].set_title('Model Loss')
    axs[1].set_ylabel('Loss')
    axs[1].set_xlabel('Epoch')
    axs[1].set_xticks(np.arange(1,len(model_history.history['loss'])+1),len(model_history.history['loss'])/10)
    axs[1].legend(['train', 'val'], loc='best')
    plt.show()

def plot_confidence_bound(scores):
	mean = statistics.mean(scores)
	std = statistics.stdev(scores)
	left = mean - 1.96*(std/10**(1/2.0))
	right = mean + 1.96*(std/10**(1/2.0))
	plt.figure()
	plt.axvline(mean, color="blue", ymax=0.75, label='Mean Accuracy')
	plt.axvline(left, color="red", ymax= 0.5, label='95% Confidence Interval')
	plt.axvline(right, color="red", ymax=0.5)
	plt.text(50, 0.8, ' Mean Accuracy = %0.2f%% \n Lower limit of CI = %0.2f%% \n Upper Limit of CI = %0.2f%%' %(mean, left, right), fontsize=12)
	plt.xlim([50, 100])
	plt.legend(fontsize=11)
	plt.xlabel('Accuracy (in %)', fontsize=12)
	plt.title('Mean Accuracy and Confidence Interval \n CNN')
	plt.show()

if __name__ == "__main__":
	X,y = load_data()
	skf = StratifiedKFold(n_splits=5,random_state=42,shuffle=True)

	y_label = convert(y)
	skf.get_n_splits(X, y_label)

	scores = []

	earlystop = EarlyStopping(monitor='val_acc', min_delta=0.01, patience=10, verbose=1, mode='auto')
	callbacks_list = [earlystop]

	cnt = 0

	for train_index, test_index in skf.split(X, y_label):
	   
	   X_train, X_test = X[train_index], X[test_index]
	   y_train, y_test = y[train_index], y[test_index]
	   
	   model = create_model()
	   model_info = model.fit(X_train,y_train,epochs = 1,validation_data=(X_test, y_test),callbacks = callbacks_list, batch_size=32)
	   pred_test = model.predict(X_test)

	   score = model.evaluate(X_test, y_test, verbose=0)

	   print model.metrics_names[1], score[1]*100
	   scores.append(score[1] * 100)

	   plot_model_history(model_info)   
	
	plot_confidence_bound(scores)

