from matplotlib import pyplot as plt

import numpy as np
import os
import tensorflow as tf
import PIL

from nets import inception
from datasets import naver
from preprocessing import inception_preprocessing

checkpoints_dir = '/tfpath/naver/train_inception_resnet_v2_naver_logs/'

slim = tf.contrib.slim
batch_size = 10
images_dir = '/tfpath/naver/naver/'
image_size = inception.inception_resnet_v2.default_image_size


def load_batch(dataset, batch_size=32, height=299, width=299, is_training=False):
    """Loads a single batch of data.

    Args:
      dataset: The dataset to load.
      batch_size: The number of images in the batch.
      height: The size of each image after preprocessing.
      width: The size of each image after preprocessing.
      is_training: Whether or not we're currently training or evaluating.

    Returns:
      images: A Tensor of size [batch_size, height, width, 3], image samples that have been preprocessed.
      images_raw: A Tensor of size [batch_size, height, width, 3], image samples that can be used for visualization.
      labels: A Tensor of size [batch_size], whose values range between 0 and dataset.num_classes.
    """
    data_provider = slim.dataset_data_provider.DatasetDataProvider(
        dataset, common_queue_capacity=32,
        common_queue_min=8)
    image_raw, label = data_provider.get(['image', 'label'])

    # Preprocess image for usage by Inception.
    image = inception_preprocessing.preprocess_image(image_raw, height, width, is_training=is_training)

    # Preprocess the image for display purposes.
    image_raw = tf.expand_dims(image_raw, 0)
    image_raw = tf.image.resize_images(image_raw, [height, width])
    image_raw = tf.squeeze(image_raw)

    # Batch it up.
    images, images_raw, labels = tf.train.batch(
        [image, image_raw, label],
        batch_size=batch_size,
        num_threads=1,
        capacity=2 * batch_size)

    return images, images_raw, labels


with tf.Graph().as_default():
    tf.logging.set_verbosity(tf.logging.INFO)

    dataset = naver.get_split('validation', images_dir)
    images, images_raw, labels = load_batch(dataset, height=image_size, width=image_size)

    # Create the model, use the default arg scope to configure the batch norm parameters.
    with slim.arg_scope(inception.inception_resnet_v2_arg_scope()):
        logits, _ = inception.inception_resnet_v2(images, num_classes=dataset.num_classes, is_training=True)

    probabilities = tf.nn.softmax(logits)

    checkpoint_path = tf.train.latest_checkpoint(checkpoints_dir)
    init_fn = slim.assign_from_checkpoint_fn(
        checkpoint_path,
        slim.get_variables_to_restore())

    with tf.Session() as sess:
        with slim.queues.QueueRunners(sess):
            sess.run(tf.initialize_local_variables())
            init_fn(sess)
            np_probabilities, np_images_raw, np_labels = sess.run([probabilities, images_raw, labels])
            print('-----------------------------------------------111111111')
            for i in range(batch_size):
                print(i)
                image = np_images_raw[i, :, :, :]
                true_label = np_labels[i]
                predicted_label = np.argmax(np_probabilities[i, :])
                predicted_name = dataset.labels_to_names[predicted_label]
                true_name = dataset.labels_to_names[true_label]

                plt.figure()
                plt.imshow(image.astype(np.uint8))
                plt.title('Ground Truth: [%s], Prediction [%s]' % (true_name, predicted_name))
                print('Ground Truth: [%s], Prediction [%s]' % (true_name, predicted_name))
                plt.axis('off')
                plt.show()