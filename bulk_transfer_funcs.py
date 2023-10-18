import glob
import numpy as np
from PIL import Image, ImageEnhance
import torch
import torch.optim as optim
from torchvision import models
from torchvision import transforms as tf
import torch.nn.functional as F
import os


class BulkStyleTransfer:
    root_path = os.path.dirname(os.path.abspath("__file__"))

    vgg = models.vgg19(pretrained=True).features

    for param in vgg.parameters():
        param.requires_grad_(False)

    device = torch.device("cpu")

    if torch.cuda.is_available():
        device = torch.device("cuda")

    vgg.to(device)

    mean = (0.485, 0.456, 0.406)
    std = (0.229, 0.224, 0.225)

    layers_of_interest = {'0': 'conv1_1',
                          '5': 'conv2_1',
                          '10': 'conv3_1',
                          '19': 'conv4_1',
                          '21': 'conv4_2',
                          '28': 'conv5_1'}

    weights = {'conv1_1': 1.0,
               'conv2_1': 0.75,
               'conv3_1': 0.35,
               'conv4_1': 0.25,
               'conv5_1': 0.15}

    def __init__(self,
                 root_path=root_path,
                 image_folder=None,
                 style_folder=None,
                 style_image=None,
                 out_folder=None):
        self.root_path = root_path
        self.image_folder = image_folder
        self.style_folder = style_folder
        self.style_image = style_image
        self.out_folder = out_folder

    def create_output_folder(self):
        if not os.path.exists(os.path.join(self.root_path, self.out_folder)):
            os.mkdir(os.path.join(self.root_path, self.out_folder))

    def open_style_image(self):
        style_img = Image.open(os.path.join(self.root_path, self.style_folder, self.style_image)).convert('RGB')

        return style_img

    def transformation(self, img):

        tasks = tf.Compose([tf.Resize(500),
                            tf.ToTensor(),
                            tf.Normalize(self.mean, self.std)])

        img = tasks(img)
        img = img.unsqueeze(0)

        return img

    def tensor_to_image(self, tensor):

        image = tensor.clone().detach()
        image = image.cpu().numpy().squeeze()

        image = image.transpose(1, 2, 0)

        image *= np.array(self.std) + np.array(self.mean)
        image = image.clip(0, 1)

        return image

    def apply_model_and_extract_features(self, image, model):
        x = image

        features = {}

        for name, layer in model._modules.items():
            x = layer(x)

            if name in self.layers_of_interest:
                features[self.layers_of_interest[name]] = x

        return features

    def calculate_gram_matrix(self, tensor):

        _, channels, height, width = tensor.size()

        tensor = tensor.view(channels, height * width)

        gram_matrix = torch.mm(tensor, tensor.t())

        gram_matrix = gram_matrix.div(channels * height * width)

        return gram_matrix

    def run_bulk_transfer(self):
        style_image_open = self.open_style_image()

        style_image_open = self.transformation(style_image_open).to(self.device)

        style_img_features = self.apply_model_and_extract_features(style_image_open, self.vgg)

        style_features_gram_matrix = {layer: self.calculate_gram_matrix(style_img_features[layer]) for layer in
                                      style_img_features}

        img_lst = []

        # reads image filename from directory and appends to list
        for name in glob.glob(os.path.join(self.root_path, self.image_folder) + "/*.jpg"):
            img_lst.append(name)

        # sorts the list by numeric order to check output against input
        img_lst.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

        count = 0

        for image in img_lst:

            content_img = Image.open(image).convert('RGB')

            enhancer = ImageEnhance.Brightness(content_img)

            factor = 1.15

            content_img = enhancer.enhance(factor)

            content_img = self.transformation(content_img).to(self.device)

            content_img_features = self.apply_model_and_extract_features(content_img, self.vgg)

            target = content_img.clone().requires_grad_(True).to(self.device)

            optimizer = optim.Adam([target], lr=0.003)

            for i in range(1, 2000):
                target_features = self.apply_model_and_extract_features(target, self.vgg)

                content_loss = F.mse_loss(target_features['conv4_2'], content_img_features['conv4_2'])

                style_loss = 0

                for layer in self.weights:
                    target_feature = target_features[layer]

                    target_gram_matrix = self.calculate_gram_matrix(target_feature)
                    style_gram_matrix = style_features_gram_matrix[layer]

                    layer_loss = F.mse_loss(target_gram_matrix, style_gram_matrix)
                    layer_loss *= self.weights[layer]

                    _, channels, height, width = target_feature.shape

                    style_loss += layer_loss

                total_loss = 1000000 * style_loss + content_loss

                if i % 500 == 0:
                    print('Epoch {}:, Style Loss : {:4f}, Content Loss : {:4f}'.format(i, style_loss, content_loss))

                optimizer.zero_grad()

                total_loss.backward()

                optimizer.step()

            count += 1

            out = self.tensor_to_image(target)

            img_out = Image.fromarray((out * 255).astype('uint8'), 'RGB')

            img_out.save(os.path.join(self.root_path, self.out_folder) + "/image" + str(count) + ".png",
                         "PNG",
                         progressive=True,
                         quality=100,
                         optimize=True)
