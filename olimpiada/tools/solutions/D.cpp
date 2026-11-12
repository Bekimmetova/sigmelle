#include <bits/stdc++.h>
using namespace std;
int main(){int n;scanf("%d",&n);long long best=LLONG_MIN,cur=0;for(int i=0;i<n;i++){long long x;scanf("%lld",&x);cur=(i==0)?x:max(x,cur+x);best=max(best,cur);}printf("%lld\n",best);}
