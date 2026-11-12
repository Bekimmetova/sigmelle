#include <bits/stdc++.h>
using namespace std;
int main(){int n;scanf("%d",&n);vector<int>a(n);for(auto&x:a)scanf("%d",&x);sort(a.begin(),a.end());int q;scanf("%d",&q);
while(q--){int x;scanf("%d",&x);printf("%d\n",(int)(upper_bound(a.begin(),a.end(),x)-a.begin()));}}
