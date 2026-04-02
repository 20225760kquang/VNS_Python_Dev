"""
Leetcode 442 : Find All Duplicates in Array

Example 1:

Input: nums = [4,3,2,7,8,2,3,1]
Output: [2,3]
Example 2:

Input: nums = [1,1,2]
Output: [1]
Example 3:

Input: nums = [1]
Output: []
"""
from typing import List 

class Solution:
    def findDuplicates(self, nums: List[int]) -> List[int]:
       
        to_dict = {x: nums.count(x) for x in set(nums)}

        return [x for x, count in to_dict.items() if count > 1]
    
    
lab2 = Solution()
result = lab2.findDuplicates([4,3,2,7,8,2,3,1])
print(result) # [2,3]