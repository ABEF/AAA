"""Independent eager TWO-adjacent-ordinal whole-unit oracle, integer rational form.

Inputs are authenticated funding/weight/claim events. It stores no production
pending tree or compact slots. Only ordinals1/2 with no other active leaves are
admitted; all earlier branches then have leftWeight==total and zero phase.
"""
Q=1<<128
class TwoLeaf:
    def __init__(self):
        self.weights=[0,0];self.phase={};self.money={}
    def _book(self,token):
        self.phase.setdefault(token,[0,0]);self.money.setdefault(token,[0,0])
    def credit(self,token,amount):
        assert amount>=0;self._book(token)
        if not amount:return
        total=sum(self.weights);assert total>0
        whole,remainder=divmod(amount*self.weights[0],total)
        high,low=self.phase[token]
        extra,rest=divmod(remainder*Q+high*total+low,total*Q)
        left=whole+extra;assert 0<=left<=amount
        self.phase[token]=list(divmod(rest,total))
        self.money[token][0]+=left;self.money[token][1]+=amount-left
    def weight(self,ordinal,value):
        assert ordinal in (1,2) and value>=0
        old=sum(self.weights)
        if self.weights[ordinal-1]==value:return
        self.weights[ordinal-1]=value;new=sum(self.weights)
        for token,(high,low)in self.phase.items():self.phase[token]=[high,low*new//old if old and new else 0]
    def take(self,token,ordinal):
        self._book(token);value=self.money[token][ordinal-1];self.money[token][ordinal-1]=0;return value
    def claim(self,token,ordinal):self._book(token);return self.money[token][ordinal-1]
