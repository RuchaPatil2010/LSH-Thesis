"""
Contains the Hash Family class where we define the hash family(rho) based on 
McCauley.
"""
import math
import random

# Assuming that all the documents have a size less than 100
MAX_STRING_SIZE = 100 
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


class HashFamily:
  """Define the hash family based on the underlying function rho which takes a 
  tuple of alphabet and length as parameters and returns 2 random numbers r1 and 
  r2 in [0,1).
  """
  
  def __init__(self, 
               pa: float=-1, 
               pr: float=-1, 
               str_len: int=MAX_STRING_SIZE, 
               num_strings: int=NUM_STRINGS,
               alphabet: list=ACCEPTABLE_CHARS):
    """Initialise the class
    Args:
        pa:          value of pa referred in the paper
        pr:          value of pr referred in the paper
        str_len:     length of the longest string in database
        num_strings: number of strings in database
        alphabet:    list of all the alphabet in the database
    """
    if pa == -1 or pr == -1:
      self.pa, self.pr = get_p_values()
    else:
      self.pa = pa
      self.pr = pr

    self.alphabet = alphabet
    self.max_len = ((8 * str_len)/(1 - self.pa)) + 6 * math.log(num_strings)
    self.rho = self.generate_rho()
  
  def hash_str(self, x: str) -> str:
    """We perform the hash function until i < |x| and |s| < 8d/(1-pa)+6log(n)
    where, d is the maximum length of all strings in databases and queries and
           n is the number of strings stored in database.
    Note, for the argument in the paper, we assume the following
    d = O(n) and alphabet size = O(n).

    Args:
      x: input string

    Returns:
      The hash value of the string: h{rho}(x).
    """
    s = ""
    i = 0
    while i < len(x) and len(s) < self.max_len:
      s, i = self.get_hash(x, i, s)

    # if the string is not completely traversed then the transcript is incomplete
    if i < len(x):
      s = "NOT-COMPLETE"
    
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
    
    r1,r2 = self.rho[(x[i],len(s))]

    # Determine the value of hashed string based on r1, r2, pa, pr
    if r1 <= self.pa:
      # hash-insert
      s += u"\u22A5"    # ⊥
    elif r2 <= self.pr:
      # hash-replace
      s += u"\u22A5"    # ⊥
      i += 1
    else:
      # hash-match
      s += x[i]
      i += 1

    return (s, i)
  
  def generate_rho(self) -> dict:
    """Generate a rho function which rakes the value of the alphabet and current
    size of output string and returns 2 numbers (r1, r2) which are chosen 
    randomly from [0,1).
    
    Returns:
      Dictionary with key as a tuple of (xi,|s|) and value as a tuple of two 
      random numbers (r1,r2) from 0 to 1.
    """
    rho = {}
    for x in self.alphabet:
      for i in range(0,math.ceil(self.max_len)):
        rho[(x,i)]=(random.uniform(0, 1), random.uniform(0, 1))

    return rho


def get_p_values(p: float=P_VALUE) -> tuple:
  """Randomize thevalue of p to get the values of pa and pr

  p <= 1/3
  pa = sqrt(p/(1+p))
  pr = sqrt(p)/(sqrt(1+p)-sqrt(p))

  Args:
    p: the value of p referred in the paper.

  Returns:
    Tuple of pa and pr
  """ 
  return (math.sqrt(p / (1 + p)), 
          math.sqrt(p) / (math.sqrt(1 + p) - math.sqrt(p)))
