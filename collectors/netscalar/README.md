### Inframer netscalar collector

* Tested on Netscalar 10.0

* Netscalar API list's the lbvservers and then we have to query the lbvserver\_binding API to get information on the binding. This collector
  gets the lbvserver, queries its binding and dumps out a consolidated json.
