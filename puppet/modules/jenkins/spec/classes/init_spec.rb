require 'spec_helper'

describe "jenkins" do
    let(:title) { 'jenkins' }

    context 'jenkins' do
        it {
            should contain_file('/var/lib/jenkins/config.xml').with({
                'ensure' => 'file',
                'owner'  => 'jenkins',
                'group'  => 'nogroup',
                'mode'   => '0644',
            })
            should contain_file('/etc/jenkins_jobs/jenkins_jobs.ini').with({
                'ensure' => 'file',
                'mode'   => '0400',
            })
        }
    end
end
