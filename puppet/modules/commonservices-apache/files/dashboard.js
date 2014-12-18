var sfDashboard = angular.module('sfDashboard', []);

function mainController($scope, $http) {
    $scope.data = {};
    $scope.members= [];

    function initProjects() {
        $scope.errors = false;
        $scope.loading = true;

        $http.get('/manage/project/')
            .success(function(data) {
                $scope.projects = data;
            })
            .error(function(data) {
                $scope.errors = data;
            }).finally(function () {
                $scope.loading = false;
            });
    };

    function initReviews() {
        $http.get('/r/changes/?q=status:open')
            .success(function(data) {
                var reviews = {};
                for (key in data) {
                    var p = data[key].project;
                    if (reviews[p] == null) {
                        reviews[p] = 0;
                    }
                    reviews[p]++;
                }
                $scope.open_reviews = reviews;
            })
            .error(function(data) {
                $scope.errors = data;
            });
    };

    function initBugs() {
        $http.get('/redmine//issues.json?status_id=open')
            .success(function(data) {
                var bugs = {};
                for (var key in data['issues']) {
                    var p = data['issues'][key]["project"]["name"];
                    if (bugs[p] == null) {
                        bugs[p] = {};
                        bugs[p]['id'] = data['issues'][key]["project"]["id"];
                        bugs[p]['count'] = 0;
                    }
                    bugs[p]['count']++;
                }
                $scope.open_bugs = bugs;
            })
            .error(function(data) {
                $scope.errors = data;
            });
    };

    function initMembers() {
        $http.get('/manage/project/membership/')
            .success( function (data) {
                $scope.members = data;
            })
            .error( function (data) {
                $scope.errors = data;
            });
    };

    function init() {
        initProjects();
        initReviews();
        initBugs();
        initMembers();
    };

    $scope.createProject = function() {
        $scope.errors = false;
        $scope.loading = true;

        $http.put('/manage/project/' + $scope.data.name , $scope.data)
            .success(function(data) {
                $scope.data = {};
                initProjects();
            })
            .error(function(data) {
            $scope.errors = data;
            }).finally(function () {
                $scope.loading = false;
            });
    };

    $scope.deleteProject = function(name) {
        if (window.confirm('Delete project ' + name + '?') ) {
            $scope.errors = false;
            $scope.loading = true;
            $http.delete('/manage/project/' + name)
                .success(function(data) {
                    $scope.data = {};
                    initProjects();
                })
                .error(function(data) {
                    $scope.errors = data;
                }).finally(function () {
                    $scope.loading = false;
                });
        }
    };

    $scope.membershipForm = function(projectName, projectObj) {
        $scope.selectedProjectName = projectName;
        $scope.selectedProject = projectObj;
        $scope.originalMembers = [];
        $scope.selectedMembers = [];
        var i = 0;
        var numMembers = $scope.members.length;

        var memberGroups = function ( member_id ) {
            var groups = projectObj["groups"];
            var memberGroups = {};
            var key;

            for ( key in groups ) {
                if ( groups.hasOwnProperty(key) ) {
                    memberGroups[key] = false;
                    for ( var k = 0; k < groups[key]["members"].length; k ++ ) {
                        if ( groups[key]["members"][k]['username'].match( member_id ) )
                            memberGroups[key] = true;
                    }
                }
            }
            return memberGroups;
        };

        for ( i = 0; i < numMembers; i++ ) {
            var member = $scope.members[i];
            $scope.originalMembers.push({name: member[2],
                                         email: member[1],
                                         groups: memberGroups(member[0])});
        }

        $scope.selectedMembers = JSON.parse(JSON.stringify($scope.originalMembers));
    };


    $scope.updateMembers = function() {
        if ( $scope.members.length < 1 ) {
            $scope.errors = "selected members list is empty";
            return;
        }
        var compareGroups = function (A, B) {
            var key;
            groups = {};
            for ( key in A ) {
                if (A[key] !== B[key]) {
                    groups[key] = B[key];
                }
            }
            return groups;
        };

        var x, key, groupName;
        for ( x = 0; x < $scope.originalMembers.length; x++ ) {
            var groups = compareGroups($scope.originalMembers[x].groups,
                                       $scope.selectedMembers[x].groups);
            var selectedMember = $scope.selectedMembers[x];
            var url = '/manage/project/membership/' +
                    $scope.selectedProjectName + '/' +
                    selectedMember.email + '/';

            for ( key in groups ) {
                groupName = key + '-group';
                if ( groups[key] ) {
                    $http.put(url, {"groups": [groupName]})
                        .success( function (data) {
                            initProjects();
                            initMembers();
                        })
                        .error( function (data) {
                            $scope.errors = data;
                        });
                }
                else {
                    $http.delete(url + groupName + '/')
                        .success( function (data) {
                            initProjects();
                            initMembers();
                        })
                        .error( function (data) {
                            $scope.errors = data;
                        });
                }
            }
        }
    };

    init();
}
