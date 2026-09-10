1\. Project objective



The objective is to design a supply chain risk-management system for a company that faces multiple simultaneous risks such as:



* Supplier failure
* Transportation disruption
* Raw-material shortage
* Demand surge
* Geopolitical disruption
* Natural disaster
* Quality failure
* Lead-time variability
* Cyberattack
* Capacity reduction



The central question is:



“What supply-chain configuration gives the company the best balance between cost, risk exposure, and resilience?”



2\. Suggested industry scenario



A consumer electronics manufacturer may be assumed because it allows us to combine almost everything students have learned.



For example:



Company: SmartTech Electronics



The company manufactures smart devices using components from several suppliers.



Supply chain:



Suppliers → Factories → Distribution Centers → Customers



Critical components:



* Processor
* Display
* Battery
* Memory
* Camera module
* Casing



Some components have single suppliers, while others have multiple suppliers.



3\. Risk factors



Supply Chain Risk Register.



Risk			Probability	Impact		Risk Score

Supplier failure	8%		Very High	High

Port disruption		12%		High		High

Raw-material shortage	15%		High		High

Demand surge		20%		Medium		Medium

Quality failure		10%		High		High

Cyberattack		5%		Very High	High

Factory disruption	7%		Very High	High

Transportation delay	18%		Medium		Medium



We should not simply use probability × impact mechanically. They can develop a more sophisticated score incorporating:



Risk Score = Probability × Impact × Exposure × Vulnerability



4\. The complicated part: supply-chain risk simulation



We can build a Monte Carlo simulation with perhaps:



10,000 simulated supply-chain scenarios



For every simulation:



1. Generate supplier disruptions.
2. Generate transportation disruptions.
3. Generate demand variability.
4. Generate lead-time variability.
5. Determine available component supply.
6. Determine production capacity.
7. Determine inventory.
8. Determine customer service level.
9. Calculate shortages.
10. Calculate financial consequences.



For example:



Total Cost = Purchase + Transportation + Holding + Shortage + Emergency Procurement + Lost Sales + Recovery



This makes the project much richer than a simple risk matrix.



5\. Multi-risk scenarios



Students should evaluate at least five scenarios.



Scenario 1 — Normal operation



No major disruption.



Scenario 2 — Supplier failure



Supplier A becomes unavailable for four weeks.



Scenario 3 — Transportation disruption



Port/transportation capacity falls by 50% for three weeks.



Scenario 4 — Demand surge



Demand increases by 30%.



Scenario 5 — Compound disruption



Supplier failure + transportation disruption + demand surge occur simultaneously.



The fifth scenario is particularly interesting because risks can interact rather than simply add together.



6\. Resilience strategies



Students then test different strategies.



Strategy A — Current supply chain



Single sourcing + existing inventory.



Strategy B — Safety-stock strategy



Increase inventory of critical components.



Strategy C — Dual sourcing



Add a second supplier.



Strategy D — Multi-sourcing



Split procurement across three suppliers.



Strategy E — Regional sourcing



Use geographically diversified suppliers.



Strategy F — Supplier capacity reservation



Pay suppliers to maintain emergency capacity.



Strategy G — Combined resilience strategy



For example:



Dual sourcing + safety stock + alternate transportation + emergency supplier capacity



7\. Optimization component



This is where the project becomes genuinely advanced.



We can optimize:



* Supplier allocation
* Safety-stock levels
* Supplier diversification
* Transportation modes
* Emergency capacity
* Inventory positioning



Objective:



min ( Expected\\ Cost + lambda\* Risk) 



where lambda represents the company's willingness to pay for risk reduction.



8\. Risk-adjusted supplier selection



Students could also calculate a risk-adjusted supplier score.



For example:



Supplier	Cost	Quality	Delivery	Financial Risk	Geopolitical Risk

A		8	9	9		8		4

B		7	8	7		9		9

C		9	9	8		7		8



Then calculate:



Supplier Score=w1\*Cost + w2\*Quality + w3\*Delivery + w4\*Risk + w5\*Geopolitical Risk



But the interesting question is:



Is the cheapest supplier still the best supplier after disruption risk is incorporated?



That creates a strong managerial discussion.

