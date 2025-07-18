import yaml
import funcy

load_yaml = funcy.partial(yaml.load, Loader=yaml.Loader)