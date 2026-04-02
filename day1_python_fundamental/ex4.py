""" 
Leetcode 20 : Valid Parentheses
Example 1:

Input: s = "()"

Output: true

Example 2:

Input: s = "()[]{}"

Output: true

Example 3:

Input: s = "(]"

Output: false

Example 4:

Input: s = "([])"

Output: true

Example 5:

Input: s = "([)]"

Output: false
"""

class Solution:
    def isValid(self, s: str) -> bool:
        mapping = {
            "(": 1,
            ")": -1,
            "[": 2,
            "]": -2,
            "{": 3,
            "}": -3,
        }

        total = sum(mapping.get(ch, 0) for ch in s)
        return total == 0
    
lab4 = Solution()
print(lab4.isValid("([{])")) # False 