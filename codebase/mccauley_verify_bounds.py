from   hash_family import HashFamily, get_p_values
from   Levenshtein import editops
import math
import random

# Concatenating the strings to 100 alphabets.
MAX_STRING_SIZE = 100 
# Number of strings in the database
NUM_STRINGS = 1682
# All the alphabet in dataset.
ACCEPTABLE_CHARS = ['A', 'T', 'C', 'G', '$']
# The value of probability constant p.
P_VALUE = random.uniform(0, 1/3)
# Number of hash functions.
NUM_HASH_FUNC=1000


def get_dataset():
  f = open('./utils/dataset.txt','r')
  seq = []
  for x in f:
    seq.append(x.split('\t')[0][:100]+'$')
  return seq


def hash_strs(words: list) -> dict:
  """Hash all the strings in the list based on the hash function.

  Args:
    text: list of strings

  Returns:
    Dict of list of file index containing the key as hashed_str and
    an object of the HashFamily class
  """
  # Define the hash function
  pa, pr = get_p_values(P_VALUE)
  rho = HashFamily(pa, 
                   pr, 
                   str_len=MAX_STRING_SIZE, 
                   num_strings=NUM_STRINGS,
                   alphabet=ACCEPTABLE_CHARS)

  # Get the hash values
  hash_values = {}
  
  for string in words:
    hashed_str = rho.hash_str(string)

    # We consider the string only if its transcript is complete.
    if hashed_str != "NOT-COMPLETE":
      if hashed_str in hash_values:
        hash_values[hashed_str].append(string)
      else:
        hash_values[hashed_str] = [string]

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
  for _ in range(0, hash_func):
    hash_values, rho = hash_strs(words)
    hash[rho] = hash_values
  
  return hash


def edit_distance(words):
  """Return the edit distance operations of the two strings.
  """
  ed = editops(words[0], words[1])
  return ed


def get_probabilities(words: list):
  """Get hash values for the words in the list and print the probability of them
  being equal.

  Args:
    words: List of 2 words.
  """
  ed = edit_distance(words)
  hash = get_hash_values(words)

  # Get the count of hash functions which hashed both the strings together.  
  similar = 0
  for h in hash.values():
    if len(h.keys())==1 and len(list(h.values())[0])==2:
      similar += 1

  # Calculate Probability, upper bound and lower bound.
  prob = similar/NUM_HASH_FUNC
  upper = P_VALUE**(len(ed))
  lower = (P_VALUE**(len(ed)))-(2/(NUM_STRINGS**2))

  # Print all the values.  
  print(f"value of p={P_VALUE}, and r={len(ed)}")
  print(f"Probability of h(x)=h(y) is: {prob}")
  print(f"p^r={upper}")
  print(f"p^r-2/n^2={lower}")
  print(f"Is probability in bounds?: {prob<=upper and prob>=lower}")


def main():
  seq = get_dataset()
  num_runs = 100

  print("For strings with lower edit distance:")
  for _ in range(0, num_runs):
    word = random.choice(seq)
    word2 = word
    diff = math.ceil(random.random()*10)
    for i in range(0, diff):
      r = math.floor(random.random()*len(word2))
      word2 = word2[:i] + word2[i+1:]
    words = [word, word2]
    get_probabilities(words)

  print("For strings with higher edit distance:")
  for _ in range(0, num_runs):
    words = random.sample(seq, 2)
    get_probabilities(words)
  


if __name__ == "__main__":
  main()
