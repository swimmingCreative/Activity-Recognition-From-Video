import warnings
warnings.filterwarnings("ignore")

from data_loader import TrainGenerator, CVGenerator
from utils import model_lstm_without_top, model_without_top

from keras.layers import Conv2D, MaxPooling2D, LSTM
from keras.layers import Dense, Flatten
from keras.layers import Activation, Dropout, Lambda
from keras.layers import ZeroPadding2D, BatchNormalization, GlobalAveragePooling1D
from keras.layers.wrappers import TimeDistributed
from keras import optimizers
from keras.callbacks import ModelCheckpoint
from utils import TrainValTensorBoard
from keras.models import Model
import argparse
import os
from keras.callbacks import ReduceLROnPlateau

config = {'data_path'     :  '../../data/',
          'batch_size'    :  64,
          'epochs'        :  20,
          'learning_rate' :  0.01,
          'decay_rate'    :  0.5, 
          'train_frames'  :  8000,
          'cv_frames'     :  800,
          'initial_epoch'   :  0}


def get_args():
    global config
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument('--load_checkpoint', default='', help='Path to hdf5 file to restore model from checkpoint')
    argparser.add_argument('--initial_epoch', default=0, help='start_epoch parameter in model.fit()')
    args = argparser.parse_args()
    return args


def main():
    args = get_args()
    config['load_checkpoint'] = args.__dict__['load_checkpoint']
    config['initial_epoch'] = int(args.__dict__['initial_epoch'])

    input_shape = (224, 224, 3)

    train_gen = TrainGenerator(config)
    cv_gen = CVGenerator(config)

    len_train = len(train_gen.train_paths)
    len_CV = len(cv_gen.cv_paths)

    print('len_train : ', len_train)
    print('len_CV : ', len_CV)

    model = model_without_top(input_shape)

    if os.path.isfile('../weights/vgg16_weights_without_top.h5'):
        model.load_weights('../weights/vgg16_weights_without_top.h5')
        print('Loaded VGG16 weights')
        
    model.add(Flatten())

    for layer in model.layers:
        layer.trainable = False

    model.add( Dense(128) )
    model.add(Activation('relu') )
    model.add( Dropout(0.3) )
    model.add(Dense(7))
    model.add(Activation('softmax'))

    optim = optimizers.Adam(lr = config['learning_rate'], decay = config['decay_rate'])
    model.compile(optimizer=optim,
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    if config['load_checkpoint'] != '':
        model.load_weights(config['load_checkpoint'])
        print('Successfully loaded weights from %s' % config['load_checkpoint'])
    else:
        print('No checkpoint found')
    model.summary()

    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=0.0001, verbose=1)

    filepath = 'model/model-{epoch:02d}-{val_loss:.2f}.hdf5'

    checkpoint = ModelCheckpoint(filepath, monitor='val_loss', save_best_only=True, verbose=1, mode='auto')
    callbacks_list = [checkpoint, TrainValTensorBoard(write_graph=False), reduce_lr]

    print('\n', config, '\n')

    hist_obj = model.fit_generator(
            generator = train_gen,
            callbacks = callbacks_list, 
            epochs = config['epochs'],
            steps_per_epoch = int(len_train/config['batch_size']),
            verbose=1,
            validation_data = cv_gen,
            validation_steps = int(len_CV/config['batch_size']),
            workers = 4,
            use_multiprocessing=True, 
            initial_epoch = config['initial_epoch']
           )

    train_loss = hist_obj.history['loss']
    val_loss = hist_obj.history['val_loss']
    train_acc = hist_obj.history['acc']
    val_acc = hist_obj.history['val_acc']

    print('train_loss')
    print(train_loss)

    print('val_loss')
    print(val_loss)

    print('train_acc')
    print(train_acc)

    print('val_acc')
    print(val_acc)

if __name__ == '__main__':
    main()
