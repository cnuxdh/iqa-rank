import os
import sys
import glob
import json
import argparse

from root_dir import MODELS_DIR, ROOT_DIR

p = os.path.dirname(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))))
if p not in sys.path:
    sys.path.append(p)

from src_code.utils.utils import calc_mean_score, save_json
from src_code.handlers.model_builder import Nima
from src_code.handlers.data_generator import TestDataGenerator


def image_file_to_json(img_path):
    img_dir = os.path.dirname(img_path)
    img_id = os.path.basename(img_path).split('.')[0]

    return img_dir, [{'image_id': img_id}]


def image_dir_to_json(img_dir, img_type='jpg'):
    img_paths = glob.glob(os.path.join(img_dir, '*.' + img_type))

    samples = []
    for img_path in img_paths:
        img_id = os.path.basename(img_path).split('.')[0]
        samples.append({'image_id': img_id})

    return samples


def predict(model, data_generator):
    return model.predict_generator(data_generator, workers=8, use_multiprocessing=True, verbose=1)


def main(base_model_name, weights_file, image_source, predictions_file, img_format='jpg'):
    # load samples
    if os.path.isfile(image_source):
        image_dir, samples = image_file_to_json(image_source)  # 图片文件夹和样本
    else:
        image_dir = image_source
        samples = image_dir_to_json(image_dir, img_type='jpg')

    # build model and load weights
    nima = Nima(base_model_name, weights=None)
    nima.build()
    nima.nima_model.load_weights(weights_file)  # 加载参数

    # initialize data generator，生成测试样本
    data_generator = TestDataGenerator(samples, image_dir, 64, 10, nima.preprocessing_function(),
                                       img_format=img_format)

    # get predictions
    predictions = predict(nima.nima_model, data_generator)

    # calc mean scores and add to samples
    for i, sample in enumerate(samples):
        sample['mean_score_prediction'] = calc_mean_score(predictions[i])

    print(json.dumps(samples, indent=2))

    if predictions_file is not None:
        save_json(samples, predictions_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument('-b', '--base-model-name', help='CNN base model name', required=True)
    # parser.add_argument('-w', '--weights-file', help='path of weights file', required=True)
    # parser.add_argument('-is', '--image-source', help='image directory or file', required=True)
    # parser.add_argument('-pf', '--predictions-file', help='file with predictions', required=False, default=None)

    args = parser.parse_args()
    args.base_model_name = 'MobileNet'

    args.weights_file = os.path.join(MODELS_DIR, 'MobileNet/weights_mobilenet_technical_0.11.hdf5')
    args.image_source = os.path.join(ROOT_DIR, 'src_code/tests/test_images/42042.jpg')
    args.predictions_file = None

    main(**args.__dict__)
