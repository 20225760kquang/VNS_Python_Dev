"""
Leetcode 125 : Valid palindrome 

Example 1:

Input: s = "A man, a plan, a canal: Panama"
Output: true
Explanation: "amanaplanacanalpanama" is a palindrome.
Example 2:

Input: s = "race a car"
Output: false
Explanation: "raceacar" is not a palindrome.
Example 3:

Input: s = " "
Output: true
Explanation: s is an empty string "" after removing non-alphanumeric characters.
Since an empty string reads the same forward and backward, it is a palindrome.
"""
import re 

class Solution:
    def isPalindrome(self,s: str) -> bool:
       s = self.convert(s)
       
       # Trường hợp empty string
       if not s : 
           return True 
       left = 0 
       right = len(s) - 1  
       
       while left <= right : 
           if s[left] == s[right] : 
               left += 1
               right -= 1 
           else : return False
     
       return True 
       

    @staticmethod
    def convert(s:str) -> str: 
        # Xóa khoảng trắng thừa 
        s = "".join(s.split())
        # Lowercase 
        s = s.lower()
        # Chỉ giữ lại kí tự chữ 
        s = re.sub(r'[^\w\s]','',s)
        return s 

lab1 = Solution()
print(lab1.isPalindrome("A man, a plan, a canal: Panama"))

