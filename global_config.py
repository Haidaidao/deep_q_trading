import json 

config = json.load(open('config.json', 'r'))

numFile = config['num_files']
MK = config['MK']
ensembleFolder = config['ensemble_folder']
label_threshold = config['label_threshold']
epoch = config['epoch']