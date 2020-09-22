from distutils.core import setup

setup(
    name="QuantitationPipeline",
    version="0.1.0",
    packages=[
        "quantify_proteins",
    ],
    scripts=[
        "accession_protein_names.py",
        "app_accessions.py",
        "quantify_group.py",
        "quantify.py",
    ]
)
