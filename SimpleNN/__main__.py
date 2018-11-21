import argparse
import torch

import numpy as np
from SimpleNN.model import SimpleNN
from SimpleNN.data import CriteoDataset, BatchIterator


def run_test_set(model, test_set):
    model.eval()
    with torch.no_grad():
        R = []
        C = []

        for sample, click, propensity in BatchIterator(test_set, 1):
            output = model(sample)

            # Calculate R
            if click == 0.999:
                o = 1.0
            else:
                o = float(np.random.choice([0, 10], p=[0.9, 0.1]))
            R.append(click * (output[:, 0, 0] / propensity) * o)

            # Calculate C
            if click == 0.999:
                o = 1
            else:
                o = float(np.random.choice([0, 10], p=[0.9, 0.1]))
            C.append((output[:, 0, 0] / propensity) * o)

        R = np.average(R) * 10**4
        C = np.average(C)
        R_div_C = R / C

        print("\nTest results:")
        print("R x 10^4: {}\t C: {}\t (R x 10^4) / C: {}\n".format(R, C, R_div_C))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--train', default='../data/vw_compressed_train')
    parser.add_argument('--test', default='../data/vw_compressed_test')
    parser.add_argument('--lamb', type=float, default=0.5)
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--stop_idx', type=int, default=50000)
    parser.add_argument('--embedding_dim', type=int, default=20)
    parser.add_argument('--hidden_dim', type=int, default=100)
    parser.add_argument('--feature_dict', type=str, default='../data/features_to_keys.json')
    args = parser.parse_args()
    train_set = CriteoDataset(args.train, args.feature_dict, args.stop_idx)
    test_set = CriteoDataset(args.test, args.feature_dict, args.stop_idx)
    model = SimpleNN(args.embedding_dim, args.hidden_dim, train_set.feature_dict)
    optimizer = torch.optim.Adam(model.parameters())

    epoch_losses = []
    for i in range(args.epochs):
        print("Starting epoch {}".format(i))
        losses = []
        for sample, click, propensity in BatchIterator(train_set, args.batch_size):
            optimizer.zero_grad()
            output = model(sample)
            loss = (click - args.lamb) * (output[:, 0, 0] / propensity)
            loss = torch.sum(loss)
            losses.append(loss.item())
            loss.backward()
            optimizer.step()
        epoch_losses.append(sum(losses) / len(losses))
        print("Finished epoch {}, avg. loss {}".format(i, epoch_losses[-1]))

        run_test_set(model, test_set)