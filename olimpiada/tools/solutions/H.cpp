#include <bits/stdc++.h>
using namespace std;
int main(){int n,m;scanf("%d %d",&n,&m);vector<vector<pair<int,long long>>>adj(n+1);for(int i=0;i<m;i++){int u,v;long long w;scanf("%d %d %lld",&u,&v,&w);adj[u].push_back({v,w});adj[v].push_back({u,w});}
const long long INF=LLONG_MAX;vector<long long>d(n+1,INF);d[1]=0;priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<>>pq;pq.push({0,1});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du>d[u])continue;for(auto [v,w]:adj[u])if(du+w<d[v]){d[v]=du+w;pq.push({d[v],v});}}
printf("%lld\n",d[n]==INF?-1:d[n]);}
