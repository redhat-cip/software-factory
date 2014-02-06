require 'spec_helper'

describe "redmine" do
    let(:title) { 'redmine' }
    context 'redmine' do
        it {
            should contain_package('redmine').with( { 'name' => 'redmine' } )
            should contain_package('apache2').with( { 'name' => 'apache2' } )
            should contain_package('libapache2-mod-passenger')
            should contain_service('apache2').with( { 'name' => 'apache2' } )
            should contain_file('/etc/redmine/default/database.yml').with({
                'ensure' => 'file',
                'owner'  => 'www-data',
                'group'  => 'www-data',
                'mode'   => '0640',
            })
            should contain_file('/etc/apache2/mods-available/passenger.conf').with({
                'ensure' => 'file',
                'owner'  => 'www-data',
                'group'  => 'www-data',
                'mode'   => '0640',
            })
            should contain_file('/etc/apache2/sites-available/redmine').with({
                'ensure' => 'file',
                'owner'  => 'www-data',
                'group'  => 'www-data',
                'mode'   => '0640',
            })
             should contain_file('/etc/apache2/sites-enabled/000-default').with({
                'ensure' => 'absent',
            })
        }
    end
end
