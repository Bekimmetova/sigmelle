#include <bits/stdc++.h>
using namespace std;
int main(){int n,m;scanf("%d %d",&n,&m);vector<string>g(n);char buf[1005];int sx=0,sy=0,fx=0,fy=0;
for(int i=0;i<n;i++){scanf("%s",buf);g[i]=buf;for(int j=0;j<m;j++){if(g[i][j]=='S'){sx=i;sy=j;}if(g[i][j]=='F'){fx=i;fy=j;}}}
vector<vector<int>>d(n,vector<int>(m,-1));queue<pair<int,int>>q;q.push({sx,sy});d[sx][sy]=0;int dx[]={1,-1,0,0},dy[]={0,0,1,-1};
while(!q.empty()){auto [x,y]=q.front();q.pop();for(int k=0;k<4;k++){int a=x+dx[k],b=y+dy[k];if(a>=0&&a<n&&b>=0&&b<m&&g[a][b]!='#'&&d[a][b]<0){d[a][b]=d[x][y]+1;q.push({a,b});}}}
printf("%d\n",d[fx][fy]);}
