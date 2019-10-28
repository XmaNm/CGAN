#coding:utf-8
import sys
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
from nets import *
from datas import *
from rsb import *

def sample_z(m, n):
    return np.random.uniform(-1., 1., size=[m, n])

def sample_y(m, n, ind):
    y = np.zeros([m, n])
    for i in range(m):
        y[i,i/4] = 1
    return y

def concat(z, y):
    return tf.concat([z,y], 1)

def conv_concat(x, y):
    bz = tf.shape(x)[0]
    print('bz',bz)
    y = tf.reshape(y, [bz, 1, 1, 10])
    return tf.concat([x, y*tf.one([bz, 28, 28, 10])], 3)

class CGAN():
    def __init__(self, generator, discriminator, data):
        self.generator = generator
        self.discriminator = discriminator
        self.data = data

        self.z_dim = self.data.z_dim
        self.y_dim = self.data.y_dim
        self.size = self.data.size
        self.channel = self.data.channel

        self.X = tf.placeholder(tf.float32, shape=[None, self.size, self.size, self.channel])
        self.z = tf.placeholder(tf.float32, shape=[None, self.z_dim])
        self.y = tf.placeholder(tf.float32, shape=[None, self.y_dim])

        self.G_sample = self.generator(concat(self.z, self.y))
        self.D_real, _ = self.discriminator(conv_concat(self.X, self.y))
        self.D_fake, _ = self.discriminator(conv_concat(self.G_sample, self.y), reuse=True)
        self.D_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self.D_real,
                                                                             labels=tf.ones_like(self.D_real))) +\
                      tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self.D_fake,
                                                                            labels=tf.zeros_like(self.D_fake)))
        self.G_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self.D_fake,
                                                                             labels=tf.ones_like(self.D_fake)))
        self.D_solver = tf.train.AdamOptimizer().minimize(self.D_loss, var_list=self.discriminator.vars)
        self.G_solver = tf.train.AdamOptimizer().minimize(self.G_loss, var_list=self.generator.vars)
        self.saver = tf.train.Saver()
        self.sess = tf.Session()
    def train(self,sample_dir,ckpt_dir = 'ckpt',training_epoches=1000,batch_size=64):
        fig_count = 0
        self.sess.run(tf.global_variables_initializer())
        for epoch in range(training_epoches):
            X_b, y_b = self.data(batch_size)
            self.sess.run(self.D_solver,
                          feed_dict={self.X:X_b,self.y:y_b,self.z:sample_z(batch_size,self.z_dim)})
            k = 1
            for _ in range(k):
                self.sess.run(self.G_solver,
                              feed_dict={self.y:y_b,self.z:sample_z(batch_size,self.z_dim)})
                if epoch %100 ==0 or epoch <100:
                    D_loss_curr = self.sess.run(self.D_loss,
                                                feed_dict={self.X:X_b,self.y:y_b,self.z:sample_z(batch_size,self.z_dim)})
                    G_loss_curr = self.sess.run(self.G_loss,
                                                feed_dict={self.y:y_b,self.z:sample_z(batch_size,self.z_dim)})
                    print('Iter: {}; D loss: {:.4}; G_loss: {:.4}'.format(epoch, D_loss_curr, G_loss_curr))

                    if epoch % 1000 == 0:
                        y_s = sample_y(16, self.y_dim, fig_count % 10)
                        samples = self.sess.run(self.G_sample,
                                                feed_dict={self.y: y_s, self.z: sample_z(16, self.z_dim)})
                        fig = self.data.data2fig(samples)
                        plt.savefig('{}/{}_{}.png'.format(sample_dir, str(fig_count).zfill(3),str(fig_count%10)),
                                    bbox_inches = 'tight')

if __name__ == '__main__':
    sample_dir = 'Samples/mnist_cgan_conv'
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir)

    # param
    generator = inference([32, 32, 3], 5, reuse=False)
    discriminator = D_conv_mnist()

    data = mnist()

    # run
    cgan = CGAN(generator, discriminator, data)
    cgan.train(sample_dir)