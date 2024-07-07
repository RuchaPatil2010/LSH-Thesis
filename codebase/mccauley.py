from   hash_family import HashFamily, get_p_values
from   nltk.corpus import words
from   Levenshtein import editops
from   pathlib     import Path
import math
import os
import random

# Assuming that all the documents have a size less than 2^15
MAX_STRING_SIZE = 25
# Number of strings in the database
NUM_STRINGS = 100
# 64 most significat characters in the documents
ACCEPTABLE_CHARS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 
                    'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 
                    'y', 'z', '$']
# The value of probability constant p.
P_VALUE = random.uniform(0, 1/8)
# If ED(x,y)=r then we need to find z s.t. ED(x,z)<=cr
R_VALUE = 2
C_VALUE = 10
# Number of hash functions used = O(1/p1), where p1=p^r-2/n^2
NUM_HASH_FUNC = math.ceil(1/P_VALUE**R_VALUE - (2/NUM_STRINGS**2))


def get_words() -> list:
  """Get a list of the longest words
  """
  word_list = get_all_words()
  return word_list[(-1)*NUM_STRINGS:]


def get_random_word() -> str:
  """Get a random word from the dictionary.
  """
  return random.choice(get_all_words()[(-4)*NUM_STRINGS:])


def get_all_words() -> list:
  """Get a list of all the words in dictionary in sorted order based on length.
  """
  word_list = words.words()
  word_list = [i.lower() for i in word_list]
  # Sort the words based on the length of the words
  word_list = sorted(word_list, key=len)

  return word_list


def hash_strs(words: list) -> dict:
  """Hash all the strings in the list based on the hash function.

  Args:
    text: list of strings

  Returns:
    Dict of list of file index containing the key as hashed_str and
    an object of the HashFamily class
  """
  # Define the hash function
  pa, pr = get_p_values()
  rho = HashFamily(pa, pr)

  # Get the hash values
  hash_values = {}
  
  for string in words:
    hashed_str = rho.hash_str(string)

    # We consider the string only if its transcript is complete.
    if hashed_str != "NOT-COMPLETE":
      if hashed_str in hash_values:
        hash_values[hashed_str].add(string)
      else:
        hash_values[hashed_str] = {string}

  return (hash_values, rho)


def get_hash_values(words: list, hash_func: int=NUM_HASH_FUNC) -> set:
  """Traverse through all the words for NUM_HASH_FUNC times and generate a 
  dictionary used to compare the queries later.

  Args:
    words: list of all the words
    hash_func: number of hash functions used

  Returns:
    Dictionary of hash function and the hash values.
  """
  # Dictionary with keys as the hash function rho and value as the buckets.
  hash={}
  for i in range(0, hash_func):
    hash_values, rho = hash_strs(words)
    hash[rho] = hash_values
  
  return hash


def process_query(query: str, hash: dict) -> list:
  """Hash the query based on all the hash functions rho and return the words 
  which match to the same bucket as the query.

  Args:
    query: the query string which we compare to all the words
    hash: the dictionary of all the hash_functions and corresponding buckets

  Returns:
    A list of all the words which have similar hash as the query, which inturn
    means that the edit distance is less.
  """
  similar_words = set()
  for rho in hash:
    bucket = rho.hash_str(query)
    if bucket in hash[rho]:
      for j in hash[rho][bucket]:
        similar_words.add(j)

  return similar_words


def main():
  words = get_words()
  hash = get_hash_values(words)
  query = get_random_word()
  similar_words = process_query(query, hash)
  print(f"Words similar to {query} are: \n{similar_words}")


if __name__ == "__main__":
  main()

def test_pa_values():
  """Check if the pa values lie in (0,1/2]
  """
  pa, pr = get_p_values()
  assert pa <= 0.5 and pa > 0
  
def test_pr_values():
  """Check if the pr values lie in (0,1]
  """
  pa, pr = get_p_values()
  assert pr <= 1 and pr > 0

def test_same_str_hash():
  """Check if the hash value for a string is same if we use the same underlying 
  function.
  """
  rho = HashFamily()
  l = random.randint(1,10)
  x = ""
  for i in range(0,l):
    x += random.choice(ACCEPTABLE_CHARS)

  assert rho.hash_str(x) == rho.hash_str(x)

def test_str_len():
  """Check if the length of the hashed str does not exceed 8d/(1-pa) + 6logn
  """
  pa, pr = get_p_values()
  rho = HashFamily(pa, pr)
  l = random.randint(1, 10)
  x = ""
  for i in range(0, l):
    x += random.choice(ACCEPTABLE_CHARS)

  hashed_str = rho.hash_str(x)

  assert (len(hashed_str) > 0 and 
          len(hashed_str) <= (8 * MAX_STRING_SIZE / (1-pa)) + 
                            (6 * math.log(NUM_STRINGS)))
  
def test_same_string():
  """Test that a string in the wordlist atleast hashes to itself.
  """
  word_list = get_words()
  hash = get_hash_values(word_list, 1)
  similar = process_query(random.choice(word_list), hash)
  assert len(similar) > 0
 