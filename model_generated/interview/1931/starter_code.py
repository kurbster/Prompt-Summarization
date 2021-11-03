# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
    self.val = val
    self.next = next
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
    self.val = val
    self.left = left
    self.right = right
class Solution:
    def isSubPath(self, head: ListNode, root: TreeNode) -> bool:
        