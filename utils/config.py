import toml

def readConfig(path:str = './config.toml') -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return toml.load(f)