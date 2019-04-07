# -*- coding: utf-8 -*-
"""project3

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_lme4n4E95muCS-V3VZb7AefD0vSWBqr

**Step 1**: Setting up Google Colab
"""

!pip install PyDrive

import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials

auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

#download the dataset
download1 = drive.CreateFile({'id': '1qxLPeBqDOydXsG5z2N2xQDIRi20kAOml'})

download1.GetContentFile('ground_truth.zip')
!unzip ground_truth.zip

#download the dataset
download2 = drive.CreateFile({'id': '13xES8GAhlEgC-6wHVl20PUowsmoN9VKo'})

download2.GetContentFile('tesseract.zip')
!unzip tesseract.zip

"""**Step 2** : Import the libraries we’ll need during our model building phase."""

import string
import glob
import os
import itertools
import collections
import timeit
import random
import pandas 
import numpy

"""**Step 3**: preprocessing of the text"""

def clean_text(word):
  res=[]
  for w in word:
    if w not in string.ascii_lowercase:
      continue
    res.append(w.lower())
  return ''.join(res)



"""**Error Detection**"""

# We have RGB images, we should set grayscale as False
word_list=[]
file_names = glob.glob(os.path.join(os.getcwd(), 'ground_truth', '*.txt'))
for i in range(len(file_names)):
  with open(file_names[i]) as file:
    raw=file.read().split()
    word_list+=list(filter(lambda x: 1<len(x)<21,list(map(clean_text,raw))))
print(word_list)

word_length=collections.defaultdict(list)
for word in word_list:
  word_length[len(word)].append(word)

word_dic=collections.defaultdict(dict)
for wl in word_length:
  for i, j in itertools.combinations(range(wl), 2):
    positional_ngram=[[0]*26 for i in range(26)]
    for w in word_length[wl]:
      positional_ngram[ord(w[i])-97][ord(w[j])-97]=1
    word_dic[wl][(i,j)]=positional_ngram
print(word_dic[3])

test_list=[]
file_names1 = glob.glob(os.path.join(os.getcwd(), 'tesseract', '*.txt'))
for i in range(len(file_names1)):
  with open(file_names1[i]) as file:
    raw=file.read().split()
    test_list+=list(filter(lambda x: 1<len(x)<21,list(map(clean_text,raw))))
print(test_list)

error=[]
context=[]
for idx, tw in enumerate(test_list):
  for i, j in itertools.combinations(range(len(tw)), 2):
    if not word_dic[len(tw)][(i,j)][ord(tw[i])-97][ord(tw[j])-97]:
      error.append(tw)
      if idx==0:
        context.append(('',tw,test_list[idx+1]))
      elif idx==len(test_list)-1:
        context.append((test_list[idx-1],tw,''))
      else:
        context.append((test_list[idx-1],tw,test_list[idx+1]))
      break
print(context)

def find_candidates(word):
  letters='abcdefghijklmnopqrstuvwxyz'
  candidates={'insertion':[],'deletion':[],'substitution':[],'reversal':[]}
  #insertion
  for i in range(len(word)+1):
    for l in letters:
      new=word[:i]+l+word[i:]
      if new in word_list:
        if i>0:
          pre=ord(word[i-1])-97
        else:
          pre=27
        candidates['insertion'].append((new,(pre,ord(l)-97)))
  #deletion
  for i in range(len(word)):
    new=word[:i]+word[i+1:]
    if new in word_list:
      if i>0:
          pre=ord(word[i-1])-97
      else:
          pre=27
      now=ord(word[i])-97
      candidates['deletion'].append((new,(pre,now)))
  #substitution:
  for i in range(len(word)):
    for l in letters:
      if word[i]!=l:
        new=word[:i]+l+word[i+1:]
        if new in word_list:
          candidates['substitution'].append((new,(ord(l)-97,ord(word[i])-97)))
  #reversal:
  for i in range(len(word)-1):
    new=list(word)
    new[i],new[i+1]=new[i+1],new[i]
    new=''.join(new)
    if new in word_list:
      candidates['reversal'].append((new,(ord(word[i])-97,ord(word[i+1])-97)))
  return candidates

print(find_candidates('acress'))

all_candidates=collections.defaultdict(dict)
for e in error:
  all_candidates[e]=find_candidates(e)
print(all_candidates)

"""As it is a multi-class classification problem (3 classes), we will one-hot encode the target variable."""

y=train['Label'].values
y = to_categorical(y)



"""**Step 4**: Creating a validation set from the training data."""

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.2)

"""**VGG19**
A common and highly effective approach to deep learning on small image datasets is to use a pretrained network. A pretrained network is a saved network that was previously trained on a large dataset, typically on a large-scale image-classification task. If this original dataset is large enough and general enough, then the spatial hierarchy of features learned by the pretrained network can effectively act as a generic model of the visual world, and hence its features can prove useful for many different computer-vision problems, even though these new problems may involve completely different classes than those of the original task.
"""

# Resize the images as 150 * 150 as required by VGG19
from keras.preprocessing.image import img_to_array, array_to_img

X_train = np.asarray([img_to_array(array_to_img(im, scale=False).resize((150,150))) for im in X_train])
X_test = np.asarray([img_to_array(array_to_img(im, scale=False).resize((150,150))) for im in X_test])

# Display the new shape
X_train.shape, X_test.shape

# Normalise the data and change data type
X_train = X_train.astype('float32')
X_train /= 255

X_test = X_test.astype('float32')
X_test /= 255

from sklearn.model_selection import train_test_split

# Here I split original training data to sub-training (80%) and validation data (20%)
X_train1, X_val, y_train1, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=13)

# Check the data size whether it is as per tensorflow and VGG19 requirement
X_train1.shape, X_val.shape, y_train1.shape, y_val.shape

from keras.applications import VGG19

# Create the base model of VGG19
vgg19 = VGG19(weights='imagenet', include_top=False, input_shape = (150, 150, 3), classes = 3)

vgg19.summary()

"""**step 5**: Extract features.

**Feature Extraction**
Feature extraction consists of using the representations learned by a previous network to extract interesting features from new samples. These features are then run through a new classifier, which is trained from scratch.

CNNs used for image classification comprise two parts: they start with a series of pooling and convolution layers, and they end with a densely-connected classifier. The first part is called the "convolutional base" of the model. In the case of convnets, "feature extraction" will simply consist of taking the convolutional base of a previously-trained network, running the new data through it, and training a new classifier on top of the output.
"""

from keras.applications.vgg19 import preprocess_input

# Preprocessing the input 
X_train1 = preprocess_input(X_train1)
X_val = preprocess_input(X_val)
X_test = preprocess_input(X_test)

# Extracting features
train_features = vgg19.predict(np.array(X_train1),verbose=1)
test_features = vgg19.predict(np.array(X_test),verbose=1)
val_features = vgg19.predict(np.array(X_val),verbose=1)

# Saving the features so that they can be used for future
np.savez("train_features", train_features, y_train)
np.savez("test_features", test_features, y_test)
np.savez("val_features", val_features, y_val)

# Current shape of features
print(train_features.shape, "\n",  test_features.shape, "\n", val_features.shape)

# Flatten extracted features
train_features = np.reshape(train_features, (960, 4*4*512))
test_features = np.reshape(test_features, (300, 4*4*512))
val_features = np.reshape(val_features, (240, 4*4*512))

"""**Step 6**: Define the model structure."""

from keras.layers import Dense, Dropout
from keras.models import Model
from keras import models
from keras import layers
from keras import optimizers

# Add Dense and Dropout layers on top of VGG19 pre-trained
model = models.Sequential()
model.add(layers.Dense(512, activation='relu', input_dim=4 * 4 * 512))
model.add(layers.Dropout(0.5))
model.add(layers.Dense(3, activation="softmax"))

import keras

# Compile the model
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])

# Train the the model
history = model.fit(train_features, y_train1,
          epochs=10,
          validation_data=(val_features, y_val))

score = model.evaluate(test_features, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

"""**Training CNN Models**

I will create a variety of different CNN-based classification models to evaluate performances on our training dataset. I will be building our model using the Keras framework. Here are the list of models I will try out and compare their results:

1.   CNN with 1 Convolutional Layer
2.   CNN with 3 Convolutional Layer
"""

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.2)

"""CNN with 1 Convolutional Layer"""

cnn1 = Sequential()
cnn1.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28,28,3)))
cnn1.add(MaxPooling2D(pool_size=(2, 2)))
cnn1.add(Dropout(0.2))

cnn1.add(Flatten())

cnn1.add(Dense(128, activation='relu'))
cnn1.add(Dense(3, activation='softmax'))
cnn1.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])
cnn1.summary()

history1 = cnn1.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

score1 = cnn1.evaluate(X_test, y_test, verbose=0)
print('Test loss:', score1[0])
print('Test accuracy:', score1[1])

"""CNN with 3 Convolutional Layer"""

cnn3 = Sequential()
cnn3.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28,28,3)))
cnn3.add(MaxPooling2D((2, 2)))
cnn3.add(Dropout(0.25))

cnn3.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
cnn3.add(MaxPooling2D(pool_size=(2, 2)))
cnn3.add(Dropout(0.25))

cnn3.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
cnn3.add(Dropout(0.4))

cnn3.add(Flatten())

cnn3.add(Dense(128, activation='relu'))
cnn3.add(Dropout(0.3))
cnn3.add(Dense(3, activation='softmax'))
cnn3.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])
cnn3.summary()

history3 = cnn3.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

score3 = cnn3.evaluate(X_test, y_test, verbose=0)
print('Test loss:', score3[0])
print('Test accuracy:', score3[1])

"""**step 7**: Visualize the results"""

import matplotlib.pyplot as plt
# %matplotlib inline

accuracy = history3.history['acc']
val_accuracy = history3.history['val_acc']
loss = history3.history['loss']
val_loss = history3.history['val_loss']
epochs = range(len(accuracy))

plt.plot(epochs, accuracy, 'bo', label='Training accuracy')
plt.plot(epochs, val_accuracy, 'b', label='Validation accuracy')
plt.title('Training and validation accuracy')
plt.legend()
plt.figure()

plt.plot(epochs, loss, 'bo', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.legend()
plt.show()

"""**Step 8: **Classification Report"""

test_data = pd.read_csv('train_set/label.csv')

test_image = []
for i in tqdm(range(test.shape[0])):
    img = image.load_img('train_set/LR/'+'img_'+test_data['Image'][i], target_size=(28,28,3), grayscale=False)
    img = image.img_to_array(img)
    img = img/255
    test_image.append(img)
test = np.array(test_image)

# making predictions
prediction = cnn3.predict_classes(test)

# get the indices to be plotted
y_true = test_data.iloc[:, 2]
correct = np.nonzero(prediction==y_true)[0]
incorrect = np.nonzero(prediction!=y_true)[0]

from sklearn.metrics import classification_report
target_names = ["Class {}".format(i) for i in range(3)]
print(classification_report(y_true, prediction, target_names=target_names))

for i, c in enumerate(correct[:9]):
    plt.subplot(3,3,i+1)
    plt.imshow(test[c].reshape(28,28,3), cmap='viridis', interpolation='none')
    plt.title("Predicted {}, Class {}".format(prediction[c], y_true[c]))
    plt.tight_layout()

for i, ic in enumerate(incorrect[0:9]):
    plt.subplot(3,3,i+1)
    plt.imshow(test[ic].reshape(28,28,3), cmap='viridis', interpolation='none')
    plt.title("Predicted {}, Class {}".format(prediction[ic], y_true[ic]))
    plt.tight_layout()

# creating submission file
sample = pd.read_csv('label.csv')
sample['predict_label'] = prediction
print(sample[:10])
sample.to_csv('sample.csv', header=True, index=False)
from google.colab import files
files.download("sample.csv")