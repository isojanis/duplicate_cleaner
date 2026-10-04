"""Include the shared UI in wheels without duplicating editable source assets."""
from pathlib import Path
from shutil import copytree

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithAssets(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
        target = Path(self.build_lib) / "duplicate_cleaner" / "resources"
        copytree(root / "qml", target / "qml", dirs_exist_ok=True)
        copytree(root / "packaging" / "assets", target / "assets", dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildWithAssets})
