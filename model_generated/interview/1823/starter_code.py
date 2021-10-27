# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
    self.val = val
    self.next = next
class Solution:
    def reorderList(self, head: ListNode) -> None:
        """
        Do not return anything, modify head in-place instead.
        """
        