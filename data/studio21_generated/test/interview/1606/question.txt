Little Chris is a huge fan of linear algebra. This time he has been given a homework about the unusual square of a square matrix.

The dot product of two integer number vectors x and y of size n is the sum of the products of the corresponding components of the vectors. The unusual square of an n × n square matrix A is defined as the sum of n dot products. The i-th of them is the dot product of the i-th row vector and the i-th column vector in the matrix A.

Fortunately for Chris, he has to work only in GF(2)! This means that all operations (addition, multiplication) are calculated modulo 2. In fact, the matrix A is binary: each element of A is either 0 or 1. For example, consider the following matrix A: $\left(\begin{array}{l l l}{1} & {1} & {1} \\{0} & {1} & {1} \\{1} & {0} & {0} \end{array} \right)$ 

The unusual square of A is equal to (1·1 + 1·0 + 1·1) + (0·1 + 1·1 + 1·0) + (1·1 + 0·1 + 0·0) = 0 + 1 + 1 = 0.

However, there is much more to the homework. Chris has to process q queries; each query can be one of the following:   given a row index i, flip all the values in the i-th row in A;  given a column index i, flip all the values in the i-th column in A;  find the unusual square of A. 

To flip a bit value w means to change it to 1 - w, i.e., 1 changes to 0 and 0 changes to 1.

Given the initial matrix A, output the answers for each query of the third type! Can you solve Chris's homework?


-----Input-----

The first line of input contains an integer n (1 ≤ n ≤ 1000), the number of rows and the number of columns in the matrix A. The next n lines describe the matrix: the i-th line contains n space-separated bits and describes the i-th row of A. The j-th number of the i-th line a_{ij} (0 ≤ a_{ij} ≤ 1) is the element on the intersection of the i-th row and the j-th column of A.

The next line of input contains an integer q (1 ≤ q ≤ 10^6), the number of queries. Each of the next q lines describes a single query, which can be one of the following:   1 i — flip the values of the i-th row;  2 i — flip the values of the i-th column;  3 — output the unusual square of A. 

Note: since the size of the input and output could be very large, don't use slow output techniques in your language. For example, do not use input and output streams (cin, cout) in C++.


-----Output-----

Let the number of the 3rd type queries in the input be m. Output a single string s of length m, where the i-th symbol of s is the value of the unusual square of A for the i-th query of the 3rd type as it appears in the input.


-----Examples-----
Input
3
1 1 1
0 1 1
1 0 0
12
3
2 3
3
2 2
2 2
1 3
3
3
1 2
2 1
1 1
3

Output
01001