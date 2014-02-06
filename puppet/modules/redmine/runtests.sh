#!/bin/bash

[[ -s "$HOME/.rvm/scripts/rvm" ]] && source "$HOME/.rvm/scripts/rvm"

rvm use $ruby@$$ --create
gem install bundler
bundle install 
bundle exec rspec spec
RESULT=$?
rvm --force gemset delete $$
exit $RESULT
