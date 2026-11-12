#include <bits/stdc++.h>
using namespace std;
int main(){int n;scanf("%d",&n);long long s=0;for(int i=0;i<n;i++){long long x;scanf("%lld",&x);if(x%2==0)s+=x;}printf("%lld\n",s);}
