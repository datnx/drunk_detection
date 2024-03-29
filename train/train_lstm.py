import sys
sys.path.append('.')
from train.trainer import Trainer
from models.lstm import DatLSTM
from prepare_data.violence_dataset import ViolenceDataset, ViolenceValDataset
import os
import argparse
import numpy as np
from torch.utils.data import DataLoader
import torch.optim as optim
import torch.nn as nn
import torch

def main():

    parser = argparse.ArgumentParser(description='Train a simple LSTM model on the prepared violence dataset')
    parser.add_argument(
        '--fight',
        type=str,
        help='the path to fight data',
        required=True
    )
    parser.add_argument(
        '--non-fight',
        type=str,
        help='the path to non_fight data',
        required=True
    )
    parser.add_argument(
        '--fight-val',
        type=str,
        help='the path to fight val data',
        required=True
    )
    parser.add_argument(
        '--non-fight-val',
        type=str,
        help='the path to non_fight val data',
        required=True
    )
    parser.add_argument(
        '--series-length',
        type=int,
        help='the length of a pose series',
        default=10
    )
    parser.add_argument(
        '--min-poses',
        type=int,
        help='minimum number of poses detected for a series to be considered valid',
        default=7
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        help='batch size',
        default=4
    )
    parser.add_argument(
        '--learning-rate',
        '-lr',
        type=float,
        help='learning rate',
        default=0.0001
    )
    parser.add_argument(
        '--num-epochs',
        type=int,
        help='number of epochs to train',
        default=10
    )
    parser.add_argument(
        '--save-dir',
        type=str,
        help='the folder to save best model in',
        required=True
    )
    args = parser.parse_args()

    # Load LSTM model
    lstm_model = DatLSTM(39, 64, 2, args.series_length)

    # Define an optimizer
    # sgd = optim.SGD(lstm_model.parameters(), args.learning_rate)
    adam = optim.Adam(lstm_model.parameters(), args.learning_rate)

    # Define a loss function
    # bce = nn.BCELoss()
    ce = nn.CrossEntropyLoss()

    # Load data
    dataset = ViolenceDataset(args.fight, args.non_fight, args.series_length, args.min_poses)
    val_dataset = ViolenceValDataset(args.fight_val, args.non_fight_val, args.series_length, args.min_poses)

    # Create dataloader
    train_loader = DataLoader(dataset, args.batch_size, shuffle=True)
    valid_loader = DataLoader(val_dataset, args.batch_size, shuffle=False)

    # Create save dir
    if not os.path.exists(args.save_dir):
        os.makedirs(args.save_dir)

    # Create a Trainer
    trainer = Trainer(lstm_model, train_loader, valid_loader, args.num_epochs, adam, ce)

    # Train
    trainer.train(args.save_dir)

if __name__ == '__main__':
    main()