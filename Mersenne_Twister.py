
# This file generates the random port numbers, which are so integral to our protocol.
# These numbers will be generated given that the server and client have the same seed.

MT_RAND_MAX = 2**32 -1

def IntegerRangeGenerator(seed,min,max):
   """Generates a stream of random integers in a range"""
   rng = MersenneTwister32(seed)
   range = 1 + max - min
   bins = MT_RAND_MAX / range
   limit = bins * range
   while True:
      randint = rng.next()
      while (randint >= limit):
         randint = rng.next()
      print min + (randint / bins),
      yield min + (randint / bins) 

def MersenneTwister32(seed):
   """32-bit Merseene Twister 19937 - Generator"""

   #Algorithm Parameters
   a = 0x9908B0DF
   u = 11
   d = 0xFFFFFFFF
   s = 7
   b = 0x9D2C5680
   t = 15
   c = 0xEFC60000
   L = 18
   w = 32
   n = 624
   m = 397
   r = 31
   f = 1812433253
   ms_bit = 0x80000000
   ls_bits = 0x7FFFFFFF
   mask_32 = 0xFFFFFFFF
   
   index = n
   state = [ 0 for i in range(n)]

   state[0] = seed

   for i in range(1,n):
      state[i] = mask_32 & (f * (state[i-1]^(state[i-1] >> (w-2))) + i)

   while(True):
      if index >= n:
         #Twist
         for i in range(n):
            y = mask_32 & ((state[i] & ms_bit) + (state[(i+1)%n] & ls_bits))
            state[i] = state[(i+m)%n]^y >> 1
            if y%2 != 0:
               state[i] = state[i]^a
         index = 0
      y = state[index]
      y = y ^ ((y >> u) & d)
      y = y ^ ((y << s) & b)
      y = y ^ ((y << t) & c)
      y = y ^ (y >> L)
      index += 1

      yield (mask_32 & y)
   

if __name__ == '__main__':
   a = MersenneTwister32(123)
   for i in range(5):
      print(a.next())
   a = IntegerRangeGenerator(123,100,110)
   for i in range(20):
      print(a.next())
