var sfDashboard = angular.module('sfDashboard', []);

sfDashboard.filter('projectMembers', function() {
    return function (members, searchMember) {
        var items;
        var filtered = [];
        var groups;
        var name;
        // Get all active project members
        if ( typeof members !== 'undefined' ) {
            items = members.slice();
            for ( var i = 0; i < items.length; i++ ) {
                groups = items[i].groups;
                if (groups.ptl || groups.core || groups.dev) {
                    filtered.push(items[i]);
                    items.splice(i--, 1);
                }
            }

            // Add to the end any users that match the list.
            if ( (typeof searchMember !== 'undefined') && (searchMember.length >= 1) ) {
                for (var j = 0; j < items.length; j++ ) {
                    name = items[j].name.toLocaleLowerCase();
                    if (name.search(searchMember.toLocaleLowerCase()) !==-1 ){
                        filtered.push(items[j]);
                    }
                }
            }
        }
        return filtered;
    };
});

function mainController($scope, $http) {
    $scope.data = {};
    $scope.members= [];
    $scope.testRunning = Object();
    $scope.testLabels = [];

    function initConfig() {
        $http.get('/manage/config/')
            .success(function(data) {
                $scope.create_project_permission = (data.create_projects != undefined &&
                                                    data.create_projects == true);
            }).
            error(function(data) {
                $scope.create_project_permission = false;
            });
    };

    function initProjects() {
        $scope.errors = false;
        $scope.loading = true;

        $http.get('/manage/project/')
            .success(function(data) {
                for(project in data) {
                    data[project]['alt_name'] = project.replace("/", "_");
                }
                $scope.projects = data;
            })
            .error(function(data) {
                $scope.errors = data;
            }).finally(function () {
                $scope.loading = false;
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

    function initTests() {
        $http.get('/zuul/status.json')
            .success( function (data) {
                var projectName;
                var tests;
                var pipelines = data.pipelines;

                for ( var i = 0; i < pipelines.length; i++ ) {
                    // Create the list of test labels
                    $scope.testLabels.push(pipelines[i].name);
                    tests = pipelines[i].change_queues;

                    for ( var j = 0; j < tests.length; j++  ) {
                        // Create an entry only if there's a test running
                        for ( var k = 0; k < tests[j].heads.length; k++ ) {

                            for ( var l = 0; l < tests[j].heads[k].length; l++ ) {
                                projectName = tests[j].heads[k][l].project;

                                // Initialize test values of the project.
                                if ( !(projectName in $scope.testRunning) ) {
                                    $scope.testRunning[projectName] = [];
                                    var z = pipelines.length;
                                    while (z) $scope.testRunning[projectName][--z] = 0;
                                }

                                $scope.testRunning[projectName][i]++;
                            }
                        }
                    }
                }
            })
            .error( function (data) {
                $scope.errors = data;
            });
    };

    function init() {
        initConfig();
        initProjects();
        initMembers();
        initTests();
    };

    $scope.createProject = function() {
        $scope.errors = false;
        $scope.loading = true;
        var name = '===' + btoa($scope.data.name);

        $http.put('/manage/project/' + name + '/', $scope.data)
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
            name = '===' + btoa(name);

            $http.delete('/manage/project/' + name + '/')
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
            var projectName = '===' + btoa($scope.selectedProjectName);
            var url = '/manage/project/membership/' + projectName + '/' +
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
