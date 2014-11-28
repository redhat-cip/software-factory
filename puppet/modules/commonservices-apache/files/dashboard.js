var sfDashboard = angular.module('sfDashboard', []);

function mainController($scope, $http) {
    $scope.data = {};

    function get_projects() {
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
    }

    get_projects();

    function get_open_reviews() {
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
    }

    get_open_reviews();

    function get_open_bugs() {
        $http.get('/redmine//issues.json?status_id=open')
            .success(function(data) {
        var bugs = {};
                for (key in data['issues']) {
                     p = data['issues'][key]["project"]["name"];
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
    }

    get_open_bugs();

    $scope.createProject = function() {
        $scope.errors = false;
        $scope.loading = true;
        $http.put('/manage/project/' + $scope.data.name , $scope.data)
            .success(function(data) {
                $scope.data = {};
                get_projects();
            })
            .error(function(data) {
            $scope.errors = data;
            }).finally(function () {
                $scope.loading = false;
            });
    };

    $scope.deleteProject = function(name) {
        $scope.errors = false;
        $scope.loading = true;
        $http.delete('/manage/project/' + name)
            .success(function(data) {
                $scope.data = {};
                get_projects();
            })
            .error(function(data) {
            $scope.errors = data;
            }).finally(function () {
                $scope.loading = false;
            });
    };
}
