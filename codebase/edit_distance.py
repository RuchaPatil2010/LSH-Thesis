from   docx        import Document
from   Levenshtein import editops
from   nltk.corpus import words
from   pathlib     import Path
import math
import os
import random

# Assuming that all the documents have a size less than 2^15
MAX_DOC_SIZE = 25
# Number of strings in the database
NUM_STRINGS = 100
# Number of hash functions used
NUM_HASH_FUNC = 1
# 64 most significat characters in the documents
ACCEPTABLE_CHARS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 
                    'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 
                    'y', 'z', '$']


class HashFamily:
  """Define the hash family based on the underlying function rho
  rho defined here based on the 2/m-universal hashing function.
  Input of rho is an alphabet and the size of hashed string at this moment,
  and the output is a pair of numbers (r1,r2) in the range [0,1)x[0,1).

  We generate the hash as follows:
  1. Convert the alphabet into number using its index in ACCEPTABLE_CHARS.
  2. Downscale the size of hashed string by considering only the rightmost 32 
     bits, we do that by % operator.
  3. Multiply the two numbers obtained above, multiply the result with an odd
     multiplier with 26 bits (so that the total is 64 bits).
  4. Divide the 64 bits number into 2 numbers of 32 bits each.
  5. r1 is obtained by considering the 5 leftmost bits of the right number and
     dividing these with 1024 to get a number in [0,1).
  6. r2 is obtained similarly by considering the rightmost bit of the right 
     number.
  """
  
  def __init__(self, pa=-1, pr=-1):
    if pa == -1 or pr == -1:
      self.pa, self.pr = get_p_values()
    else:
      self.pa = pa
      self.pr = pr
    self.multiplier = random.randint(1, pow(2, 20))
    # multiplier should be odd number
    self.multiplier = 2 * self.multiplier - 1
  
  def hash_str(self, x: str) -> str:
    """We perform the hash function until i<|x| and |s| < 8d/(1-pa)+6log(n)
    where, d is the maximum length of all strings in databases and queries and
           n is the number of strings stored in database.
    Note, for the argument in the paper, we assume the following
    d = O(n) and alphabet size = O(n), although the given database does not 
    satisfy this assumption.
    """
    s = ""
    i = 0
    while (i < len(x) and 
           len(s) < ((8 * MAX_DOC_SIZE)/(1 - self.pa)) 
                      + 6 * math.log(NUM_STRINGS)):
      s, i = self.get_hash(x, i, s)

    # if the string is not completely traversed then the transcript is incomplete
    if i < len(x):
      s = "INCOMPLETE"
    
    return s

  def get_hash(self, x: str, i: int, s: str) -> tuple:
    """Determine the next character in string s
    if r1 < pa, we add ⊥ to s
    if r1 > pa and r2 < pr, we add ⊥ to s and increment i
    if r1 > pa and r2 > pr, we add xi to s and increment i

    Args:
      x: input string
      i: the ith element which we are processing
      s: the output string we have at this point

    Returns:
      A tuple containing the updated string s and the index i
    """
    # Convert xi into int
    try:
      val = ACCEPTABLE_CHARS.index(x[i]) + 1
    except ValueError:
      # Handle value error when the char is not present in ACCEPTABLE_CHARS.
      val = 0
    
    # Product of multiplier, xi and |s|.
    prod = self.multiplier * val * len(s)
    # print(self.multiplier, val, len(s), prod)
    prod = prod % pow(2, 32)

    # Get the values of r1 and r2
    r2 = ((prod % 1024) >> (5)) / 32
    r1 = (prod % 32) / 32
    # print(r1,r2)

    # Determine the value of hashed string based on r1, r2, pa, pr
    if r1 <= self.pa:
      # hash-insert
      s += u"\u22A5"    # ⊥
    elif r2 <= self.pr:
      # hash-replace
      s += u"\u22A5"    # ⊥
      i+=1
    else:
      # hash-match
      s += x[i]
      i+=1

    return (s, i)


def get_p_values() -> tuple:
  """Randomize thevalue of p to get the values of pa and pr

  p <= 1/3
  pa = sqrt(p/(1+p))
  pr = sqrt(p)/(sqrt(1+p)-sqrt(p))

  Returns:
    Tuple of pa and pr
  """
  global P_VALUE 
  P_VALUE = random.uniform(0, 1/3)
  return (math.sqrt(P_VALUE / (1 + P_VALUE)), 
          math.sqrt(P_VALUE) / (math.sqrt(1 + P_VALUE) - math.sqrt(P_VALUE)))


def get_words() -> list:
  """Get a list of the longest words
  """
  word_list = words.words()
  word_list = [i.lower() for i in word_list]
  # Sort the words based on the length of the words
  word_list = sorted(word_list, key=len)

  return word_list[(-1)*NUM_STRINGS:]


def hash_strs(text: list) -> dict:
  """Consider each paragraph of the file as a string, hash the string and store
  the value in a dict with key as the hashed string and value as a list of index
  of the file.

  Args:
    text: list of text in all files

  Returns:
    Dict of list of file index containing the key as hashed_str
  """
  # Define the hash function
  pa, pr = get_p_values()
  rho = HashFamily(pa, pr)

  # Get the hash values
  hash_values = {}
  
  for (i,content) in enumerate(text):
    hashed_str = rho.hash_str(content)

    if hashed_str != "INCOMPLETE":
      if hashed_str in hash_values:
        hash_values[hashed_str].add(i)
      else:
        hash_values[hashed_str] = {i}

  return hash_values


def get_candidate_pairs(text: list) -> set:
  """Traverse through all the files for NUM_HASH_FUNC times and get the pairs
  of documents which might have same paragraphs.
  We hash each paragraph and compare this hashed string for each file, if any
  two files have similar paragraphs, they would form a candidate pairs.
  If two paragraphs hash to the same string means that a path through the edit
  distance graph exists based on the operations we have.

  Args:
    paragraphs: list of all the paragraphs in the files

  Returns:
    set of candidate pairs
  """
  candidate_pairs = set()
  for i in range(0, NUM_HASH_FUNC):
    hash_values = hash_strs(text)
    # Generate candidate pairs for each key
    for value in hash_values.values():
      for k in value:
        for j in value:
          if k < j:
            candidate_pairs.add((k, j))
  
  return candidate_pairs


def get_edit_distance(candidate_pairs: set, word_list: list) -> list:
  """Get the edit distance operations to convert first string into the second
  string in each tuple.

  Args:
    candidate_pairs: pairs of similar words
    word_list: universal list of words

  Returns:
    List of edit operations for each tuple in candidate_pairs
  """
  edit_operations = []
  for (i, j) in candidate_pairs:
    edit_operations.append(editops(word_list[i], word_list[j]))

  return edit_operations


def verify_the_bounds(edit_operations: list, word_list: list):
  """Verify if ED(x,y)<=r then P(hashed_value(x)=hashed_value(y))>=p^r-2/n^2
  and if ED(x,y)>=cr then P(hashed_value(x)=hashed_value(y))<=(2p)^cr

  Args:
    edit_operations: list of edit operations for all the words with same hashed
                     strings
    word_list: all the words in the dictionary we are using
  """
  ED_calculated = {}
  ED_actual = {}
  for i in range(0, 25):
    ED_calculated[i] = 0
    ED_actual[i] = 0

  for i in edit_operations:
    l = len(i)
    ED_calculated[l] += 1
  
  for i in word_list:
    for j in word_list:
      if i < j:
        l = len(editops(i, j))
        ED_actual[l] += 1

  c = 5    
  for r in range(1, 5):
    # For ED < r
    sum_actual = 0
    sum_calculated = 0
    for i in range(0,r+1):
      sum_actual += ED_actual[i]
      sum_calculated += ED_calculated[i]
    
    p = sum_calculated/sum_actual
    if p < pow(P_VALUE, r) - (2 / (NUM_STRINGS * NUM_STRINGS)):
      print(f"Upper bound probability failed for r = {r}")
      print(f"probability of equal hash_strings = {p}")
      print(f"bound = {pow(P_VALUE, r) - (2 / (NUM_STRINGS * NUM_STRINGS))}")

    # For ED > cr
    sum_actual = 0
    sum_calculated = 0
    for i in range(c*r,25):
      sum_actual += ED_actual[i]
      sum_calculated += ED_calculated[i]
    
    p = sum_calculated/sum_actual
    if p > pow(3 * P_VALUE, c * r):
      print(f"Lower bound probability failed for r = {r}")
      print(f"probability of equal hash_strings = {p}")
      print(f"bound = {pow(3 * P_VALUE, c * r)}")

    


def main():
  words = get_words()
  candidate_pairs = get_candidate_pairs(words)
  edit_operations = get_edit_distance(candidate_pairs, words)
  verify_the_bounds(edit_operations, words)

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
    x+= random.choice(ACCEPTABLE_CHARS)

  assert rho.hash_str(x) == rho.hash_str(x)

def test_same_str_len():
  """Check if the length of the hashed str does not exceed 8d/(1-pa) + 6logn
  """
  pa, pr = get_p_values()
  rho = HashFamily(pa, pr)
  l = random.randint(1, 10)
  x = ""
  for i in range(0, l):
    x+= random.choice(ACCEPTABLE_CHARS)

  hashed_str = rho.hash_str(x)

  assert (len(hashed_str) > 0 and 
          len(hashed_str) <= (8 * MAX_DOC_SIZE / (1-pa)) + 
                            (6 * math.log(NUM_STRINGS)))
  
def test_candidate_pairs():
  """Check if the values of candidate pairs are not out of range.
  """
  l = random.randint(1, 15)
  hashed_str = []
  rho = HashFamily()
  for i in range(0, l):
    l_str = random.randint(1, 15)
    x = ""
    for j in range(0, l_str):
      x+= random.choice(ACCEPTABLE_CHARS)
    hashed_str.append(rho.hash_str(x))

  # Check if the values are not out of range
  candidate_pairs = get_candidate_pairs(hashed_str)
  for i,j in candidate_pairs:
    if i < 0 or j < 0 or i>=l or j >= l:
      assert False
    
  assert True

def test_repetitions_candidate_pairs():
  """Check if the candidate pairs have repetitions.
  """
  l = random.randint(1, 15)
  hashed_str = []
  rho = HashFamily()
  for i in range(0, l):
    l_str = random.randint(1, 15)
    x = ""
    for j in range(0, l_str):
      x+= random.choice(ACCEPTABLE_CHARS)
    hashed_str.append(rho.hash_str(x))

  # Check for repetitions
  candidate_pairs = get_candidate_pairs(hashed_str)
  visited_pairs = set()
  for i,j in candidate_pairs:
    if (i,j) in visited_pairs:
      assert False
    visited_pairs.add((i,j))
    visited_pairs.add((j,i))
    
  assert True
 