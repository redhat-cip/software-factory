// Remove all offline node
for (aSlave in hudson.model.Hudson.instance.slaves) {
  if (aSlave.getComputer().isOffline()) {
   println("Removing node: " + aSlave.name);
   aSlave.getComputer().doDoDelete();
  }
}
