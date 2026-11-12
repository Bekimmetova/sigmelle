#include <bits/stdc++.h>
using namespace std;
int main(){string s;cin>>s;int n=s.size(),c=0;for(int i=0;i<n/2;i++)if(s[i]!=s[n-1-i])c++;cout<<c<<"\n";}
