from batch_config import load_config

config = load_config('../config/batch_config.json')
print('Config loaded')
print('Destination mappings:', config.get('destination_mappings', {}))
print('Test matching:')
for key, value in config.get('destination_mappings', {}).items():
    print(f'  {key} -> {value}')