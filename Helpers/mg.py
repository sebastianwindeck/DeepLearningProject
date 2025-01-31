# mg.py ist ein anderes Beispiel, dass die Generierung von Musikstück zum 
# Inhalt hat. Ebenso kurz, kompakt, übersichtlich, und läuft nach kleineren
# Anpassungen bei mir.
# Ursprünglich aus https://github.com/subpath/Keras_music_gereration/blob/master/Music%20gerenation%20with%20Keras%20and%20TF.ipynb.
# Generiert ein kurzes Stück, das man in VLC abspeielen kann (klingt noch nicht 
# so gut)



import mido
from mido import MidiFile, MidiTrack, Message
from keras.layers import LSTM, Dense, Activation, Dropout, Flatten
from keras.preprocessing import sequence
from keras.models import Sequential
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
import numpy as np


ifile = 'Samples/mary.mid'
ifile = 'Samples/MAPS_MUS-chpn-p7_SptkBGCl.mid' 
mid = MidiFile(ifile) 
numb_epochs = 25
notes = []
velocities = []

for msg in mid:
    if not msg.is_meta:
        if msg.channel == 0:
            if msg.type == 'note_on':
                data = msg.bytes()
                # append note and velocity from [type, note, velocity]
                note = data[1]
                velocity = data[2]
                notes.append(note)
                velocities.append(velocity)

combine = [[i,j] for i,j in zip(notes, velocities) ]

note_min = np.min(notes)
note_max = np.max(notes)
velocities_min = np.min(velocities)
velocities_max = np.max(velocities)

for i in combine:
    i[0] = 2*(i[0]-((note_min+note_max)/2))/(note_max-note_min)
    i[1] = 2*(i[1]-((velocities_min+velocities_max)/2))/(velocities_max-velocities_min)

X = []
Y = []
n_prev = 30
for i in range(len(combine)-n_prev):
    x = combine[i:i+n_prev]
    y = combine[i+n_prev]
    X.append(x)
    Y.append(y)
# save a seed to do prediction later
seed = combine[0:n_prev]

model = Sequential()
model.add(LSTM(256, input_shape=(n_prev, 2), return_sequences=True))
model.add(Dropout(0.6))
model.add(LSTM(128, input_shape=(n_prev, 2), return_sequences=True))
model.add(Dropout(0.6))
model.add(LSTM(64, input_shape=(n_prev, 2), return_sequences=False))
model.add(Dropout(0.6))
model.add(Dense(2))
model.add(Activation('linear'))
optimizer = Adam(lr=0.001)
model.compile(loss='mse', optimizer=optimizer)
filepath="./Checkpoints/checkpoint_model_{epoch:02d}.hdf5"
model_save_callback = ModelCheckpoint(filepath, monitor='val_acc', 
                                      verbose=1, save_best_only=False, 
                                      mode='auto', period=5)

model.fit(np.array(X), np.array(Y), 32, numb_epochs, verbose=1, callbacks=[model_save_callback])

prediction = []
x = seed
x = np.expand_dims(x, axis=0)

for i in range(300):
    preds = model.predict(x)
    x = np.squeeze(x)
    x = np.concatenate((x, preds))
    x = x[1:]
    x = np.expand_dims(x, axis=0)
    preds = np.squeeze(preds)
    prediction.append(preds)

for pred in prediction:
# Undo the preprocessing
    pred[0] = int((pred[0]/2)*(note_max-note_min) + (note_min+note_max)/2)
    pred[1] = int((pred[1]/2)*(velocities_max-velocities_min) + (velocities_min+velocities_max)/2)
    if pred[0] < 24:
        pred[0] = 24
    elif pred[0] > 102:
        pred[0] = 102
    if pred[1] < 0:
        pred[1] = 0
    elif pred[1] > 127:
        pred[1] = 127

mid = MidiFile()
track = MidiTrack()

t = 0
for note in prediction:
    # 147 means note_on
    note = np.asarray([147, note[0], note[1]])
    bytes = note.astype(int)
    msg = Message.from_bytes(bytes[0:3])
    t += 1
    msg.time = t
    track.append(msg)

mid.tracks.append(track)
mid.save(ifile.replace('.mid', '_g.mid'))
