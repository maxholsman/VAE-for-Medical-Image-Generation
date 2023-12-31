import os
import yaml
import argparse
import numpy as np
from pathlib import Path
from models import *
from models import vanilla_vae
from models import mssim_vae
from experiment import VAEXperiment
import torch.backends.cudnn as cudnn
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning import seed_everything
from pytorch_lightning.callbacks import LearningRateMonitor, ModelCheckpoint
from dataset import VAEDataset
from pytorch_lightning.strategies import DDPStrategy

#Change these config parameters accordingly
config = {
    'VanillaVAE': {
        'model_params': {
            'name': 'VanillaVAE',
            'in_channels': 3,
            'latent_dim': 128
        },
        'data_params': {
            'data_path': "Data/",
            'train_batch_size': 64,
            'val_batch_size':  64,
            'patch_size': 64,
            'data_name': 'prostategleason',
            'num_workers': 4,
        },
        'exp_params': {
            'LR': 0.005,
            'weight_decay': 0.0,
            'scheduler_gamma': 0.95,
            'kld_weight': 0.00025,
            'manual_seed': 1265
        },
        'trainer_params': {
            'max_epochs': 100
        },
        'logging_params': {
            'save_dir': "logs/",
            'name': "VanillaVAE"      
        }

    },
    'MSSIMVAE': {
        'model_params': {
            'name': 'MSSIMVAE',
            'in_channels': 3,
            'latent_dim': 128
        },
        'data_params': {
            'data_path': "Data/",
            'train_batch_size': 64,
            'val_batch_size':  64,
            'patch_size': 64,
            'data_name': 'prostategleason',
            'num_workers': 4,
        },
        'exp_params': {
            'LR': 0.005,
            'weight_decay': 0.0,
            'scheduler_gamma': 0.95,
            'kld_weight': 0.00025,
            'manual_seed': 1265
        },
        'trainer_params': {
            'max_epochs': 10
        },
        'logging_params': {
            'save_dir': "logs/",
            'name': "MSSIMVAE"      
        }
        }
    }

models = {
    'VanillaVAE': vanilla_vae.VanillaVAE,
    'MSSIMVAE': mssim_vae.MSSIMVAE
}

#CHANGE MODEL TYPE HERE
MODEL = 'VanillaVAE'

# Initializing logger
tb_logger =  TensorBoardLogger(save_dir=config[MODEL]['logging_params']['save_dir'],
                               name=config[MODEL]['model_params']['name'],)

# For reproducibility
seed_everything(config[MODEL]['exp_params']['manual_seed'], True)

model = models[config[MODEL]['model_params']['name']](**config[MODEL]['model_params'])
experiment = VAEXperiment(model,
                          config[MODEL]['exp_params'])

# Setting up PyTorch Lightning Datamodule object
data = VAEDataset(**config[MODEL]["data_params"], pin_memory=True)

data.setup()

# Initializing trainer object
runner = Trainer(logger=tb_logger,
                 callbacks=[
                     LearningRateMonitor(),
                     ModelCheckpoint(save_top_k=2,
                                     dirpath =os.path.join(tb_logger.log_dir , "checkpoints"),
                                     monitor= "val_loss",
                                     save_last= True),
                 ],
                 strategy='ddp_notebook',
                 **config[MODEL]['trainer_params'])


# Samples and reconstructions logged to Google Drive
Path(f"{tb_logger.log_dir}/Samples").mkdir(exist_ok=True, parents=True)
Path(f"{tb_logger.log_dir}/Reconstructions").mkdir(exist_ok=True, parents=True)

# Fitting trainer object
print(f"======= Training {config[MODEL]['model_params']['name']} =======")
runner.fit(experiment, data)


