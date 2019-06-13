from keras.models import Model
from keras.applications import MobileNet as ConvNet
from keras.applications.mobilenet import preprocess_input
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Flatten
from pathlib import Path, PosixPath
from typing import Tuple
from PIL import Image
from numpy.linalg import norm

import numpy as np


class CNN:
    def __init__(self) -> None:
        self.model_full = ConvNet(include_top=True)
        x = Flatten()(self.model_full.layers[-3].output) # hard-coded slice at -3 (conv layer closest to the output layer)
        self.model = Model(inputs=self.model_full.input, outputs=[x])
        self.TARGET_SIZE = (224, 224)
        self.BATCH_SIZE = 64

    def image_preprocess(self, pillow_image: Image) -> np.ndarray:
        im_res = pillow_image.resize(self.TARGET_SIZE)
        im_arr = np.array(im_res)
        return im_arr

    def convert_to_array(self, path_image: None) -> np.ndarray:
        try:
            if isinstance(path_image, Path):
                im = Image.open(path_image)
            elif isinstance(path_image, np.ndarray):
                im = path_image.astype('uint8') # fromarray can't take float32/64
                im = Image.fromarray(im)
            else:
                raise Exception
            im_arr = self.image_preprocess(im)
            return im_arr
        except Exception:
            print('Check Input Format! Input should be either a Path Variable or a numpy array!')
            raise

    def cnn_image(self, path_image: str) -> np.ndarray:
        im_arr = self.convert_to_array(path_image)
        im_arr_proc = preprocess_input(im_arr)
        im_arr_shaped = np.array(im_arr_proc)[np.newaxis, :]
        return self.model.predict(im_arr_shaped)

    @staticmethod
    def get_sub_dir(path_dir: Path) -> str:
        return path_dir.parts[-1]

    @staticmethod
    def get_parent_dir(path_dir: Path) -> PosixPath:
        return path_dir.parent

    def generator(self, path_dir: Path) -> ImageDataGenerator:
        sub_dir = self.get_sub_dir(path_dir)
        img_gen = ImageDataGenerator(preprocessing_function=preprocess_input)
        parent_dir = self.get_parent_dir(path_dir)

        img_batches = img_gen.flow_from_directory(
            directory=parent_dir,
            target_size=self.TARGET_SIZE,
            batch_size=self.BATCH_SIZE,
            color_mode='rgb',
            shuffle=False,
            classes=[sub_dir],
            class_mode=None
        )
        return img_batches

    def cnn_dir(self, path_dir: Path) -> Tuple[np.ndarray, dict]:
        image_generator = self.generator(path_dir)
        feat_vec = self.model.predict_generator(image_generator, len(image_generator), verbose=1)
        filenames = [i.split('/')[-1] for i in image_generator.filenames]
        file_mapping = dict(zip(range(len(image_generator.filenames)), filenames))
        return feat_vec, file_mapping


class CosEval:
    def __init__(self, query_vector, ret_vector):
        self.query_vector = query_vector
        self.ret_vector = ret_vector
        self.normalize_vector_matrices()

    def normalize_vector_matrices(self):
        self.normed_query_vector = self.get_normalized_matrix(self.query_vector)
        self.normed_ret_vector = self.get_normalized_matrix(self.ret_vector)

    @staticmethod
    def get_normalized_matrix(x):
        x_norm_per_row = norm(x, axis=1)
        x_norm_per_row = x_norm_per_row[:, np.newaxis]  # adding another axis
        x_norm_per_row_tiled = np.tile(x_norm_per_row, (1, x.shape[1]))
        x_normalized = x / x_norm_per_row_tiled
        return x_normalized