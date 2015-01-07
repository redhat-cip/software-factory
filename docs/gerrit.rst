.. toctree::

Customized Gerrit package
=========================

The used Gerrit version has been modified to run within an iframe. Gerrit does
not escape an iframe any more.

The following patch has been applied to Gerrit:

.. code-block:: none

 diff --git a/gerrit-gwtexpui/src/main/java/com/google/gwtexpui/user/client/UserAgent.java b/gerrit-gwtexpui/src/main/java/com/google/gwtexpui/user/client/UserAgent.java
 index c654902..3ec52d7 100644
 --- a/gerrit-gwtexpui/src/main/java/com/google/gwtexpui/user/client/UserAgent.java
 +++ b/gerrit-gwtexpui/src/main/java/com/google/gwtexpui/user/client/UserAgent.java
 @@ -79,8 +79,8 @@ public class UserAgent {
     */
    public static void assertNotInIFrame() {
      if (GWT.isScript() && amInsideIFrame()) {
 -      bustOutOfIFrame(Window.Location.getHref());
 -      throw new RuntimeException();
 +      //bustOutOfIFrame(Window.Location.getHref());
 +      //throw new RuntimeException();
      }
    }

Note: a better option for a production deployment would be check if the location
matches the used SF domain. This is in the works.

Afterwards Gerrit has to be rebuilt from sources. You need a JDK and Maven for
this:

.. code-block:: bash

 $ sudo apt-get install maven openjdk-7-jdk zip
 $
 $ git clone https://gerrit.googlesource.com/buck
 $ git clone https://gerrit.googlesource.com/gerrit
 $ cd ~/gerrit/
 $ git checkout v2.8.6.1
 $ git submodule init
 $ git submodule update
 $ cd ~/buck/
 $ git checkout $(cat ../gerrit/.buckversion)
 $ ant
 $ mkdir ~/bin
 $ PATH=~/bin:$PATH
 $ ln -s `pwd`/bin/buck ~/bin/
 $ ln -s `pwd`/bin/buckd ~/bin/
 $ which buck
 $ cd ~/gerrit/
 $ patch -p0 < ~/gerrit.patch
 $ buck build gerrit

If the build was successful the gerrit.war file has been placed in `~/gerrit/buck-out/gen/gerrit.war`.
