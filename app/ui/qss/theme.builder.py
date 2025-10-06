# Wrapper to keep naming convention while delegating to theme_builder module.
from .theme_builder import generate

if __name__ == "__main__":
    generate("minimal")
