import setuptools

setuptools.setup(
    name="bakestimator",
    version="0.4",
    author="Igor Tkach",
    author_email="itkach@gmail.com",
    description="Utility to calculate estimated baking rewards and required deposits on Tezos",
    keywords="tezos baking reward deposit endorsement block",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=["requests", "scipy"],
    entry_points={
        "console_scripts": [
            "bakestimator=bakestimator.cli:main",
        ],
    },
)
