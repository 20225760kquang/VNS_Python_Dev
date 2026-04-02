""" 
Leetcode 268 : Missing Numbers 
Example 1:

Input: nums = [3,0,1]

Output: 2

Explanation:

n = 3 since there are 3 numbers, so all numbers are in the range [0,3]. 2 is the missing number in the range since it does not appear in nums.

Example 3:

Input: nums = [9,6,4,2,3,5,7,0,1]

Output: 8

Explanation:

n = 9 since there are 9 numbers, so all numbers are in the range [0,9]. 8 is the missing number in the range since it does not appear in nums.
"""
from typing import List 
class Solution:
    def missingNumber(self, nums: List[int]) -> int:
        
        length = len(nums)
        for x in range(0,length+1):
            if x not in nums : 
                return x 
    
lab3 = Solution()
result = lab3.missingNumber([9,6,4,2,3,5,7,0,1])
print(result) # 8