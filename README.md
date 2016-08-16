# BasicTagger

This repository provides a basic tagger which identifies strings and lemmas in text and links them to identifiers from a resource.

Current version: 0.1

Dependencies:

KafNafParserPy
Python3

Usage:

python ontology_tagger_on_naf.py input_directory output_directory [list of resources]

Input:

Directory of NAF files with (at least) token and term layer
Output directory
At least one resource file providing strings and identifiers

Output:

NAF files containing all information from input NAF and additional markables; each markable links a string (set of tokens) to an identifier. 

Resource structure:

Resources should be tsv files of the following structure:

surface string (lower case) TAB lemmas of string TAB head word (lower case) TAB lemma of head word TAB identifier

Features Coming up:

Options:
- apply to single file instead of directory
- only string match or only lemma match
- option to set pointer to resource or to retrieve it from the resource itself


For questions contact:

antske.fokkens@vu.nl
