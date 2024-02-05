from types import SimpleNamespace

def parse(d):
    """
    Convert nested dict to nested namespace
    """
    x = SimpleNamespace()
    _ = [setattr(x, k, parse(v)) if isinstance(v, dict) else setattr(x, k, v)
            for k, v in d.items() ]
    return x

def unparse(n):
    """
    Convert nested namespace to nested dict
    """
    return { k: unparse(v) if isinstance(v, SimpleNamespace) else v
            for k,v in vars(n).items() }

def unwrap_resolution(resolution: SimpleNamespace):
    """
    Convert resolution namespace to tuple of height and width
    """
    return (resolution.width, resolution.height)

def unwrap_hsv(hsv: SimpleNamespace):
    """
    Convert HSV namespace to numpy array for OpenCV
    """
    return { 'hue': int(hsv.hue), 'saturation': int(hsv.saturation), 'value': int(hsv.value) }
