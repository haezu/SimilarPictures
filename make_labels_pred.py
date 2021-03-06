from matplotlib import pyplot as plt

import numpy as np
import os
import tensorflow as tf
import cv2
from nets import inception
from preprocessing import inception_preprocessing
from utils import make_test_data, aug_subdir_label

CHECKPOINT_DIR = 'C:\\Users\\iceba\\develop\\data\\dummy\\pretrained_models\\train_log_inception_resnet_v2_naver'
PRED_IMG_RESULT = 'C:\\Users\\iceba\\develop\\data\\dummy\\result\\images'
TOTAL_IMAGE_DIR = 'C:\\Users\\iceba\\develop\\data\\dummy\\img\\naver_photos\\total'
ORIGINAL_IMAGE_DIR = 'C:\\Users\\iceba\\develop\\data\\dummy\\img\\naver_photos\\original'
slim = tf.contrib.slim

image_size = inception.inception_resnet_v2.default_image_size    

label_list = list()

with tf.Graph().as_default():

    user_images = [] # 복수의 원본 이미지
    user_processed_images = [] # 복수의 전처리된 이미지
    test_img_path = "C:\\Users\\iceba\\develop\\data\\dummy\\test"
    if make_test_data.test_dataset(ORIGINAL_IMAGE_DIR, test_img_path): print('make test dataset success')
    image_files = os.listdir(test_img_path) # 분류하고 싶은 이미지가 저장된 폴더

    for i in image_files:
        image_input = tf.read_file(test_img_path + os.sep + i)
        image = tf.image.decode_jpeg(image_input, channels=3)
        user_images.append(image)
        processed_image = inception_preprocessing.preprocess_image(image, image_size, image_size, is_training=False)
        user_processed_images.append(processed_image)
        
    processed_images  = tf.expand_dims(processed_image, 0)
    
    with slim.arg_scope(inception.inception_resnet_v2_arg_scope()):
        logits, _ = inception.inception_resnet_v2(user_processed_images, num_classes=153, is_training=False)
    probabilities = tf.nn.softmax(logits)


    init_fn = slim.assign_from_checkpoint_fn(
        os.path.join(CHECKPOINT_DIR, 'model.ckpt-19248'),
        slim.get_model_variables('InceptionResnetV2'))

    with tf.Session() as sess:
        init_fn(sess)
        np_images, probabilities = sess.run([user_images, probabilities])
    
    names = os.listdir("C:\\Users\\iceba\\develop\\data\\dummy\\img\\naver_photos\\total")
    

    for idx, files in enumerate(image_files):
        probabilitie = probabilities[idx, 0:]
        sorted_inds = [i[0] for i in sorted(enumerate(-probabilitie), key=lambda x:x[1])]
        
        for p in range(5):
            index = sorted_inds[p]
            print('Probability %0.2f%% => [%s]' % (probabilitie[index], names[index]))
            if p == 0:
                label_list.append([names[index], files])
        print()

label_list.sort()
map_label = dict()
aug_subdir_label.make_label_dict(TOTAL_IMAGE_DIR, map_label)
with open('labels_true.txt', 'a') as f1:
    with open('labels_pred2.txt', 'a') as f2:
        with open('img_paths.txt', 'a') as f3:
            for label, img in label_list:
                img_model = img.split('_')[0]
                f1.write(map_label[str(img_model)]+'\n')
                f2.write(str(label)+'\n')
                f3.write(str(img)+'\n')
                cpy_img = cv2.imread(test_img_path+os.sep+img)
                cv2.imwrite(PRED_IMG_RESULT+ os.sep+img, cpy_img)
