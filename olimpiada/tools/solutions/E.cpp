#include <bits/stdc++.h>
using namespace std;
const long long MOD=1e9+7;
int main(){int n,k;scanf("%d %d",&n,&k);vector<char>b(n+1,0);for(int i=0;i<k;i++){int x;scanf("%d",&x);b[x]=1;}
vector<long long>dp(n+1,0);dp[0]=1;for(int i=1;i<=n;i++){if(b[i])continue;long long v=dp[i-1];if(i>=2)v+=dp[i-2];if(i>=3)v+=dp[i-3];dp[i]=v%MOD;}printf("%lld\n",dp[n]);}
