from yaml import safe_load


def load_yaml(filepath="/home/jj/workspace/config/config.yaml"):
    """ function to load config from yaml 
    """
    with open(filepath, 'r', encoding = 'utf-8') as stream:
        try:
            data = safe_load(stream)
        except Exception as e:
            print(e)
            data = None
    return data
