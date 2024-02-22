# -*- coding: utf-8 -*-
"""LSH

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lVT-5m-gL_7auwaOUBenQF-lkXN7sLc7
"""
from   docx    import Document
from   pathlib import Path
import math
import os
import random

DATA_FOLDER = Path("./dataset/")
HASH_FUNC_COUNT = 20
BAND_SIZE = 5
BIT_SPACE = 32
SHINGLE_SIZE = 5   # 5-shingles
NUM_SIGNATURES_LOG = 16  #final_bits
# 64 most significat characters in the documents
ACCEPTABLE_CHARS = ['\\', '!', '"', '#', '$', '&', "'", '(', ')', '*', '+', ',', 
                    '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', 
                    '9', ':', ';', '=', '?', '@', '[', ' ', ']', '^', '_', 'a',
                    'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 
                    'z', '~', '·', '–']


class UniversalHash:
  """Class define inf functions from the 2/m hash family
  """

  def __init__(self, bit_space, range_space):
    self.h_range = pow(2, range_space)
    self.width = bit_space - range_space
    self.multiplier = random.randint(1, bit_space/2 - 1)
    self.multiplier = (2*self.multiplier + 1) % self.h_range

  def get_value(self, num):
    return int((num * self.multiplier) % self.h_range) >> self.width


def get_files() -> list:
  """Get all the files from the dataset folder

  Returns:
    list: os paths of all the dataset files
  """
  files = []
  for entry in os.listdir(DATA_FOLDER):
    if os.path.isfile(os.path.join(DATA_FOLDER, entry)):
        files.append(os.path.join(DATA_FOLDER, entry))
  
  return files


def preprocess_shingles(shingle: str) -> int:
  """Convert string into number for easy calculation.

  Args:
    shingle: strings of SHINGLE_SIZE (k-shingles)

  Returns:
    Integer equivalent of the shingle. This could be visualised a the index of 
    the shingle
  """
  val = 0
  for i in shingle:
    try:
      val = (val * len(ACCEPTABLE_CHARS)) + ACCEPTABLE_CHARS.index(i)
    except ValueError:
      # Handle value error when the char is not present in ACCEPTABLE_CHARS.
      val = (val * len(ACCEPTABLE_CHARS))

  return val


def hash_LSH(data, hash_func):
  """We hash the values for each band and return the buckets
  """
  ret = set()
  for i in data:
    ret.add(hash_func.get_value(i))

  return ret

def get_shingles(files):
  """
  This will return shingles table in the form of list of sets
  Where each index in the list would correspond to the document and the set
  would denote if the minhash of each shingle is present in the document.
  Example: shingles = [{1, 3, 6}, {2, 4, 16, 25, 36}, ...]
  """
  # List of shingles in respective files
  shingles = []

  for f in files:
    # extract content from files
    content = [p.text.lower() for p in Document(f).paragraphs]
    content = "\n".join(content)

    current_shingle = ""
    all_shingles = set()

    # Add all the shingles in set
    for char in content:
      current_shingle += char
      if len(current_shingle) > SHINGLE_SIZE:
        # If the shingle is longer we trim it
        current_shingle = current_shingle[1:]
        all_shingles.add(preprocess_shingles(current_shingle))
      elif len(current_shingle) == SHINGLE_SIZE :
        all_shingles.add(preprocess_shingles(current_shingle))

    shingles.append(all_shingles)
  return shingles


def create_signature_matrix(data : list) -> list:
  """Create the minHash Signatures using hash functions
  Algorithm followed in the function:
  1. Initialise the signature matrix to infinity
  2. Traverse the sparse matrix. As we have a set of the shingles present, we do
     this by traversing through all the shingles' indices and if the given
     shingle is present in the set, we consider it true, else false.
  3. If the shingle is present we replace the value in signature matrix 
     corresponding to the given document with the minimum of current value or
     the result of the hash function.

  We use hash functions here as for a universal hash function, the frequency of
  h(x1) = h(x2) where x1 != x2 is 1/m where m is the range of the hash function.
  But, if the domain = range of the function, then the value of hash is ideally
  the permutation of the values. Hence, instead of permuting, we apply hash to
  the indices.

  Args:
    data: List of set of indices of all the shingles present in the respective 
          document
  
  Returns:
    Signature matrix, a 2D matrix of num_of_docs * num_of_hash_functions 
    containing the minHash signatures of the documents w.r.t each of the hash
    function
  """
  # Initialise signatures to infinity
  signature = [[float('inf') for j in range(0, HASH_FUNC_COUNT)] for i in data]

  # Bits needed to store values in signature matrix
  signature_bits = math.ceil(
                    math.log(
                      pow(len(ACCEPTABLE_CHARS), SHINGLE_SIZE), 
                      2))

  # Initialise the hash functions which simulates the generation of minHash 
  # signatures
  hash_funcs = [UniversalHash(BIT_SPACE, signature_bits)
                for i in range(0, HASH_FUNC_COUNT)]

  # Hash all the values in sparse matrix and store the minimum value
  for index, d in enumerate(data):
    for i in d:
      for j in range(0, HASH_FUNC_COUNT):
        # For every hash function, we modify the signature value
        signature[index][j] = min(signature[index][j],
                                  hash_funcs[j].get_value(i))

  return signature

def get_candidate_pair(matrix : list) -> set:
  """Hash bands in signature matrix and create candidate pairs on collision.

  Args:
    matrix: signature matrix

  Returns:
    List of candidate pairs
  """
  candidate_pairs = set()

  for i in range(0, int(HASH_FUNC_COUNT/BAND_SIZE)):
    hash_values = []

    # Change the hash function for every band
    hash_func = UniversalHash(BIT_SPACE, NUM_SIGNATURES_LOG)

    # Get the buckets for every band
    for index, d in enumerate(matrix):
      hash_values.append(hash_LSH(d[i*BAND_SIZE:(i+1)*BAND_SIZE], hash_func))

    # Compare the buckets with each other to get pairs
    for ind_i, i in enumerate(hash_values):
      for ind_j, j in enumerate(hash_values):
        # Check for equal pairs
        if i == j and ind_i < ind_j:
          candidate_pairs.add((ind_i, ind_j))

  return candidate_pairs

def main():
  files = get_files()
  shingles = get_shingles(files)
  matrix = create_signature_matrix(shingles)
  candidate_pairs = get_candidate_pair(matrix)
  print(candidate_pairs)

if __name__ == "__main__":
  main()