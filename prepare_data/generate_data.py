import sys
sys.path.append('simple_HRNet_master')
import os
from video import PoseSeriesGenerator, Video, Person
import argparse
import torch
from torchvision.transforms import transforms
from models2.hrnet import HRNet
import numpy as np

def main():

    parser = argparse.ArgumentParser(description='Generate series of poses from RWF-2000 dataset.')
    parser.add_argument(
        '--data-path',
        type=str,
        help='The path to the folder containing videos',
        required=True
    )
    parser.add_argument(
        '--out',
        type=str,
        help='output file path',
        required=True
    )
    parser.add_argument(
        '--series-length',
        type=int,
        help='the length of a pose series',
        default=10
    )
    parser.add_argument(
        '--min_poses',
        type=int,
        help='minimum number of poses detected for a series to be considered valid',
        default=7
    )
    args = parser.parse_args()

    if torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    # load yolov5x
    yolov5x = torch.hub.load('ultralytics/yolov5', 'yolov5x', pretrained=True)
    yolov5x.to(device)

    # transform
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((384, 288)),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # load hrnet
    hrnet = HRNet(48)
    hrnet.to(device)
    hrnet.eval()
    checkpoint = torch.load('weight/pose_hrnet_w48_384x288.pth', map_location=device)
    hrnet.load_state_dict(checkpoint)

    # generate fight data
    generate_data(data_dir, yolov5x, transform, device, hrnet, args.out)

def generate_data(data_dir, detector, transform, device, pose_model, out):
    data = []
    for filename in os.listdir(data_dir):
        video = Video(os.path.join(data_dir, filename), detector, transform, device, pose_model)
        video.extract_poses()
        generator = PoseSeriesGenerator(video, 10, 7)
        data.extend(generator.generate())
    data = np.asarray(data)

    # get the head by taking the average of five key points on the head (nose, left_eye, right_eye, left_ear, right_ear)
    data[:, :, 4] = np.mean(data[:, :, :5], axis=2)
    data = data[:, :, 4:]

    # min-max normalization
    min = np.min(data[:, :, :, :2], axis=2, keepdims=True)
    max = np.max(data[:, :, :, :2], axis=2, keepdims=True)
    data[:, :, :, :2] = (data[:, :, :, :2] - min) / (max - min)

    # get the origin by taking the average of four key points on the body (left_shoulder, right_shoulder, left_hip, right_hip)
    origin = (np.sum(data[:, :, 1:3, :2], axis=2, keepdims=True) + np.sum(data[:, :, 7:9, :2], axis=2, keepdims=True)) / 4

    # shift the origin
    data[:, :, :, :2] = data[:, :, :, :2] - origin

    # save into file
    np.save(out, data)

if __name__ == '__main__':
    main()