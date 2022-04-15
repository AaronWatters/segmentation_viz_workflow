from setuptools import setup

url = ""
version = "0.1.0"
readme = open('README.md').read()

setup(
    name="segmentation_viz_workflow",
    packages=["segmentation_viz_workflow"],
    version=version,
    description="Code and documentation about creating microscopy cell segmentation visualizations.",
    long_description=readme,
    include_package_data=True,
    author="Aaron Watters",
    author_email="awatters@flatironinstitute.org",
    url=url,
    install_requires=[
        "numpy", 
        "scipy", 
        ],
    license="MIT"
)
