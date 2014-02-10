#!/bin/bash

[[ -s "$HOME/.rvm/scripts/rvm" ]] && source "$HOME/.rvm/scripts/rvm"

rvm use $ruby@$$ --create
gem install --no-rdoc --no-ri puppet-lint
gem install --no-rdoc --no-ri rspec-puppet
gem install --no-rdoc --no-ri rake
gem install --no-rdoc --no-ri puppet
rake rspec
RESULT=$?
rvm --force gemset delete $$
exit $RESULT
